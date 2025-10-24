Python SHiP-framework
=====================

Welcome to the official Python bindings for the SHiP (Similarity-Hierarchical-Partitioning) clustering framework.

The SHiP framework offers a modular and extensible approach to hierarchical clustering based on similarity trees, ultrametric hierarchies, and flexible partitioning strategies.

This Python package exposes several submodules:

Modules Overview
----------------

| **SHiP Module**
| The central interface to the SHiP framework. It allows you to construct similarity trees from your data, build hierarchical clusterings, and extract flat partitions with customizable parameters and algorithms.

| **Ultrametric Tree Submodule**
| Contains an overview (Enum class) of all available similarity trees used to represent relationships between data points. These trees form the basis for hierarchy construction. Different tree types, such as `DCTree` and others, can be selected from here when constructing an SHiP object.

| **Partitioning Submodule**
| Provides an overview (Enum class) of all available tree partitioning methods. These partitioning methods operate on the hierarchical trees to produce a flat clustering. Examples include methods like the Elbow method and fixed-K partitioning. They can be used in the fit or fit_predict method of an constructed SHiP object.


| **Logger Submodule**
| This modules contains settings to defines log levels. Use this submodule to select the verbosity of messages during tree and hierarchy construction, and also partitioning.

Getting Started
---------------

Import the main SHiP class to construct a similarity tree and cluster the tree by using one of the available partitioning methods:

.. code-block:: python

    from SHiP import SHiP

    # Initialize with your data and preferred tree type
    ship = SHiP(data=my_data, treeType="DCTree")

    # Perform clustering with chosen parameters
    labels = ship.fit_predict(hierarchy=2, partitioningMethod="Elbow")

For more detailed usage and examples, please refer to the module-specific documentation pages.

----

The SHiP framework is implemented in C++ for performance (for C++ documentation, see :doc:`../c++_api/index`) and exposes a Python interface via pybind11 for easy integration in Python workflows.

Feel free to explore the submodules to see all the options applicable to `SHiP`.


Modules
-------
.. toctree::
   :maxdepth: 1

   Module#SHiP
   Submodule#ultrametric_tree
   Submodule#partitioning
   Submodule#logger
