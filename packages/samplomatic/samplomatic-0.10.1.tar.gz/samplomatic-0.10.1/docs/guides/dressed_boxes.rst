Dressed boxes
=============

Physical noise mechanisms that occur during the execution of quantum circuits are contextual.
When applying operations on disjoint qubits simultaneously, the noise profile of the overall operation may not be equal to that of the constituent parts, if those parts were to be applied in isolation.
Similarly, for operations that ideally commute on the same qubits, the noise profile associated with the individual operations may not commute and could be different altogether if the order of the operations changed.
Therefore, protocols for suppressing, mitigating, and correcting noise need to know the context in which it arises.

Samplomatic uses box instructions to reason about collections of circuit operations that should be treated as having a stable noise context, and uses annotations on boxes to allow users to declare and configure intent.
Every box is a scope that owns a set of qubits, operations that act on those qubits, and a list of annotations.
Samplomatic annotations specify *directives* and *dressings*.
Directives specify what to do with the box, e.g. twirl the box.
Dressings are groups of parameterized gates to add to the left- or right-side of the box, e.g. a layer of single qubit gates.
The gates in a dressing incorporate gates from the box, as well as operations required to enact directives:

* Gates in the box that are compatible with and on the same side as the parameterized gates.
* Twirling gates sampled from a set to randomize the box.
* Noise injection gates sampled from a Pauli Lindblad map.
* User-specified basis changing gates.

Note that directives can alter dressings of other boxes.

A guiding example
-----------------

Suppose we would like to twirl the following circuit, adding random Pauli gates before and after the parallel entangling gates that don't change the logical content of the circuit, but that do change the effective noise model.

.. figure:: ../figs/undressed_pauli.drawio.png

    Circuit to Pauli twirl.


This is achieved by stratifying the circuit into boxes and adding twirl annotations.

.. figure:: ../figs/dressed_pauli_twirl.drawio.png

    Circuit with Pauli twirling directives.
    The ``@`` symbol is used to specify directives, dressing by default on the left.


Each dressed box contains a layer of single-qubit gates and a layer of two-qubit entangling gates on disjoint pairs of qubits.
The layer of entangling gates is surrounded by layers of random Pauli gates in such a way that the logical action of the box is unchanged.
These random Pauli layers are *virtual* in the same spirit as a virtual Z gate–they do not add additional operations to the circuit, but instead act as a directive to alter how adjacent single-qubit gates are implemented.

.. figure:: ../figs/pauli_twirl.drawio.png

    Circuit with dressings and gates from directives.
    Dressings are the dashed boxes.
    Pauli layers attached by arrows cancel each other out.
    The final Pauli layer will be applied as bit flips to the measurement outcomes.


The random Pauli layer between the entangling gates and single-qubit gates is composed into the layer of single-qubit gates and implemented together in its dressing.
The other random Pauli layer will be composed into the dressing of the next dressed box.

To summarize, the left (right) twirl directive is to implement a random Pauli in this box's dressing and apply the Pauli that undoes it in the next (previous) box's dressing.
The inject noise and basis change directives are analogous.

Circuit randomization with virtual gates
----------------------------------------

Samplomatic uses the framework of *virtual gates* to reason about circuits with dressed boxes.
Conceptually, and as implemented in a :class:`~.Samplex` instance produced by the :func:`~build` process, virtual gates are generated at the boundary of the box opposite its dressing.
These virtual gates are moved through the circuit in a prescribed way and need to be composed into a dressing.
If all virtual gates can be composed into a dressing, randomizations of the circuit can be built procedurally.

.. figure:: ../figs/dressed_box.drawio.png

    Circuit with twirl, basis change, and inject noise directives.


Gates on the side of the dressing compatible with its template parametrization can be composed into it, reducing the number of physical gates.
These are called *easy* gates.
The remainder of the box is called *hard* and is implemented as is.

.. figure:: ../figs/dressed_box_uncollected.drawio.png

    Examples of circuits with hanging virtual gates.
    The virtual gates on the opposite side of the dressing have nowhere to be implemented.


.. figure:: ../figs/dressed_box_collected.drawio.png

    Examples of circuits where all virtual gates are composed into dressings.
    Measurements have Pauli gates composed in by accounting for the bitflip they induce.


.. figure:: ../figs/dressed_box_mixed_collect.drawio.png

    Complex example where all virtual gates are collected.
    Virtual gates generated by one box can be composed into different dressings.

This allows for constructions where dressed boxes do not need to have the same width.
