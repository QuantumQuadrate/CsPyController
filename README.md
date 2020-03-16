# CsPyController

Saffman Lab experiment controller.
Written by Martin Lichtman

## Installation

### Python Requirements

It is highly recommended that you use a pip-compatible environment manager to 
handle your dependency installation. Our recommendation is virtualenv with 
either virtualenvwrapper or virtualenvwrapper-win depending on your OS.

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

### National Instruments

The CsPy controller depends on two LabVIEW servers for functionality. In order 
to run these servers, some National Instruments drivers as well as a run-time
version of LabVIEW is necessary. To be able to edit the servers, a development
version is necessary. All of the necessary installers for National Instruments
software compatible with Windows 7 or Windows 10 systems can be found in the
public folder of the lab's Hexagon server. A machine running the PXI server
requires all of the dependencies whereas one only running the DDS server only
needs the LabVIEW installation and the 845x drivers. If CsPy is the only LabVIEW
dependency for your computer and you already have other development versions of
LabVIEW installed, it is recommended to use the NI Package Manager to uninstall
all previously installed dependencies prior to installing the CsPy dependencies.
It is highly recommended that you make a system restore point prior to your
uninstallation process so that it may be reverted if that becomes necessary. If
any of the drivers give you options for which LabVIEW versions to add support
for, select only 32-bit LabVIEW 2014 and 2015. Any time the National Instruments
update service tells you there is a Critical Update, install it. Always remain
up to date on the Critical Updates. The non-critical updates are unnecessary.
### Configuration files

Some parameters need to be specified before the controller is started, such as 
DLL paths and python modules not installed globally. Additionally there are 
experiment specific parameters that rarely or never change. These are all good 
candidates for entries in a config file. Basically if you ever thought hey I 
wish X experiment would stop overwriting my Y whenever they makes changes, Y 
should be moved to the config file.

To prevent everyone form just overwriting each others config files perpetuating
the cycle, everyone makes their own config file with a descriptive name such as
`config_FNODE.cfg` or `config_AQUA.cfg`. You then, on your Windows machine, 
run cmd.exe as administrator, navigate to the config folder for the controller 
and run the following code:
```bash
mklink config.cfg config_<EXPERIMENT TAG>.cfg
```
which makes a symbolic (soft) link to your actual `config_<EXPERIMENT TAG>.cfg` 
file whenever the experiment looks for `config.cfg` and no one has to yell at 
anyone else anymore.

The configuration file is stored in the settings and data files as a JSON 
string.
In the event that the configuration file differs from the saved JSON 
configuration in the settings, the user will be prompted at startup to choose 
which version they want to use.
## Usage Notes

### Threaded Analysis

Threaded analyses are now built into the CsPyController, but analyses are not 
threaded by default since I do not have the ability to test everyone's analyses.
In order to enable threading for your analysis you need to add some code to the 
`__init__` class method for your analysis. To see how this works let's say we 
have two analyses `Analysis1` and `Analysis2`, and `Analysis2` depends on the 
results of `Analysis1`. `Analysis1` only depends on instrument data, and no 
other analysis. The contents of the `__init__` method for `Analysis1` would 
look like this:
```python
def __init__(self, experiment, desc=None):
    if desc is None:
        desc = ''
    super(Analysis1, self).__init__('Analysis1', experiment, desc)
    # initialize Analysis1 here
    self.queueAfterMeasurement = True  # enable threading for analysis
```
`Analysis2` is then:
```python
def __init__(self, experiment, desc=None):
    if desc is None:
        desc = ''
    super(Analysis2, self).__init__('Analysis2', experiment, desc)
    # initialize Analysis2 here
    self.queueAfterMeasurement = True  # enable threading for analysis
    self.measurementDependencies += [self.experiment.Analysis1Obj]
```
Note that `self.experiment.Analysis1Obj` refers to the instantiation of the 
`Analysis1` class named `Analysis1Obj` in your experiment class file.

### National Instruments
The high-speed digital I/O (NI PXIe-6545) instrument and other such PXIe/PCIE
cards can be set up via the python controller entirely.

On the computer running the labview server:
 * open NI MAX and get (or set) the name (_name_) in the device settings

On the computer running the python controller:
 * In the PXI communication palette, the PXI communication must be enabled and 
 connected to the labview server
 * The timeout on the PXI communciation should be longer than the measurement 
 cycle time
 * In the HSDIO palette, the resource name field should be set to _name_
 * The number of channels should be specified e.g. 32 (increments of 32)
 * The same number of channels should be added (using the + button)

### Functional Waveforms

The functional waveforms module may throw an error ("Exception in HSDIO: index 
2 is out of bounds for axis 0 with size 2") if there is a channel in the HSDIO 
or Analog Out waveforms that has one or fewer defined intervals. This may also 
appear as an exception in functional_waveforms_graph.draw_digital(). As a 
workaround, I've added the following to the init function in our functional 
waveforms file (it adds a 100 microsecond 'off' period to the beginning of the 
sequence to ensure that all channels have at least two defined values):

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
You can specify Origin behavior by modifying the below lines in your config 
file. As of the time of writing, all of the experiments use the same Origin 
configurations. If you need different behavior, simply make new Origin config 
files for yourself and adjust your experiment config file to match.

```python
[ORIGIN]
OriginTest = False ; if true communciate with a local origin server
OriginCfgPath = config/origin_config
```

#### Usage
The module works by automagically generating a list of per-measurement and 
per-iteration datasets after and experiment has been run. You should not attempt
to populate datasets you want to log, instead first run an experiment where the
variable or measurement you want to record is setup to be saved to the hdf5 
file. The origin interface palette should then be populated with all the 
datasets you can track. You may need to close and reopen the palette to show
changes.

Once you have populated the lists of variables, then fill in the "namespace" for
your experiment. The namespace will keep you from overwritting someone elses 
data, the namespace should be short and I suggest a format of the form:
```
FNODE_, RB_, AQUA_, etc.
```
You will not be able to record data without a namespace or a stream name and any
stream you enable will be automatically disabled in the palette when running an 
experiment, if you fail to comply.

Now find the variable you want to record in the list of variables, give it a 
name (remember the namespace will be prepended to the stream name). Verify that 
the data type is correct (numpy datatypes are used), the most common time it 
won't be is if an integer is detected but the value will sometimes be a float.
If this is the case change the int32 to a float32, or whatever is appropriate 
from the numpy datatypes. Finally, click the stream checkbox and verify that the
enable box is checked at the top. If you are testing with a local server, make 
sure the test box is checked (and you have the local origin server running).

When you run the experiment, data will now be logged on a per-iteration or 
per-measurement basis based on the type of data you are logging.

If you run into an issue try removing the offending variables from the list 
with the remove button. Re-running the experiment will repopulate the list.
