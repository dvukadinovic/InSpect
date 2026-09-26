import panel as pn
from panel import Tabs, Row, Column

from input import files, load_files_button, info_box
from .spec import stokes_grid, plot_button, p2

# pn.curdoc().title = "InSpect"

tabs = Tabs(
    ("Files", Column(Row(load_files_button, info_box), files)),
    ("Spectra", Column(plot_button, stokes_grid, p2)),
    # ("Inversions", Column(inversions_table, inversions_plot)),
)
tabs.servable()