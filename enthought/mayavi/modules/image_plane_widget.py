"""A simple ImagePlaneWidget module to view image data.

"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005, Enthought, Inc.
# License: BSD Style.

# Enthought library imports.
from enthought.traits.api import Instance
from enthought.traits.ui.api import View, Group, Item
from enthought.tvtk.api import tvtk

# Local imports
from enthought.mayavi.core.module import Module
from enthought.mayavi.core.common import error


######################################################################
# `ImagePlaneWidget` class.
######################################################################
class ImagePlaneWidget(Module):

    # The version of this class.  Used for persistence.
    __version__ = 0

    ipw = Instance(tvtk.ImagePlaneWidget, allow_none=False)

    view = View(Group(Item(name='ipw', style='custom', resizable=True),
                      show_labels=False
                      ),
                width=600,
                height=600,
                resizable=True,
                scrollable=True
                )

    ######################################################################
    # `Module` interface
    ######################################################################
    def setup_pipeline(self):
        """Override this method so that it *creates* the tvtk
        pipeline.

        This method is invoked when the object is initialized via
        `__init__`.  Note that at the time this method is called, the
        tvtk data pipeline will *not* yet be setup.  So upstream data
        will not be available.  The idea is that you simply create the
        basic objects and setup those parts of the pipeline not
        dependent on upstream sources and filters.  You should also
        set the `actors` attribute up at this point.
        """
        # Create the various objects for this module.
        self.ipw = tvtk.ImagePlaneWidget(display_text=1,
                                         key_press_activation=0,
                                         left_button_action=1,
                                         middle_button_action=0)

    def update_pipeline(self):
        """Override this method so that it *updates* the tvtk pipeline
        when data upstream is known to have changed.

        This method is invoked (automatically) when any of the inputs
        sends a `pipeline_changed` event.
        """
        mod_mgr = self.module_manager
        if mod_mgr is None:
            return

        # Data is available, so set the input for the IPW.
        input = mod_mgr.source.outputs[0]
        if not (input.is_a('vtkStructuredPoints') \
                or input.is_a('vtkImageData')):
            msg = 'ImagePlaneWidget only supports structured points or '\
                  'image data.'
            error(msg)
            raise TypeError, msg
            
        self.ipw.input = input
        # Set the LUT for the IPW.
        self.ipw.lookup_table = mod_mgr.scalar_lut_manager.lut
        
        self.pipeline_changed = True

    def update_data(self):
        """Override this method so that it flushes the vtk pipeline if
        that is necessary.

        This method is invoked (automatically) when any of the inputs
        sends a `data_changed` event.
        """
        # Just set data_changed, the component should do the rest.
        self.data_changed = True

    ######################################################################
    # Non-public methods.
    ######################################################################
    def _ipw_changed(self, old, new):
        if old is not None:
            old.on_trait_change(self.render, remove=True)
            self.widgets.remove(old)            
        new.on_trait_change(self.render)
        self.widgets.append(new)
        if old is not None:
            self.update_pipeline()