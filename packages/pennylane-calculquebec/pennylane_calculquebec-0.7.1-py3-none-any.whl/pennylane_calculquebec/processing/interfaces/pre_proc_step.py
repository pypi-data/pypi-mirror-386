"""
Contains a base class that can be used for creating new pre-processing steps
"""

from pennylane.tape import QuantumTape
from pennylane_calculquebec.processing.interfaces.base_step import BaseStep


class PreProcStep(BaseStep):
    """a base class that represents pre-processing steps that apply on quantum circuit operations"""

    def execute(self, tape: QuantumTape):
        """
        applies processing on a quantum circuit's results after the execution

        Args:
            tape (QuantumTape) : the tape representation of the quantum circuit

        Returns:
            QuantumTape : the processed tape
        """

        return tape
