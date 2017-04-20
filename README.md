# CsPyController

Saffman Lab experiment controller.
Written by Martin Lichtman


## Usage Notes

### HSDIO
The high-speed digital I/O (NI PXIe-6545) instrument can be set up via the python controller entirely.

On the computer running the labview server:
 * open NI MAX and get (or set) the name (_name_) in the device settings
 
On the computer running the python controller:
 * In the PXI communication palette, the PXI communication must be enabled and connected to the labview server
 * The timeout on the PXI communciation should be longer than the measurement cycle time
 * In the HSDIO palette, the resource name field should be set to _name_
 * The number of channels should be specified e.g. 32 (increments of 32)
 * The same number of channels should be added (using the + button)
