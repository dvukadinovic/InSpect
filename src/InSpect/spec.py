from bokeh.layouts import Column, Row, gridplot
from bokeh.models import Button, Slider
from bokeh.models import TabPanel, Tabs
from bokeh import palettes
from bokeh.plotting import figure, curdoc

import numpy as np
from input import spectra, mean_spectra

def get_vmin_vmax(data):
    vmin = np.min(data)
    vmax = np.max(data)
    return vmin, vmax

def plot_all(wave_index):
    if len(spectra)==0:
        return

    plot_stokes_maps(wave_index=wave_index)

    p2.line(spectra[0].wavelengths, mean_spectra[0], line_width=2, color="black", name="mean_stokes_I")
    p2.line(spectra[0].wavelengths, spectra[0].intensities[:,0,0,], line_width=2, color="red", name="local_spectrum")
    vmin, vmax = get_vmin_vmax(mean_spectra[0])
    p2.line([spectra[0].wavelengths[0], spectra[0].wavelengths[0]], [vmin, vmax], line_width=2, color="green", line_dash="dashed", name="wavelength_marker")

def plot_stokes_maps(wave_index):
    nx, ny = spectra[0].intensities.shape[1:]
    p_StokesI.image(image=[spectra[0].intensities[wave_index]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesQ.image(image=[spectra[0].spec[...,wave_index,1]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesU.image(image=[spectra[0].spec[...,wave_index,2]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")
    # p_StokesV.image(image=[spectra[0].spec[...,wave_index,3]], x=0, y=0, dw=nx, dh=ny, palette=palettes.Greys256, level="image")

def on_tap(event):
    x = event.x
    ind = np.argmin(np.abs(spectra[0].wavelengths-x))
    plot_stokes_maps(wave_index=ind)

    for name in ["wavelength_marker"]:
        render = p2.select_one({"name": name})
        if render is not None:
            p2.renderers.remove(render)

    vmin, vmax = get_vmin_vmax(mean_spectra[0])
    p2.line([spectra[0].wavelengths[ind], spectra[0].wavelengths[ind]], [vmin, vmax], line_width=2, color="green", line_dash="dashed", name="wavelength_marker")

def on_tap_maps(event):
    x = event.x
    y = event.y

    if x<0 or x>=spectra[0].intensities.shape[1] or y<0 or y>=spectra[0].intensities.shape[2]:
        return

    # remove previous renders
    for name in ["mean_stokes_I", "local_spectrum"]:
        render = p2.select_one({"name": name})
        if render is not None:
            p2.renderers.remove(render)

    p2.line(spectra[0].wavelengths, mean_spectra[0], line_width=2, color="black", name="mean_stokes_I")
    p2.line(spectra[0].wavelengths, spectra[0].intensities[:,int(y),int(x)], line_width=2, color="red", name="local_spectrum")

plot_button = Button(label="Initialize plots", button_type="primary")
plot_button.on_click(lambda event: plot_all(wave_index=0))

# Stokes panels
p_StokesI = figure(width=800, height=800, toolbar_location="above")
# p_StokesQ = figure(width=500, height=500, toolbar_location="above")
# p_StokesU = figure(width=500, height=500, toolbar_location="above")
# p_StokesV = figure(width=500, height=500, toolbar_location="above")
p_Stokes = [p_StokesI]#, p_StokesQ, p_StokesU, p_StokesV]
for p in p_Stokes:
    p.x_range.range_padding = p.y_range.range_padding = 0
    p.on_event('tap', on_tap_maps)

# stokes_grid = gridplot([[p_StokesI, p_StokesQ], [p_StokesU, p_StokesV]])
stokes_grid = gridplot([[p_StokesI]])#, [p_StokesU, p_StokesV]])

# mean Stokes I spectrum plot
p2 = figure(width=800, height=400, toolbar_location="above")
p2.on_event('tap', on_tap)