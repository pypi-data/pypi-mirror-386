How to migrate from plotpy V1
-----------------------------

This section describes the steps to migrate python code using plotpy V1 to plotpy V2.

Updating the imports
^^^^^^^^^^^^^^^^^^^^

PlotPy V1 to PlotPy V2
~~~~~~~~~~~~~~~~~~~~~~

The following table gives the equivalence between plotpy V1 and plotpy V2 imports
or objects.

For most of them, the change in the module path is the only difference (only
the import statement have to be updated in your client code). For others, the
third column of this table gives more details about the changes that may be
required in your code.

.. csv-table:: Compatibility table
    :file: v1_to_v2.csv

PlotPy V1 to guidata V3
~~~~~~~~~~~~~~~~~~~~~~~

With the release of PlotPy V2, the ``DataSet`` related features have been moved
to the `guidata` package (from where they were originally extracted).

The following table gives the equivalence between PlotPy V1 and guidata V3 imports
or objects.

.. csv-table:: Compatibility table
    :file: v1_to_guidata_v3.csv

New method for thresholding image item LUTs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The method :py:meth:`plotpy.items.BaseImageItem.set_lut_threshold` has been
added. It allows to set the percentage of outliers to be clipped from the image
histogram values.

This method is available for all image items:

* :py:class:`.ImageItem`
* :py:class:`.XYImageItem`
* :py:class:`.MaskedImageItem`
* :py:class:`.TrImageItem`

New options added to plot builder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``PlotItemBuilder`` factory class has been renamed to :py:class:`.PlotBuilder`,
because it provides not only methods for creating plot items, but also methods
for creating ready-to-use plots.

New methods for creating ready-to-use plots have been added to the class:

* :py:meth:`.PlotBuilder.widget`
* :py:meth:`.PlotBuilder.dialog`
* :py:meth:`.PlotBuilder.window`

The method :py:meth:`.PlotBuilder.contours` has been added, in order to create
contour curves. It returns a list of :py:class:`plotpy.items.ContourItem` objects.

See demo script `tests/items/test_contour.py`.

The new keyword parameter ``alpha_function`` has been added to the methods
:py:meth:`.PlotBuilder.image`, :py:meth:`.PlotBuilder.xyimage`,
:py:meth:`.PlotBuilder.maskedimage`, :py:meth:`.PlotBuilder.maskedxyimage`,
:py:meth:`.PlotBuilder.trimage`, :py:meth:`.PlotBuilder.rgbimage`, and
:py:meth:`.PlotBuilder.quadgrid`. It allows to specify a function to
compute the alpha channel of the image from the data values. The supported
functions are:

* :py:attr:`plotpy.constants.LUTAlpha.NONE` (default)
* :py:attr:`plotpy.constants.LUTAlpha.CONSTANT`
* :py:attr:`plotpy.constants.LUTAlpha.LINEAR`
* :py:attr:`plotpy.constants.LUTAlpha.SIGMOID`
* :py:attr:`plotpy.constants.LUTAlpha.TANH`
* :py:attr:`plotpy.constants.LUTAlpha.STEP`

.. warning:: The ``alpha_mask`` parameter has been removed from the methods
             :py:meth:`.PlotBuilder.image`, :py:meth:`.PlotBuilder.xyimage`,
             :py:meth:`.PlotBuilder.maskedimage`, :py:meth:`.PlotBuilder.maskedxyimage`,
             :py:meth:`.PlotBuilder.trimage`, :py:meth:`.PlotBuilder.rgbimage`, and
             :py:meth:`.PlotBuilder.quadgrid`. If you were using it, you should
             replace it by the new ``alpha_function`` parameter.

Plot item icon handling
^^^^^^^^^^^^^^^^^^^^^^^

The `guiqwt` library was allowing to instantiate plot items without needing to create
a `QApplication` instance (no GUI event loop was required). This was not the case with
`plotpy` V1, so that it was not possible -for example- to serialize/deserialize plot
items to JSON without creating a `QApplication` instance.

With `plotpy` V2, this has been fixed by removing the `QIcon` instantiation from the
plot items constructors (call to `QwtPlotItem.setIcon` method).

Note that -in the meantime- `QwtPlotItem.setIcon` and `QwtPlotItem.icon` methods have
also been removed in PythonQwt V0.14.3.

Code relying on this feature should thus be updated to use the new `get_icon_name`
method instead, i.e. `get_icon(item.get_icon_name())` instead of `item.icon()`.
