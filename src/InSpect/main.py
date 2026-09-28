import panel as pn
from panel import Tabs, Row, Column, VSpacer
from panel.layout import Divider

from spec import stokes_grid, header, p2
from input import files, load_files_button, info_box

# pn.curdoc().title = "InSpect"

tabs = Tabs(
    ("Files", Column(Row(load_files_button, 
                         info_box
                     ), 
                     files,
                     width_policy="max",
                     sizing_mode="stretch_both"
                    )
    ),
    ("Spectra", Column(header,  
                       Divider(margin=10),
                       Row(p2, stokes_grid, margin=10), 
                       width_policy="max",
                       sizing_mode="stretch_both"
                       )
    ),
    width_policy="max",
    sizing_mode="stretch_both"
)
tabs.servable()