from matplotlib.pyplot import plot
from panel import Column, Row
from panel.widgets import StaticText, TextInput

from bokeh.models import Button, HoverTool
from bokeh import palettes
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper, ColorBar

import numpy as np
from scipy.constants import c as SPEED_OF_LIGHT
import colorcet as cc

from input import spectra, mean_spectra, cog_velocity

TOOLTIPS = [
    ("(x,y)", "($x{int}, $y{int})"),
]

INITIALIZED = False
INITIALIZED_COG = False
NORMALIZED = False
FONT_SIZE = "12pt"

XPOS = 0
YPOS = 0

p_COG = None

def plot_pixel_position(x, y, nx, ny):
    x_info.value = f"{x:d}"
    y_info.value = f"{y:d}"

    for p in p_Stokes:
        p.line([x,x], [0,ny], line_width=2, color="red", name="pixel_marker_x")
        p.line([0,nx], [y,y], line_width=2, color="red", name="pixel_marker_y")

def initialize_plots(wave_index):
    global INITIALIZED

    if len(spectra)==0:
        return
    nx, ny = spectra[0].intensities.shape[1:]

    # clear all figures from previous renderers
    for p in p_Stokes:
        p.renderers = []
    p2.renderers = []

    plot_stokes_maps(wave_index=wave_index)
    plot_pixel_position(XPOS, YPOS, nx, ny)

    plot_mean_and_current_spectrum(XPOS, YPOS)
    plot_vertical_line_at_wavelength(wave_index=wave_index)

    INITIALIZED = True

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
    wavelength_info.value = f"{spectra[0].wavelengths[wave_index]:.4f} nm"
    p2.vspan(x=[spectra[0].wavelengths[wave_index]], line_width=2, color="green", line_dash="dashed", name="wavelength_marker")
    
def on_wavelength_click(event):
    if not INITIALIZED:
        return

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
    global XPOS, YPOS

    if not INITIALIZED:
        return

    x = int(event.x)
    y = int(event.y)
    nx = spectra[0].intensities.shape[1]
    ny = spectra[0].intensities.shape[2]

    if x<0 or x>=nx or y<0 or y>=ny:
        return
    
    XPOS = x
    YPOS = y
    
    plot_mean_and_current_spectrum(XPOS, YPOS)

    # remove previous pixel position markers on map plot
    for p in p_Stokes:
        for name in ["pixel_marker_x", "pixel_marker_y"]:
            render = p.select_one({"name": name})
            if render is not None:
                p.renderers.remove(render)

    plot_pixel_position(XPOS, YPOS, nx, ny)

def on_cog_click(event):
    if not INITIALIZED and p_COG is None:
        return
    
    x = int(event.x)
    y = int(event.y)
    nx = spectra[0].intensities.shape[1]
    ny = spectra[0].intensities.shape[2]

    if x<0 or x>=nx or y<0 or y>=ny:
        return

    cog_velocity_info.value = f"{cog_velocity[0][x,y]:.4f} m/s"

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

def initialize_COG_plot():
    global p_COG
    global INITIALIZED_COG

    if INITIALIZED_COG:
        return

    p_COG = figure(width=730, height=700, title="Center-of-gravity velocity", toolbar_location="above", tooltips=TOOLTIPS, styles={"font-size": FONT_SIZE})
    p_COG.xaxis.axis_label = "x [px]"
    p_COG.yaxis.axis_label = "y [px]"
    p_COG.on_event('tap', on_cog_click)

    main_plots.append(Column(cog_velocity_info, Row(p_COG)))

    INITIALIZED_COG = True

def compute_COG_velocity():
    global cog_velocity

    if not NORMALIZED:
        return None
    
    initialize_COG_plot()

    for name in ["cog_velocity_image"]:
        render = p_COG.select_one({"name": name})
        if render is not None:
            p_COG.renderers.remove(render)

    lam0 = float(central_wavelength_input.value)

    for ids in range(len(spectra)):
        mask_outliers = np.ones(np.shape(spectra[ids].intensities), dtype=bool)
        mask_outliers[np.abs(spectra[ids].intensities)>2] = 0
        intensities = spectra[ids].intensities * mask_outliers
        
        numerator = np.sum(spectra[ids].wavelengths[:, np.newaxis, np.newaxis] * (1. - intensities), axis=0)
        denominator = np.sum(1. - intensities, axis=0)
        cog_shift =  numerator / denominator / lam0 - 1
        cog_velocity.append(-cog_shift * SPEED_OF_LIGHT)

        vmin, vmax = np.quantile(cog_velocity[ids], [0.14, 0.86])
        vmax = np.max(np.abs([vmin, vmax]))
        vmin = -vmax

    color_mapper = LinearColorMapper(palette=cc.coolwarm, low=vmin, high=vmax)
    p_COG.image(image=[cog_velocity[0]], x=-0.5, y=-0.5, dw=cog_velocity[0].shape[0], dh=cog_velocity[0].shape[1], color_mapper=color_mapper, level="image", name="cog_velocity_image")

    color_bar = ColorBar(color_mapper=color_mapper, width=20, label_standoff=12, border_line_color=None, location="right")
    p_COG.add_layout(color_bar, 'right')

#--- header info and option
plot_button = Button(label="Initialize plots", button_type="primary", margin=(10, 5, 5, 10))
plot_button.on_click(lambda event: initialize_plots(wave_index=0))

normalize_button = Button(label="Normalize", button_type="primary", margin=(5, 5, 5, 10))
normalize_button.on_click(normalize_spectra)

calculate_COG_button = Button(label="Calculate COG", button_type="primary", margin=(5, 5, 5, 10))
calculate_COG_button.on_click(lambda event: compute_COG_velocity())

central_wavelength_input = TextInput(value="", placeholder='Enter a line central wavelength...', label="Central wavelength [nm]", width=200, margin=(5, 5, 5, 10))

# header = Column(Row(plot_button, width_policy="max"), sizing_mode="stretch_both", width_policy="max")
header = Column(plot_button, normalize_button, Row(calculate_COG_button, central_wavelength_input), max_height=150, sizing_mode="stretch_both", width_policy="max")

#--- main plot panels
# Stokes panels
p_StokesI = figure(width=700, height=700, toolbar_location="above", title="Stokes I", styles={"font-size": FONT_SIZE}, tooltips=TOOLTIPS)
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
p2 = figure(width=800, height=400, toolbar_location="above", title="Stokes I spectrum", styles={"font-size": FONT_SIZE})
p2.on_event('tap', on_wavelength_click)
p2.xaxis.axis_label = "wavelength [nm]"
p2.yaxis.axis_label = "Absolute intensity"
p2.add_tools(HoverTool(tooltips=[("wavelength", "@x{0[.]0000}"), 
                                 ("intensity", "@y")],
                        mode="vline",
                    )
            )

wavelength_info = StaticText(label="wavelength", value="nan", width=300, height=30, margin=(10, 5, 10, 50), name="wavelength_info", styles={"font-size": FONT_SIZE})
x_info = StaticText(label="x", value="nan", width=100, height=30, margin=(10, 5, 5, 50), name="x_info", styles={"font-size": FONT_SIZE})
y_info = StaticText(label="y", value="nan", width=100, height=30, margin=(10, 5, 10, 5), name="y_info", styles={"font-size": FONT_SIZE})
cog_velocity_info = StaticText(label="COG velocity", value="nan", width=300, height=30, margin=(10, 5, 10, 50), name="cog_velocity_info", styles={"font-size": FONT_SIZE})

main_plots = Row(Column(Row(x_info, y_info), p2), Column(wavelength_info, stokes_grid))