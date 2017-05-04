# CsPyController

Saffman Lab experiment controller.
Written by Martin Lichtman

## Dependencies

 * enaml (0.9.8-3 or later)
 * h5py (2.5.0-3 or later)
 * matplotlib (1.4.3-5 or later, 2 is not supported)
 * numpy (1.9.2-1 or later)
 * pyaudio (0.2.4-3 or later)
 * pypng (0.0.15-1 or later)
 * PyQt (4.11.3-1 or later)
 * pyserial (2.7-2 or later)
 * scikit learn (0.16.1-2 or later)
 * scipy (0.15.1-2 or later)
 * colorama (pip install colorama) -> for colored output logs
 * colorlog (pip install colorlog) -> for colored output logs
 * origin (see below)

### On Ubuntu

To install pyaudio in virtual environment: 

```bash
$ sudo apt-get install libjack-jackd2-dev portaudio19-dev
```
Then you can `pip install pyaudio` as normal.

To install PyQt4 in virtual environment, first install globally:
```bash
$ sudo apt-get install python-qt4
```
Then copy from `/usr/lib/python2.7/dist-packages/PyQt4` to `<virtual_enviroment_dir>/lib/python2.7/site-packages`.
Also copy `/usr/lib/python2.7/dist-packages/sip.<architecture>.so` to the same path.

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

### Origin Server
For interfacing with the origin data server.

#### Setup
You will need to download the origin package from github.
You should first navigate to a directory outside of the CsPyController directory.
The clone the package:

```bash
git clone https://github.com/QuantumQuadrate/Origin.git
```

Currently we are using the dev branch so switch to it

```bash
cd Origin
git checkout dev
```

Now you need to add the path to the python path so it can find the package when you import it.
To do this edit the path to the `CsPyController/python/origin.py` file to reflect the path of your installation.

```python
# first find ourself
fullBasePath = "C:\\LabSoftware\\Origin" #example path
```

#### Usage
The module works by automagically generating a list of per-measurement and per-iteration datasets after and experiment has been run.
You should not attempt to populate datasets you want to log, instead first run an experiment where the variable or measurement you want to record is setup to be saved to the hdf5 file.
The origin interface palette should then be populated with all the datasets you can track.
You may need to close and reopen the palette to shows changes.

Once you have populated the lists of variables, then fill in the "namespace" for your experiment.
The namespace will keep you from overwritting someone elses data, the namespace should be short and I suggest a format of the form:
```
FNODE_, RB_, AQUA_, etc.
```
You will not be able to record data without a namespace or a stream name and any stream you enable will be automatically disabled in the palette when running an experiment, if you fail to comply.

Now find the variable you want to record in the list of variables, give it a name (remember the namespace will be prepended to the stream name).
Verify that the data type is correct (numpy datatypes are used), the most common time it wont be is if an integer is detected but the value will sometimes be a float.
If this is the case change the int32 to a float32, or whatever is appropriate from the numpy datatypes.
Finally, click the stream checkbox and verify that the enable box is checked at the top.
If you are testing with a local server, make sure the test box is checked (and you have the local origin server running).

When you run the experiment, data will now be logged on a per-iteration or per-measurement basis based on the type of data you are logging.

If you run into an issue try removing the offending variables from the list with the remove button.
Re-running the experiment will repopulate the list.
