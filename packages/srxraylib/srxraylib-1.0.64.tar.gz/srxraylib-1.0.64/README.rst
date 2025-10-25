==========
SR-xraylib
==========

About
-----

Miscellaneous utilities and tools for synchrotron radiation and x-ray optics.

The classes and functions here can be used in a standalone more. They include:

* metrology: tools for x-ray optics metrology, including dabam (DAtaBAse for Metrology profiles) [1,2].
* plot: plotting tools. GOL (Graphics in One Line) contain functions to make easily simple plots using matplotlib.
* synchrotron sources: srfunc contains functions to calculate synchrotron emission of bending magnets and wigglers.
* util:
    * data_structors: igor-like data structures.
    * h5_simple_writer: simple writer for hdf5 files.
    * inverse_method_sampler: classes for generating random numbers following given 1D, 2D and 3D probability distribution functons

Documentation
-------------
https://srxraylib.readthedocs.io/


Source repository
-----------------
https://github.com/oasys-kit/sr-xraylib

Quick-installation
------------------
srxraylib can be installed with Python 3.x:

.. code-block:: console

    $ python -m pip install srxraylib

References
----------
[1] https://github.com/oasys-kit/DabamFiles

[2] http://dx.doi.org/10.1107/S1600577516005014