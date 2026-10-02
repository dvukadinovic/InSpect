import panel as pn
from panel import Tabs, Row, Column, VSpacer
from panel.layout import Divider

from spec import header, main_plots
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
                       main_plots, 
                       width_policy="max",
                       sizing_mode="stretch_both"
                       )
    ),
    title="InSpect",
    width_policy="max",
    sizing_mode="stretch_both"
)
tabs.servable()