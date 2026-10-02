### Introduction

A lightweight browser viewer for exploring the spectral cubes computed using the MPS-ATLAS code.

Start the server locally with:

`panel serve src/InSpect [--port your_desired_port_number]`

If running on the server (e.g. MPCDF Raven), create the ssh tunnel for the desired port and open in the local browser instead:

`ssh -NfL port_number:localhost:port_number uname@server.address`

Have fun!

### To Do

- [x] button to compute COG velocity and plot it to the side of the intensity map
- [ ] bug fix for the COG map colorbar initialization
- [ ] button for spaxel averaging (with optional input on the size of spaxels)
- [ ] drop down menu to select which spectrum to plot (if we loaded more than one)
- [ ] plot average spectrum in selected region (allow for multiple selections)
- [ ] colormap selector (for intensity and COG plots)
