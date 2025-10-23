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

"""Twirl"""

from qiskit.circuit import Annotation

from .decomposition_mode import DecompositionLiteral, DecompositionMode
from .dressing_mode import DressingLiteral, DressingMode
from .virtual_type import TWIRLING_GROUPS, GroupLiteral, VirtualType


class Twirl(Annotation):
    """Directive to twirl the contents of a ``box`` instruction.

    Args:
        group: Which group to twirl with.
        dressing: Which side of the box to attached dressing instructions.
        decomposition: How to decompose single-qubit gates.
    """

    namespace = "samplomatic.twirl"

    __slots__ = ("group", "dressing", "decomposition")

    def __init__(
        self,
        group: GroupLiteral = VirtualType.PAULI,
        dressing: DressingLiteral = DressingMode.LEFT,
        decomposition: DecompositionLiteral = DecompositionMode.RZSX,
    ):
        self.group = VirtualType(group)
        self.dressing = DressingMode(dressing)
        self.decomposition = DecompositionMode(decomposition)

        if self.group not in TWIRLING_GROUPS:
            allowed = (f"'{group}'" for group in TWIRLING_GROUPS)
            raise ValueError(f"The group must be one of [{', '.join(allowed)}].")

    def __eq__(self, other):
        return (
            isinstance(other, Twirl)
            and self.group == other.group
            and self.dressing == other.dressing
            and self.decomposition == other.decomposition
        )

    def __hash__(self):
        return hash((self.group, self.dressing, self.decomposition))

    def __repr__(self):
        return (
            f"{type(self).__name__}(group='{self.group.name.lower()}', dressing="
            f"'{self.dressing.name.lower()}', decomposition='{self.decomposition.name.lower()}')"
        )
