# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""ChangeBasis"""

from __future__ import annotations

from qiskit.circuit import Annotation

from ..aliases import StrRef
from .change_basis_mode import ChangeBasisLiteral, ChangeBasisMode
from .decomposition_mode import DecompositionLiteral, DecompositionMode


class ChangeBasis(Annotation):
    """Directive to add basis changing gates.

    The resulting :class:`~.Samplex` built from a circuit with a box with this annotation has
    a tensor input with name ``ref`` and shape ``'(len(box_instruction.qubits),)'``. The tensor is
    indexed in physical qubit order, in other words, the order of the qubits in the outer-most
    circuit, restricted to those used by the box.

    Args:
        decomposition: How to decompose basis changing gates.
        mode: Whether to add gates to prepare or measure in a given basis.
        ref: A unique identifier of this basis change. If ``None``, it is set to ``mode.value``.
    """

    namespace = "samplomatic.change_basis"

    __slots__ = ("decomposition", "mode", "ref")

    def __init__(
        self,
        decomposition: DecompositionLiteral = DecompositionMode.RZSX,
        mode: ChangeBasisLiteral = ChangeBasisMode.MEASURE,
        ref: StrRef | None = None,
    ):
        self.decomposition = DecompositionMode(decomposition)
        self.mode = ChangeBasisMode(mode)
        self.ref = ref or self.mode.value

    def __eq__(self, other):
        return (
            isinstance(other, ChangeBasis)
            and self.decomposition == other.decomposition
            and self.mode == other.mode
            and self.ref == other.ref
        )

    def __hash__(self):
        return hash((self.decomposition, self.mode, self.ref))

    def __repr__(self):
        return (
            f"{type(self).__name__}(decomposition='{self.decomposition.name.lower()}', "
            f"mode='{self.mode.name.lower()}', ref='{self.ref}')"
        )
