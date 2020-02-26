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
 * pyzmq (pip install zmq) -> zmq communication for origin and pypico server
 * dicttoxml -> used for some labview xml communication (I forked the main copy of this to fix some annoying things)
 * origin (see below)

### On Ubuntu

Alomost everything can be installed with:
```bash
$ pip install -r requirements.txt
```

This gives us most of our python dependencies. Some additional dependencies may
exist on a per-experiment basis if hardware that your experiment uses requires
dlls or other external code. One additional requirement we all need but 
unfortunately cannot pip install is PyQT4. Instead, you can find a windows wheel
for PyQt4 at the below link. The filename of the wheel you want is most likely
PyQt4‑4.11.4‑cp27‑cp27m‑win_amd64.whl. Download the wheel and pip install it in
your virtual environment.

[QT Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt4)

First though install the system level pyaudio dependencies below.

To install pyaudio in virtual environment:

```bash
$ sudo apt-get install libjack-jackd2-dev portaudio19-dev
```
Then you can `pip install pyaudio` as normal.

The requirement.txt file does not include the PyQt4 dependency so install it by doing the following.
To install PyQt4 in virtual environment, first install globally:
```bash
$ sudo apt-get install python-qt4
```
Then copy from `/usr/lib/python2.7/dist-packages/PyQt4` to `<virtual_enviroment_dir>/lib/python2.7/site-packages`.
Also copy `/usr/lib/python2.7/dist-packages/sip.<architecture>.so` to the same path.

If you use matplotlib 1.5.0 or greater there is an issue when importing `NavigationToolbar2QTAgg`.
You can just edit the backend code to call `NavigationToolbar2QT` instead or downgrade to 1.4.

## Configuration files

Some parameters need to be specified before the controller is started, sich as DLL paths and python modules not installed globally.
Additionally there are experiment specific parameters that rarely or never change.
These are all good candidates for entries in a config file.
Basically if you ever thought hey I wish X experiment would stop overwriting my Y whenever they makes changes, Y should be moved to the config file.

To prevent everyone form just overwriting each others config files perpetuating the cycle, everyone makes their own config file with a discriptive name such as `config_FNODE.cfg` or `config_AQUA.cfg`.
You then, on your Windows machine, run cmd.exe as administrator, navigate to the python folder for the controller and run the following code:
```bash
mklink config\config.cfg config\config_<EXPERIMENT TAG>.cfg
```
which makes a symbolic (soft) link to your actual `config_<EXPERIMENT TAG>.cfg` file whenever the experiment looks for `config.cfg` and no one has to yell at anyone else anymore.

On a linux machine run:
```bash
ln -s config_<EXPERIMENT TAG>.cfg config.cfg
```

The configuration file is stored in the settings and data files as a JSON string.
In the event that the configuration file differs from the saved JSON configuration in the settings, the user will be prompted at startup to choose which version they want to use.

## Threaded Analysis

Threaded analyses are now built into the CsPyController, but analyses are not threaded by default since I do not have the ability to test everyone's analyses.
In order to enable threading for your analysis you need to add some code to the `__init__` class method for your analysis.
To see how this works let's say we have two analyses `Analysis1` and `Analysis2`, and `Analysis2` depends on the results of `Analysis1`.
`Analysis1` only depends on instrument data, and no other analysis.
The contents of the `__init__` method for `Analysis1` would look like this:
```python
def __init__(self, experiment, desc=None):
    super(Analysis1, self).__init__('Analysis1', experiment, 'description of Analysis1')
    # initialize Analysis1 here
    self.queueAfterMeasurement = True  # enable threading for analysis
```
`Analysis2` is then:
```python
def __init__(self, experiment, desc=None):
    super(Analysis2, self).__init__('Analysis2', experiment, 'description of Analysis2')
    # initialize Analysis2 here
    self.queueAfterMeasurement = True  # enable threading for analysis
    self.measurementDependencies += [self.experiment.Analysis1Obj]
```
Note that `self.experiment.Analysis1Obj` refers to the instantiation of the `Analysis1` class named `Analysis1Obj` in the main `aqua.py` file.

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

### Functional Waveforms

The functional waveforms module may throw an error ("Exception in HSDIO: index 2 is out of bounds for axis 0 with size 2") if there is a channel in the HSDIO or Analog Out waveforms that has one or fewer defined intervals. This may also appear as an exception in functional_waveforms_graph.draw_digital(). As a workaround, I've added the following to the init function in our functional waveforms file (it adds a 100 microsecond 'off' period to the beginning of the sequence to ensure that all channels have at least two defined values):

```
def initAll(t=0):
    for chan in range(NUM_HSDIO_CHANNELS):
        HSDIO(0, chan, False)
        HSDIO(0.1, chan, False)
    for chan in range(NUM_ANALOG_CHANNELS):
        AO_Set(0, chan, 0)
        AO_Set(0.1, chan, 0)
    t += 0.1
```

### Origin Server
For interfacing with the origin data server.

#### Setup
You will need to download the origin package from github.
You should first navigate to a directory outside of the CsPyController directory.
The clone the package:

```bash
git clone https://github.com/QuantumQuadrate/Origin.git
```

Now you need to add the path to the python path so it can find the package when you import it.
To do this edit the config file `CsPyController/python/config/config_<EXPTAG>.cfg` to reflect the path of your installation.

```python
OriginInstallPath = "C:\\LabSoftware\\Origin" ; example path
```

I forked the xmltodict module on pip because the author put in a bunch of log statements that end up poluting
our logging.
I deleted them, but to avoid it you have to install my fork, so:
```bash
pip install -e git+https://github.com/mfe5003/dicttoxml#egg=dicttoxml
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
