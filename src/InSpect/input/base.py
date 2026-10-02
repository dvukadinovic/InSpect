from panel.widgets import FileSelector, Button
from panel.pane import Alert
import numpy as np

from .mps_atlas import load_spectrum

spectra = []
mean_spectra = []
cog_velocity = []

class FileTreeSelector(FileSelector):
    def __init__(self, **params):
        super().__init__(**params)
        self._file_selector = FileSelector(**params)

def load_files(event):
    global spectra
    fpaths = files.value
    try:
        for path in fpaths:
            spec = load_spectrum(path)
            spectra.append(spec)
            mean_spectra.append(np.mean(spec.intensities, axis=(1,2)))
            info_box.object = f"Loaded spectrum from {path}"
            info_box.alert_type = "success"
    except Exception as e:
        info_box.object = f"Error loading file: {e}"
        info_box.alert_type = "warning"

# File Selector widget
root_dir = "~/Documents/uni-graz/projects/rv_metallicity/spectra/mhm10"
files = FileTreeSelector(directory=root_dir, label="Select a file(s)")
files.value = ["/home/dusan/Documents/uni-graz/projects/rv_metallicity/spectra/mhm10/Fe6299_vald_05_06_mhm1.0_4bin/G2_mhm10_SSD_4bin_371000/result_Int.371000_0_part_01.nc"]

# button to load files
load_files_button = Button(name="Load Files", button_type="primary")
load_files_button.on_click(load_files)

# info box regarding data loading
info_box = Alert(object="", alert_type="info", visible=True)

# progress bar for loading files