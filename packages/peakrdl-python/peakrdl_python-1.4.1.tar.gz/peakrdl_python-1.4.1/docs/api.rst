Python API
**********

PeakRDL Python can be used from a python API to generate the python package.
This approach may be useful if multiple operations need to be sequenced for
example:

* A build process that has multiple files dependencies
* A build process that needs other IP-XACT inputs
* A build process that will use other tools form the PeakRDL Suite, for example:

    * building HTML documentation with PeakRDL HTML
    * building UVM using PeakRDL UVM

Example
=======

The following example shows the compiling an SystemRDL file and then generating
the python register access layer using PeakRDL Python.



.. code-block:: python

    from peakrdl_python import compiler_with_udp_registers
    from peakrdl_python.exporter import PythonExporter

    # compile the systemRDL
    rdlc = compiler_with_udp_registers()
    rdlc.compile_file('basic.rdl')
    spec = rdlc.elaborate(top_def_name='basic').top

    # generate the python package register access layer
    exporter = PythonExporter()
    exporter.export(node=spec, path='generated_code')


PythonExporter
==============

The main exported class used to build the python register access layer:

.. autoclass:: peakrdl_python.exporter.PythonExporter
    :members:
    :special-members: __init__

Compiler Extensions
-------------------

PeakRDL Python uses two User Defined Properties to help the generation, there are definitions of
these available to register with a the Compiler

.. autoclass:: peakrdl_python.PythonHideUDP
    :members:


.. autoclass:: peakrdl_python.PythonInstNameUDP
    :members:

The compiler factory function will generate an instance of the compiler with these registered

.. autofunction:: peakrdl_python.compiler_with_udp_registers
