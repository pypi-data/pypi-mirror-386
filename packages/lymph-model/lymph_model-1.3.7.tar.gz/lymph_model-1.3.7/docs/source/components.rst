.. module: components

.. _components:


Components
===========

Below we document the core components implementing the Bayesian network and hidden
Markov model we use to compute probabilistic predictions of lymphatic tumor spread.

Diagnostic Modalities
---------------------

.. automodule:: lymph.modalities
    :members:
    :special-members: __init__, __hash__
    :show-inheritance:


Marginalization over Diagnosis Times
-----------------------------------

.. automodule:: lymph.diagnosis_times
    :members:
    :special-members: __init__, __hash__
    :show-inheritance:

Matrices
--------

.. automodule:: lymph.matrix
    :members:
    :special-members: __init__
    :show-inheritance:
