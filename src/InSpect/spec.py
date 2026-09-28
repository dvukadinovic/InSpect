from panel import Column, Row

from bokeh.models import Button, HoverTool
from bokeh import palettes
from bokeh.plotting import figure, ColumnDataSource

import numpy as np

from input import spectra, mean_spectra

TOOLTIPS = [
    ("(x,y)", "($x{int}, $y{int})"),
]

NORMALIZED = False

def plot_pixel_position(x, y, nx, ny):
    for p in p_Stokes:
        p.line([x,x], [0,ny], line_width=2, color="red", name="pixel_marker_x")
        p.line([0,nx], [y,y], line_width=2, color="red", name="pixel_marker_y")

def initialize_plots(wave_index):
    if len(spectra)==0:
        return
    nx, ny = spectra[0].intensities.shape[1:]

    # clear all figures from previous renderers
    for p in p_Stokes:
        p.renderers = []
    p2.renderers = []

    plot_stokes_maps(wave_index=wave_index)
    plot_pixel_position(0, 0, nx, ny)

    plot_mean_and_current_spectrum(0, 0)
    plot_vertical_line_at_wavelength(wave_index=wave_index)

def plot_stokes_maps(wave_index):
    nx, ny = spectra[0].intensities.shape[1:]
    p_StokesI.image(image=[spectra[0].intensities[wave_index]], x=-0.5, y=-0.5, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesQ.image(image=[spectra[0].intensities[wave_index+10]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesU.image(image=[spectra[0].intensities[wave_index+20]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesV.image(image=[spectra[0].intensities[wave_index+30]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")

def plot_mean_and_current_spectrum(x, y):
    # remove previous renders on wavelength plot
    for name in ["mean_stokes_I", "local_spectrum"]:
        render = p2.select_one({"name": name})
        if render is not None:
            p2.renderers.remove(render)

    p2.line(spectra[0].wavelengths, mean_spectra[0], line_width=2, color="black", name="mean_stokes_I")
    p2.line(spectra[0].wavelengths, spectra[0].intensities[:,int(y),int(x)], line_width=2, color="red", name="local_spectrum")

def plot_vertical_line_at_wavelength(wave_index):
    p2.vspan(x=[spectra[0].wavelengths[wave_index]], line_width=2, color="green", line_dash="dashed", name="wavelength_marker")
    
def on_wavelength_click(event):
    x = event.x
    ind = np.argmin(np.abs(spectra[0].wavelengths-x))

    plot_stokes_maps(wave_index=ind)

    # remove previous wavelength marker on wavelength plot
    for name in ["wavelength_marker"]:
        render = p2.select_one({"name": name})
        if render is not None:
            p2.renderers.remove(render)

    plot_vertical_line_at_wavelength(wave_index=ind)

def on_image_click(event):
    x = int(event.x)
    y = int(event.y)
    nx = spectra[0].intensities.shape[1]
    ny = spectra[0].intensities.shape[2]

    if x<0 or x>=nx or y<0 or y>=ny:
        return
    
    plot_mean_and_current_spectrum(x, y)

    # remove previous pixel position markers on map plot
    for p in p_Stokes:
        for name in ["pixel_marker_x", "pixel_marker_y"]:
            render = p.select_one({"name": name})
            if render is not None:
                p.renderers.remove(render)

    plot_pixel_position(x, y, nx, ny)

def normalize_spectra():
    global NORMALIZED

    if NORMALIZED:
        return 

    k = (mean_spectra[0][-1] - mean_spectra[0][0])/(spectra[0].wavelengths[-1] - spectra[0].wavelengths[0])
    n = mean_spectra[0][0] - k*spectra[0].wavelengths[0]
    continuum = k*spectra[0].wavelengths + n

    for i in range(len(spectra)):
        spectra[i].intensities /= continuum[:, np.newaxis, np.newaxis]
        mean_spectra[i] /= continuum

    NORMALIZED = True
    p2.yaxis.axis_label = "Normalized intensity"

    initialize_plots(wave_index=0)

#--- header info and option
plot_button = Button(label="Initialize plots", button_type="primary", margin=10)
plot_button.on_click(lambda event: initialize_plots(wave_index=0))

normalize_button = Button(label="Normalize", button_type="primary", margin=10)
normalize_button.on_click(normalize_spectra)

# header = Column(Row(plot_button, width_policy="max"), sizing_mode="stretch_both", width_policy="max")
header = Column(plot_button, normalize_button, max_height=150, sizing_mode="stretch_both", width_policy="max")

#--- main plot panels
# Stokes panels
p_StokesI = figure(width=700, height=700, toolbar_location="above", tooltips=TOOLTIPS)
# p_StokesQ = figure(width=700, height=700, toolbar_location="above", tooltips=TOOLTIPS)
# p_StokesU = figure(width=700, height=700, toolbar_location="above", tooltips=TOOLTIPS)
# p_StokesV = figure(width=700, height=700, toolbar_location="above", tooltips=TOOLTIPS)
p_Stokes = [p_StokesI]#, p_StokesQ, p_StokesU, p_StokesV]
for p in p_Stokes:
    p.x_range.range_padding = p.y_range.range_padding = 0
    p.on_event('tap', on_image_click)
    p.xaxis.axis_label = "x [px]"
    p.yaxis.axis_label = "y [px]"

# stokes_grid = Column(Row(p_StokesI, p_StokesQ), Row(p_StokesU, p_StokesV), sizing_mode="stretch_both", width_policy="max")
stokes_grid = Column(p_StokesI, sizing_mode="stretch_both", width_policy="max")

# mean Stokes I spectrum plot
p2 = figure(width=800, height=400, toolbar_location="above")
p2.on_event('tap', on_wavelength_click)
p2.xaxis.axis_label = "wavelength [nm]"
p2.yaxis.axis_label = "Absolute intensity"
p2.add_tools(HoverTool(tooltips=[("wavelength", "@x{0[.]0000}"), 
                                 ("intensity", "@y")],
                        mode="vline",
                    )
            )