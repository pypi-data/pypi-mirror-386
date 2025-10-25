"""
Contains placement pre-processing steps
"""

from pennylane.tape import QuantumTape
import pennylane_calculquebec.utility.graph as graph_util
from pennylane_calculquebec.processing.interfaces import PreProcStep
from pennylane_calculquebec.logger import logger


class Placement(PreProcStep):
    """
    base class for any placement algorithm.
    """

    def __init__(
        self,
        machine_name: str,
        use_benchmark=True,
        q1_acceptance=0.5,
        q2_acceptance=0.5,
        excluded_qubits=[],
        excluded_couplers=[],
    ):
        """constructor for placement algorithms

        Args:
            use_benchmark (bool, optional): should we use benchmarks during placement? Defaults to True.
            q1_acceptance (float, optional): what is the level of acceptance for state 1 readout? Defaults to 0.5.
            q2_acceptance (float, optional): what is the level of acceptance for cz fidelity? Defaults to 0.5.
            excluded_qubits (list, optional): what qubits should we exclude from the mapping? Defaults to [].
            excluded_couplers (list, optional): what couplers should we exclude from the mapping? Defaults to [].
        """
        self.use_benchmark = use_benchmark
        self.machine_name = machine_name
        self.q1_acceptance = q1_acceptance
        self.q2_acceptance = q2_acceptance
        self.excluded_qubits = excluded_qubits
        self.excluded_couplers = excluded_couplers


class ISMAGS(Placement):
    """
    finds a mapping between the circuit's wires and the machine's qubits using the ISMAGS subgraph isomorphism algorithm\n
    ISMAGS is similar to VF2 except it also considers symmetries which can make it faster in some cases\n
    Plus, the networkx implementation has capabilities for searching for largest common subgraphs
    """

    def execute(self, tape):
        """places the circuit on the machine's connectivity using ISMAGS subgraph isomorphism algorithm\n
        If there is no perfect match, the missing nodes are mapped with qubits that minimize the subsequent routing path\n
        1. find largest common subgraph\n
        2. for each unmapped node\n
            3. find the best neighbour (using cost function)\n
            4. find machine node with shortest path from already mapped machine node\n
        5. map wires in all operations and measurements\n

        Args:
            tape (QuantumTape): The tape to act on

        Raises:
            Exception: There should be enough space on the machine to run the circuit

        Returns:
            QuantumTape: The transformed quantum tape
        """
        circuit_topology = graph_util.circuit_graph(tape)
        machine_topology = graph_util.machine_graph(
            self.machine_name,
            self.use_benchmark,
            self.q1_acceptance,
            self.q2_acceptance,
            self.excluded_qubits,
            self.excluded_couplers,
        )

        if len(graph_util.find_biggest_group(circuit_topology)) > len(
            graph_util.find_biggest_group(machine_topology)
        ):
            raise Exception(
                f"There are {machine_topology.number_of_nodes} qubits on the machine but your circuit has {circuit_topology.number_of_nodes}."
            )

        # 1. find largest common subgraph
        mapping = graph_util.find_largest_common_subgraph_ismags(
            circuit_topology, machine_topology
        )

        # 2. find all unmapped nodes
        missing = [
            node for node in circuit_topology.nodes if node not in mapping.keys()
        ]

        for source in missing:
            if source in mapping:
                continue

            if circuit_topology.degree(source) <= 0:
                mapping[source] = graph_util.find_best_wire(
                    machine_topology,
                    self.machine_name,
                    list(mapping.values()),
                    self.use_benchmark,
                )
                continue

            mapping[source] = graph_util.find_best_wire(
                machine_topology,
                self.machine_name,
                [machine_node for machine_node in mapping.values()],
                self.use_benchmark,
            )

            for destination in missing:
                if (source, destination) not in circuit_topology.edges:
                    continue

                ASTAR(self.machine_name, False)._recurse(
                    source,
                    destination,
                    mapping,
                    missing,
                    machine_topology,
                    circuit_topology,
                )

        # 5. map wires in all operations and measurements
        new_tape = type(tape)(
            [operation.map_wires(mapping) for operation in tape.operations],
            [measurement.map_wires(mapping) for measurement in tape.measurements],
            shots=tape.shots,
        )

        return new_tape


class VF2(Placement):
    """
    finds a mapping between the circuit's wires and the machine's qubits using the VF2 subgraph isomorphism algorithm\n
    the networkx implementation of VF2 doesn't allow for largest common subgraph research, so we're using a combinatorics approach and testing all possibilities from largest to smallest\n
    this "brute force" approach makes the algorithm quite slower than other solutions in the plugin
    """

    def execute(self, tape):
        """places the circuit on the machine's connectivity using VF2 algorithm\n
        If there is no perfect match, the missing nodes are mapped with qubits that minimize the subsequent routing path\n
        1. find largest common subgraph\n
        2. for each unmapped node\n
            3. find the best neighbour (using cost function)\n
            4. find machine node with shortest path from already mapped machine node\n
        5. map wires in all operations and measurements\n

        Args:
            tape (QuantumTape): the tape to act on

        Raises:
            Exception: There should be enough space on the machine to run the circuit

        Returns:
            QuantumTape: The transformed quantum tape
        """
        circuit_topology = graph_util.circuit_graph(tape)
        machine_topology = graph_util.machine_graph(
            self.machine_name,
            self.use_benchmark,
            self.q1_acceptance,
            self.q2_acceptance,
            self.excluded_qubits,
            self.excluded_couplers,
        )

        if len(graph_util.find_biggest_group(circuit_topology)) > len(
            graph_util.find_biggest_group(machine_topology)
        ):
            raise Exception(
                f"There are {machine_topology.number_of_nodes()} qubits on the machine but your circuit has {circuit_topology.number_of_nodes()}."
            )

        # 1. find the largest common subgraph using VF2 algorithm and combinatorics
        mapping = graph_util.find_largest_common_subgraph_vf2(
            circuit_topology, machine_topology
        )

        # 2. find all unmapped nodes
        missing = [
            node for node in circuit_topology.nodes if node not in mapping.keys()
        ]

        for node in missing:
            # 3. check if missing node has any neighbours
            if circuit_topology.degree(node) <= 0:
                # 3.a if not, just assign node to arbitrary qubit
                mapping[node] = graph_util.find_best_wire(
                    machine_topology,
                    self.machine_name,
                    list(mapping.values()),
                    self.use_benchmark,
                )
                continue

            # 4. find the best neighbour (using cost function)
            most_connected_node = graph_util.find_best_neighbour(
                node, circuit_topology, self.machine_name, self.use_benchmark
            )

            # 5. find machine node with shortest path from already mapped machine node
            possibles = [
                possible
                for possible in machine_topology.nodes
                if possible not in mapping.values()
            ]
            shortest_path_mapping = graph_util.node_with_shortest_path_from_selection(
                mapping[most_connected_node],
                possibles,
                machine_topology,
                machine_name=self.machine_name,
                use_benchmark=self.use_benchmark,
            )

            mapping[node] = shortest_path_mapping

        # 5. map wires in all operations and measurements
        new_tape = type(tape)(
            [operation.map_wires(mapping) for operation in tape.operations],
            [measurement.map_wires(mapping) for measurement in tape.measurements],
            shots=tape.shots,
        )

        return new_tape


class ASTAR(Placement):
    """
    finds a mapping between the circuit's wires and the machine's qubits using an ASTAR based traversal heuristic
    """

    def _recurse(
        self,
        source,
        destination,
        mapping,
        to_explore,
        machine_topology,
        circuit_topology,
    ):
        """traverses the circuit graph, finding mappings for nodes recursively

        Args:
            source (int): the node of origin
            destination (int): the destination node
            mapping (dict[int, int]): which wires are already mapped to a qubit
            to_explore (list[int]): which wires remain to be mapped
            machine_topology (Graph): the graph representation of the machine
            circuit_topology (Graph): the graph representation of the circuit
        """
        try:
            if destination in mapping:
                return

            mapping[destination] = graph_util.find_closest_wire(
                mapping[source],
                machine_topology,
                self.machine_name,
                excluding=[machine_node for machine_node in mapping.values()],
                use_benchmark=self.use_benchmark,
            )

            source2 = destination
            for destination2 in to_explore:
                if (source2, destination2) not in circuit_topology.edges:
                    continue

                self._recurse(
                    source2,
                    destination2,
                    mapping,
                    to_explore,
                    machine_topology,
                    circuit_topology,
                )
        except Exception as e:
            logger.error(
                "Error %s in _recurse located in ASTAR: %s", type(e).__name__, e
            )

    def execute(self, tape: QuantumTape) -> QuantumTape:
        """places the circuit on the machine's connectivity using astar algorithm and comparing path lengths

        Args:
            tape (QuantumTape): The quantum tape to act on

        Raises:
            Exception: There should be enough space on the machine to run the circuit

        Returns:
            QuantumTape: The transformed quantum tape
        """
        circuit_topology = graph_util.circuit_graph(tape)
        machine_topology = graph_util.machine_graph(
            self.machine_name,
            self.use_benchmark,
            self.q1_acceptance,
            self.q2_acceptance,
            self.excluded_qubits,
            self.excluded_couplers,
        )

        if len(graph_util.find_biggest_group(circuit_topology)) > len(
            graph_util.find_biggest_group(machine_topology)
        ):
            raise Exception(
                f"There are {machine_topology.number_of_nodes} qubits on the machine but your circuit has {circuit_topology.number_of_nodes}."
            )

        mapping = {}
        # sort nodes by degree descending, so that we map the most connected node first
        to_explore = list(
            reversed(
                sorted(
                    [wires for wires in tape.wires],
                    key=lambda node: circuit_topology.degree(node),
                )
            )
        )

        for source in to_explore:
            if source in mapping:
                continue
            mapping[source] = graph_util.find_best_wire(
                machine_topology,
                self.machine_name,
                [machine_node for machine_node in mapping.values()],
                self.use_benchmark,
            )

            for destination in to_explore:
                if (source, destination) not in circuit_topology.edges:
                    continue

                self._recurse(
                    source,
                    destination,
                    mapping,
                    to_explore,
                    machine_topology,
                    circuit_topology,
                )

        new_tape = type(tape)(
            [operation.map_wires(mapping) for operation in tape.operations],
            [measurement.map_wires(mapping) for measurement in tape.measurements],
            shots=tape.shots,
        )
        return new_tape
