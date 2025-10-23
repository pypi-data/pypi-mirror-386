from typing import Any, List, Union

from compute_api_client import BackendType
from qi2_shared.hybrid.quantum_interface import QuantumInterface
from qiskit import QuantumCircuit

from qiskit_quantuminspire.hybrid.hybrid_job import QIHybridJob
from qiskit_quantuminspire.qi_backend import QIBaseBackend


class QIHybridBackend(QIBaseBackend):
    """Used as a Qiskit backend for hybrid algorithms that are fully executed on the Quantum Inspire platform.

    Quantum hardware specifications are inferred from the backend type selected on submission.
    """

    def __init__(self, qi: QuantumInterface, **kwargs: Any):
        super().__init__(BackendType.model_validate(qi.backend_type), **kwargs)
        self._quantum_interface = qi

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIHybridJob:
        self.set_options(**options)
        job = QIHybridJob(run_input=run_input, backend=self, quantum_interface=self._quantum_interface)
        job.submit()
        return job
