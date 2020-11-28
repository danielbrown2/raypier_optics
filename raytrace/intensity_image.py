
from traits.api import Float, Instance, Bool, on_trait_change, Array
from traitsui.api import View, Item, VGroup
from chaco.api import GridDataSource, GridMapper, ImageData, Spectral,\
        DataRange1D, CMapImagePlot, DataRange2D, PlotComponent, Plot,\
        ArrayPlotData, PlotComponent, HPlotContainer, ColorBar, LinearMapper, ImagePlot
        
from chaco.default_colormaps import Spectral
        
from enable.api import ComponentEditor
from chaco.tools.api import PanTool, ZoomTool

from .results import Result
from .fields import EFieldPlane

import numpy
from numpy import inf


class ProbePlanePanTool(PanTool):
    probe = Instance(EFieldPlane)
    
    def panning_mouse_move(self, event):
        """ Handles the mouse being moved when the tool is in the 'panning'
        state.
        """
        plot = self.component

        if self._auto_constrain and self.constrain_direction is None:
            # Determine the constraint direction
            x_orig, y_orig = self._original_xy
            if abs(event.x - x_orig) > abs(event.y - y_orig):
                self.constrain_direction = "x"
            else:
                self.constrain_direction = "y"

        deltas = [0.0,0.0,0.0]
        direction_info = [("x", "width", 0), ("y", "height", 1)]
        for direction, bound_name, index in direction_info:
            if not self.constrain or self.constrain_direction == direction:
                mapper = getattr(plot, direction + "_mapper")
                domain_min, domain_max = mapper.domain_limits
                eventpos = getattr(event, direction)
                origpos = self._original_xy[index]

                deltas[index] = mapper.map_data(origpos) - mapper.map_data(eventpos)

                # Use .set_bounds() so that we don't generate two range_changed
                # events on the DataRange
        self.probe.translate_local(deltas[0], deltas[1], deltas[2])

        event.handled = True

        self._original_xy = (event.x, event.y)
        #plot.request_redraw()
        return


class IntensityImageView(Result):
    field_probe = Instance(EFieldPlane)
    
    hbox = Instance(HPlotContainer)
    cbar = Instance(ColorBar)
    crange = Instance(DataRange1D, ())
    
    ds = Instance(ArrayPlotData, ())
    intensity_data = Array()
    plot = Instance(Plot)
    image_plot = Instance(ImagePlot)
    
    pan_tool = Instance(PanTool)
    
    width = Float(1.0)
    height = Float(1.0)
    
    traits_view = View(VGroup(
            Item("hbox", editor=ComponentEditor(), show_label=False)
                ))
    
    
    def calc_intensity(self, e_field):
        E = e_field
        U = (E.real**2).sum(axis=-1) + (E.imag**2).sum(axis=-1)
        self.intensity_data = U
        return U
    
    def calc_result(self, model):
        pass
        #self.calc_intensity(self.field_probe.E_field)
        
    def _pan_tool_default(self):
        #return PanTool()
        return ProbePlanePanTool()
    
    def _field_probe_changed(self, old, new):
        if old is not None:
            old.on_trait_change(self.on_field_changed, "E_field", remove=True)
        new.on_trait_change(self.on_field_changed, "E_field")
        self.pan_tool.probe = new
        
    def on_field_changed(self, e_field):
        intensity_image = self.calc_intensity(e_field)
        
        probe = self.field_probe
        self.ds.set_data("img", intensity_image)
        side = probe.width
        yside = probe.height
        
        if self.plot is not None:
            a = probe.centre
            self.plot.title = f"Intensity @ ({a[0]:0.3f}, {a[1]:0.3f}, {a[2]:0.3f})"
            
            plot = self.image_plot
            #plot.
            plot.x_mapper.range.set_bounds(0,side)
            plot.y_mapper.range.set_bounds(0,yside)
            plot.request_redraw()
            
    def _hbox_default(self):
        hbox = HPlotContainer()
        hbox.add(self.plot)
        hbox.add(self.cbar)
        #hbox.bgcolor = 'sys_window' 
        return hbox
    
    def _cbar_default(self):
        colormap = Spectral(self.crange) #self.cmap(self.crange)
        cbar = ColorBar(index_mapper=LinearMapper(range=self.crange),
                        color_mapper=colormap,
                        padding=20, width=20, orientation='v', resizable='v')
        axis = cbar._axis
        #axis.tick_label_formatter = tick_formatter
        #cbtool = ColorbarTool(component=cbar, color_map=self.cmap.__name__)
        #cbar.tools.append(cbtool)
        self.crange.on_trait_change(self.on_rescale, "updated")
        return cbar
    
    def on_rescale(self):
        if self.hbox is not None:
            self.hbox.request_redraw()
    
    def _plot_default(self):
        probe = self.field_probe
        if probe is None:
            xside=1
            yside=1
            data = [[0.0]]
        else:
            xside = probe.width
            yside = probe.height
            data = self.calc_intensity(probe.E_field)
            
        x_bounds = (0,xside)
        y_bounds = (0,yside)
        
        ds = self.ds
        ds.set_data("img", self.intensity_data)
        plot = Plot(ds)
        imgplot = plot.img_plot("img",
                                xbounds=x_bounds,
                                ybounds=y_bounds,
                                colormap=Spectral(self.crange))[0]
        self.image_plot = imgplot
        self.cbar.index_mapper.range.sources = [self.image_plot.value]
        plot.x_axis.title = "Width /mm"
        plot.y_axis.title = "Height /mm"
        a = probe.centre
        plot.title = f"Intensity @ ({a[0]:0.3f}, {a[1]:0.3f}, {a[2]:0.3f})"
        
        pantool = PanTool(plot) #self.pan_tool
        pantool = self.pan_tool
        pantool.component = self.image_plot
        self.pan_tool = pantool
        plot.tools.append(pantool)
        
        return plot
