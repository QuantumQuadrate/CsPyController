"""instrument_property.py
This file contains the mechanism for a property that describes some setting of an instrument.  A Prop can be saved and loaded.
A Prop can have properties of its own.
A Prop has extensions like EvalProp from a setting that takes some string input and is evaluated.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Atom, Str, Bool, Int, Float, List, Member, Value, observe
from enaml.validator import Validator
from enaml.application import deferred_call

import pickle, traceback, h5py, numpy
import cs_evaluate


# class myBool(Bool):
#     """This class extends an Atom.Bool to make it more robust against loading settings from HDF5.
#     In a normal Bool, it cannot tolerate being assigned a value from a numpy.bool_
#     Here we get around this by giving the class its own from HDF5 method which casts loaded values to bool
#     before assignment."""
#
#     def toHDF5(self, hdf_parent_node, name='myBool'):
#         hdf_parent_node.attrs[name]=self.value #is a Bool accessable this way?
#
#     def fromHDF5(self, hdf):
#         self.value=hdf


class Prop(Atom):
    """The base class for all stored info about instruments and their properties."""

    name = Str()
    description = Str()
    experiment = Member()
    properties = Member()
    #GUI = Member()  # an optional enaml object that represents this class in the GUI, and has an update() method, to be run on eval
    doNotSendToHardware = Member()

    def __init__(self, name, experiment, description=''):
        self.experiment = experiment  # keep track of the experiment so we can get variables and such
        self.name = name  # name must be compatible with being a python variable name, and also an XML tag
        self.description = description  # English language description, including units and hints about possible values
        self.properties = ['description']  # things that are evaluated (if they define evaluate()) and saved to xml.  This is a list of the STRING of variable names (i.e. 'enable', not just: enable)
        self.doNotSendToHardware = ['description']

    def evaluate(self):
        """This function goes through the properties list and evaluates any of them with their own evaluate() method.
        This function should be overridden in subclasses at the lowest level on the Prop tree."""

        if self.experiment.allow_evaluation:
            #go through the properties list and evaluate
            for p in self.properties:
                try:
                    o = getattr(self, p)
                except:
                    #if the item isn't found
                    logger.warning('In Prop.evaluate for '+self.name+': Property '+p+' does not exist.')
                    continue
                if hasattr(o, 'evaluate'):  # check if it has an evaluate method.  If not, do nothing.
                    try:
                        o.evaluate()  # evaluate it
                    except PauseError:
                        raise PauseError
                    except Exception as e:
                        logger.warning('Evaluating '+p+' in '+self.name+'.properties.\n'+str(e)+str(traceback.format_exc())+'\n')
                        raise PauseError
            #if self.GUI is not None and hasattr(self.GUI, 'update'):
            #    self.GUI.update()

    def toHDF5(self, hdf_parent_node, name=None):
        """This function provides generic behavior to save a Prop as an HDF5 group.  The choice of group has been made
        because a Prop in general can have subproperties, and using a dataset would limit this behavior.  We go through
        the properties list.  If an item has its own toHDF5() method, that will be used.  If not, then we will try to
        save it as a dataset. This will only work if it is a type that h5py recognizes.  Else, it will be pickled using
        python's human readable pickling format. And saved to the HDF5 as a string dataset.  We assume that settings
        files will only ever be accessed as read-only and so variable length strings are not bothered with.  The node
        name is self.name, because nodes must have unique names (and so node type cannot be used as the name)."""

        if name is None:
            #if no name suggestion is given (usually used for ListProps) then use self.name
            name = self.name

        #create the group that represents this Prop
        try:
            my_node = hdf_parent_node.require_group(name)
        except TypeError:
            logger.warning('Incompatible object `{}` already exists in `{}`. Deleting the old object.'.format(name, hdf_parent_node.name))
            del hdf_parent_node[name]
            my_node = hdf_parent_node.create_group(name)

        #go through the list of properties:
        for p in self.properties:

            #convert the string name to an actual object
            try:
                o = getattr(self, p)
            except:
                logger.warning('In Prop.toHDF5() for class '+name+': item '+p+' in properties list does not exist.\n')
                continue

            #try to save it in various ways
            if hasattr(o, 'toHDF5'):
            #use toHDF5() of the object if available
                try:
                    o.toHDF5(my_node, p)
                except PauseError:
                    raise PauseError #pass it on quietly
                except Exception as e:
                    logger.warning('While trying '+p+'.toHDF5() in Prop.toHDF5() in '+name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
                    raise PauseError
            else:
                if p == 'version':
                    #save the version tag as an attribute
                    my_node.attrs['version'] = o
                else:
                    #try to save it as a dataset, then as an attribute.  If that fails, save its pickle
                    try:
                        #first try saving as a dataset
                        my_node[p] = o
                    except:
                        try:
                            #if that doesn't work, try saving as an attribute
                            my_node.attrs[p] = o
                        except:
                            #else just pickle it
                            try:
                                logger.debug("Preparing to pickle field name.property: `{}.{}`".format(name, p))
                                my_node[p]=pickle.dumps(o)
                            except RuntimeError:
                                logger.debug("Preparing to overwrite field name.property: `{}.{}`".format(name, p))
                                # we make it here if you try to overwrite an existing dataset
                                try:
                                    my_node[p][()] = pickle.dumps(o)
                                except MemoryError:
                                    logger.warning("Problem overwriting dataset: `{}.{}`. Deleting and inserting new dataset.".format(name, p))
                                    del my_node[p]
                                    my_node[p]=pickle.dumps(o)

                            except Exception as e:
                                logger.exception('While picking '+p+' in Prop.toHDF5() in')
                                raise PauseError
        return my_node

    def fromHDF5(self, hdf):
        '''This function provides generic HDF5 loading behavior for this package.
        First, version tags are checked.
        If an object exists and has its own fromHDF5 method, that will be used.  Else, we will attempt to load it as a python pickle.
        If this fails we load it as whatever type the HDF5 dataset is stored as.  (The later is preferable to the python pickle, but we must try the pickle first,
        to distinguish between pickles and raw strings.
        self is the object corresponding to the top level tag in the parameter hdf, and its children are what will be loaded here.'''

        #hdf node is guaranteed to have a name
        self.name = hdf.name.split('/')[-1]

        #check version
        if 'version' in hdf.attrs:
            if hasattr(self, 'version'):
                if hdf.attrs['version'] != self.version:
                    logger.info('Current '+self.name+' version is '+self.version+', you are loading from version: '+hdf.attrs['version'])
            else:
                logger.info('Code object '+self.name+' has no version, but HDF5 node has version: '+hdf.attrs['version'])
        elif hasattr(self, 'version'):
            logger.info('Code object '+self.name+' has version '+self.version+' but HDF5 node has no version tag.')

        #go through all attributes of hdf node and try to load them
        for i in hdf.attrs:
            if i != 'version':
                #check to see if this is one of the properties we care to load
                if i not in self.properties:
                    logger.info('Prop.fromHDF5(): HDF5 has attribute: '+i+', but this is not in the '+self.name+'.properties list.  It will not be loaded.\n')
                else:
                    #load in all other tags into variables
                    try:
                        #identify the variable to be loaded
                        var = getattr(self, i)
                        exists = True
                    except:
                        logger.info('in '+self.name+' in Prop.fromHDF5().  Will attempt to load attribute' + i +
                                       ' which was not previously defined in ' + self.name + '.\n')
                        exists = False
                    if exists and hasattr(var, 'fromHDF5'):
                        #set it using its own method
                        #this will preserve the instance identity
                        try:
                            var.fromHDF5(hdf.attrs[i])
                        except PauseError:
                            # a subclass has raised an error
                            # this is an error, but we will not pass it on, in order to finish loading
                            continue
                        except Exception as e:
                            logger.warning('While trying attribute'+i+'.fromHDF5() in Prop.fromHDF5() in '+self.name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
                            # this is an error, but we will not pass it on, in order to finish loading
                            continue
                    else:
                        try:
                            #try to unpickle it
                            x = pickle.loads(hdf.attrs[i])
                        except:
                            #if unpickling failed, just use the stored value
                            try:
                                x = hdf.attrs[i]
                                if exists:
                                    #mitigate the fact that atom cannot handle numpy bool and int types
                                    if type(var) == bool:
                                        x = bool(x)
                                    elif type(var) == int:
                                        x = int(x)
                            except:
                                logger.warning('Exception trying to load value for HDF5 attribute {} in {}.fromHDF5()'.format(i,self.name))
                                # this is an error, but we will not pass it on, in order to finish loading
                                continue
                        try:
                            # use the unpickled value
                            setattr(self, i, x)
                        except Exception as e:
                            logger.warning('in ' + self.name + ' in Prop.fromHDF5() while setting variable ' + i + ' in ' + self.name + '\n' + str(e) + '\n')
                            # this is an error, but we will not pass it on, in order to finish loading
                            continue

        #go through all names in hdf node (group) and try to load them
        for i in hdf:
            #check to see if this is one of the properties we care to load
            if i not in self.properties:
                logger.info('Prop.fromHDF5(): HDF5 has item: '+i+', but this is not in the '+self.name+'.properties list.  It will not be loaded.\n')
            else:
                #load in all other tags into variables
                try:
                    #identify the variable to be loaded
                    var = getattr(self, i)
                    exists = True
                except:
                    logger.info('in '+self.name+' in Prop.fromHDF5().  Will attempt to load '+i+' which was not previously defined in '+self.name+'.\n')
                    exists = False
                if exists and hasattr(var, 'fromHDF5'):
                    #set it using its own method
                    #this will preserve the instance identity
                    try:
                        var.fromHDF5(hdf[i])
                    except PauseError:
                        # a subclass has raised an error
                        # must be important so we will pass it on
                        raise PauseError
                    except Exception as e:
                        logger.warning('While trying '+i+'.fromHDF5() in Prop.fromHDF5() in '+self.name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
                        # this is an error, but we will not pass it on, in order to finish loading
                        continue
                else:
                    #check to see if it is stored as a dataset
                    if isinstance(hdf[i],h5py._hl.dataset.Dataset):
                        try:
                            #try to unpickle it
                            x = pickle.loads(hdf[i].value)
                        except:
                            #if unpickling failed, just use the stored value
                            try:
                                x = hdf[i].value
                                if exists:
                                    #mitigate the fact that atom cannot handle numpy bool and int types
                                    if type(var) == bool:
                                        x = bool(x)
                                    elif type(var) == int:
                                        x = int(x)
                            except:
                                logger.warning('Exception trying to load value for HDF5 node {} in {}.fromHDF5()'.format(i,self.name))
                                # this is an error, but we will not pass it on, in order to finish loading
                                continue
                        try:
                            setattr(self, i, x)
                        except Exception as e:
                            logger.warning('in '+self.name+' in Prop.fromHDF5() while setting variable '+i+' in '+self.name+'\n'+str(e)+'\n')
                            # this is an error, but we will not pass it on, in order to finish loading
                            continue
                    elif isinstance(hdf[i],h5py._hl.group.Group):
                        logger.warning('Cannot load HDF5 Group '+i+' without an fromHDF5() method in '+self.name)
                        # this is an error, but we will not pass it on, in order to finish loading
                        continue
                    else:
                        logger.warning('Cannot load HDF5 node {} which is of type {} in {}.fromHDF5()'.format(i,type(i),self.name))
                        # this is an error, but we will not pass it on, in order to finish loading
                        continue
        return self

    def toHardware(self):
        '''This function provides generic hardware communication XML for this package.  It is similar to toXML(self),
        but in the end it puts out str(value) of each property, which is useful to the hardware, and does not put out any of the
        function information that leads to those values.'''
        output=''

        #go through list of single properties:
        for p in self.properties: # I use a for loop instead of list comprehension so I can have more detailed error reporting.
            if p not in self.doNotSendToHardware:
                #convert the string name to an actual object
                try:
                    o=getattr(self,p)
                except:
                    logger.warning('In Prop.toHardware() for class '+self.name+': item '+p+' in properties list does not exist.\n')
                    raise PauseError

                output += self.HardwareProtocol(o, p)

        try:
            return '<{}>{}</{}>\n'.format(self.name, output, self.name)
        except Exception as e:
            logger.warning('While in format() in Prop.toHardware() in '+self.name+'.\n'+str(e)+'\n')
            raise PauseError

    def HardwareProtocol(self, o, name):
        '''A separate function with just the toHardware protocol, so we can reuse it independently of toXML(self)'''
        #if it has its own toHardware method, use it
        if hasattr(o,'toHardware'):
            try:
                return o.toHardware()
            except PauseError:
                raise PauseError
            except Exception as e:
                logger.warning('In Prop.HardwareProtocol() for class '+self.name+' while trying '+name+'.toHardware.\n'+str(e)+'\n')
                raise PauseError

        #else just give str(o)
        else:
            try:
                return '<{}>{}</{}>\n'.format(name, str(o), name)
            except Exception as e:
                logger.warning('In str('+name+') in Prop.HardwareProtocol() for '+self.name+'.\n'+str(e)+'\n')
                raise PauseError

    def call_evaluate(self, changed):
        """This function exists to allow Atom calls to evaluate() when something is changed.
        @observe passes the 'changed' parameter, whereas evaluate() takes no parameters."""
        if self.experiment.allow_evaluation:
            self.evaluate()

    def set_gui(self, d):
        """Takes in a dictionary (d) of things to set, where self.key is the parameter to set, and value is what it will
        be set to.  Makes a deferred call to set_dict so that this will happen in the gui thread"""
        if self.experiment.gui is not None:
            deferred_call(self.set_dict, d)
        else:
            self.set_dict(d)

    def set_dict(self, d):
        """Takes in a dictionary (d) of things to set, where self.key is the parameter to set, and value is what it will
        be set to.  Usually this is not called directly, but rather as a deferred call in set_gui
        so it is done in the GUI thread."""

        for key, value in d.iteritems():
            setattr(self, key, value)


class EvalProp(Prop):

    """The base class for any Prop that has a function, and can be evaluated to a value."""

    function = Str()
    valid = Bool(True)
    placeholder = Str()
    valueStr = Str()

    def __init__(self, name, experiment, description='', function=''):
        super(EvalProp, self).__init__(name, experiment, description)
        self.function = function
        self.properties += ['function']
        self.observe('function', self.call_evaluate)

    def evaluate(self):
        """This is the evaluation function that gets run programmatically during experiments and initialization.
        It will pause an experiment if an evaluation fails."""

        # We do not call super(EvalProp,self).evaluate() to evaluate things in the properties list,
        # because there is no need for an EvalProp to have subproperties at this time.

        if self.experiment.allow_evaluation:

            # Use experiment.vars, if available
            try:
                vars = self.experiment.vars
            except:
                logger.warning('EvalProp ' + self.name + ' has no experiment assigned in evaluate().')
                vars = {}

            # evaluate the 'function'
            try:
                value, valid = cs_evaluate.evalWithDict(self.function, varDict=vars)
            except Exception as e:
                logger.error('Error in EvalProp.evaluate() while evaluating property {}, {}, {}\n{}\n'.format(self.name, self.description, self.function, e))
                self.set_gui({'valid': False, 'valueStr': ''})
                raise PauseError
            if not valid:
                logger.error('Error in EvalProp.evaluate() while evaluating property {}, {}, {}\n'.format(self.name, self.description, self.function))
                self.set_gui({'valid': False, 'valueStr': ''})
                raise PauseError

            # store the result in self.value (we used to check for None here, but now allow it)
            try:
                self.value = value
                self.set_gui({'valueStr': str(value)})
            except TypeError as e:
                #this type of error is raised by Atom type checking
                logger.error('TypeError while evaluating:\nproperty: '+self.name+'\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e)+'\n')
                self.set_gui({'valid': False, 'valueStr': ''})
                raise PauseError
            except Exception as e:
                logger.error('Exception in EvalProp.evaluate() in '+self.name+'.\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e)+'\n')
                self.set_gui({'valid': False, 'valueStr': ''})
                raise PauseError

            #if we made it through all that, then the evaluation was okay
            self.set_gui({'valid': True})

    def toHardware(self):
        try:
            valueStr = str(self.value)
        except Exception as e:
            logger.warning('Exception in str(self.value) in EvalProp.toHardware() in '+self.name+' .\n'+str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name,valueStr,self.name)


class StrProp(EvalProp):
    value = Str()
    placeholder = 'string'


class IntProp(EvalProp):
    value = Int()
    placeholder = 'integer'


class RangeProp(EvalProp):
    '''This can't be instantiated directly.  Use IntRangeProp or FloatRangeProp.'''
    value=Value()
    low=Value()
    high=Value()
    placeholder=Str('')
    hasLow=Bool(False)
    hasHigh=Bool(False)

    def __init__(self,name,experiment,description='',function='',low=None,high=None):
        if low is not None:
            self.low=low
            self.hasLow=True
        if high is not None:
            self.high=high
            self.hasHigh=True
        super(RangeProp,self).__init__(name,experiment,description,function)

        self.observe('low', self.set_placeholder)
        self.observe('high', self.set_placeholder)
        self.set_placeholder({})
        self.evaluate()

    @observe('value')
    def value_changed(self,changed):
        if self.hasLow:
            if self.low > changed['value']:
                raise TypeError('Attempt to assign {} to {}RangeProp {} but the minimum value is {}'.format(changed['value'],self.numberType,self.name,self.low))
        if self.hasHigh:
            if changed['value'] > self.high:
                raise TypeError('Attempt to assign {} to {}RangeProp {} but the maximum value is {}'.format(changed['value'],self.numberType,self.name,self.high))

    @observe('low','high')
    def set_placeholder(self,changed):
        if self.hasLow:
            if self.hasHigh:
                self.placeholder='{} < {} < {}'.format(self.low,self.numberType,self.high)
            else:
                self.placeholder='{} < {}'.format(self.low,self.numberType,)
        elif self.hasHigh:
            self.placeholder='{} < {}'.format(self.numberType,self.high)
        else:
            self.placeholder='{}'.format(self.numberType)

class IntRangeProp(RangeProp):
    value = Int()
    low = Int()
    high = Int()
    numberType = 'Int'

class FloatRangeProp(RangeProp):
    value = Float()
    low = Float()
    high = Float()
    numberType = 'Float'

class FloatProp(EvalProp):
    value = Float()
    placeholder = 'float'

class BoolProp(EvalProp):
    value = Bool()
    placeholder = 'boolean'

class EnumProp(EvalProp):
    '''A homemade enum holder that allows us to set the possible values dynamically (unlike using a predefined Atom.Enum)'''
    value=Value()
    allowedValues=List()

    def __init__(self,name,experiment,description='',function='',allowedValues=None):
        super(EnumProp,self).__init__(name,experiment,description,function)
        if allowedValues is None:
            self.allowedValues=[]
        else:
            self.allowedValues=allowedValues
        self.evaluate()

    @observe('value')
    def value_changed(self,changed):
        if not (changed['value'] in self.allowedValues):
            raise TypeError('Attempt to assign {} to EnumProp {} but the only allowed values are: {}'.format(changed['value'],self.name,self.allowedValues))

    @observe('allowedValues')
    def set_placeholder(self,changed):
        self.placeholder = ','.join([str(i) for i in self.allowedValues])


class ListProp(Prop):
    """A ListProp is used to store a list of Props.  Unlike a normal list, they can be evaluated and saved properly as
    part of the tree."""

    listProperty = List()
    listElementType = Member()
    listElementName = Member()
    listElementKwargs = Member()
    gui = Member() #store a link to the enaml GUI so we can force it to refresh
    length = Int(0)
    names = List(Str())
    descriptions = List(Str())

    def __init__(self, name, experiment, description='', listProperty=None, listElementType=None,
                 listElementName='element', listElementKwargs=None):
        """
        :param name: A unique name for this Prop, used in saving.
        :param experiment: The main instance of Experiment that controls experiment flow.
        :param description: An explanation of what this is for.
        :param listProperty: A list that is used for initialization.  Otherwise a blank list is used.
        :param listElementType: The type that will be used when an element is appended.
        :param listElementName: What to call each new element, used in saving.
        :param listElementKwargs: A dictionary of keyword arguments to pass to __init__ of listElementType.
        :return:
        """

        super(ListProp, self).__init__(name, experiment, description)

        #we need the following if statement, because otherwise the listProperty of different instances of ListProp
        #are all set to point to the SAME default empty list []
        #default arguments are evaluated during definition, not during a call
        if listProperty is None:
            self.listProperty = []
        else:
            self.listProperty = listProperty
        self.listElementType = listElementType
        self.listElementName = listElementName
        if listElementKwargs is None:
            self.listElementKwargs = {}
        else:
            self.listElementKwargs = listElementKwargs
        self.refreshGUI()

    def refreshGUI(self):
        #update anything that uses the length variable, such as spin boxes
        self.length = len(self.listProperty)
        self.names = [i.name for i in self.listProperty]
        self.descriptions = [i.description for i in self.listProperty]

        #forcibly refresh the list
        if self.gui is not None:
            try:
                deferred_call(self.gui.refresh_items)
            except:
                logger.debug('ListProp call to refreshGUI when no GUI exists.')

    def __iter__(self):
        return iter(self.listProperty)

    def __len__(self):
        return len(self.listProperty)

    def __getitem__(self, i):
        return self.listProperty[i]

    def append(self, x):
        self.listProperty.append(x)
        self.refreshGUI()

    def pop(self, i):
        x = self.listProperty.pop(i)
        self.refreshGUI()
        return x

    def remove(self, x):
        self.listProperty.remove(x)
        self.refreshGUI()

    def copy(self, i):
        """Make a copy of element i of the list and append it to the end."""
        x = self.listProperty[i].copy()
        self.listProperty.append(x)
        self.refreshGUI()
        return x

    def getNextAvailableName(self):
        #figure out unique name for a new item
        count = len(self.listProperty) #start naming after current length, so this will go faster
        names = [i.name for i in self.listProperty]
        while True:
            name = self.listElementName+str(count)
            if not name in names:
                return name
            count += 1

    def add(self):
        new = self.listElementType(self.getNextAvailableName(), self.experiment, **self.listElementKwargs)
        self.listProperty.append(new)
        self.refreshGUI()
        return new

    def add_at(self, i):
        new = self.listElementType(self.getNextAvailableName(), self.experiment, **self.listElementKwargs)
        self.listProperty.insert(i, new)
        self.refreshGUI()
        return new

    def insert(self, i, x):
        self.listProperty.insert(i, x)
        self.refreshGUI()

    def index(self, x):
        return self.listProperty.index(x)

    def evaluate(self):
        if self.experiment.allow_evaluation:
            #go through the listProperty and evaluate each item
            for i,o in enumerate(self.listProperty):
                if hasattr(o, 'evaluate'):  # check if it has an evaluate method.  If not, do nothing.
                    try:
                        o.evaluate()  # evaluate it
                    except PauseError:
                        raise PauseError
                    except Exception as e:
                        logger.warning('Evaluating list item '+str(i)+' '+o.name+' in ListProp.evaluate() in '+self.name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
                        raise PauseError
        self.refreshGUI()

    def toHDF5(self, hdf, name=None):
        """ListProp has a special toHDF5 method because we do not save any of the normal properties for a listProp.
          It would be confusing to do so, as that is not what a ListProp is for."""

        list_node=hdf.require_group(self.name)

        #go through the listProperty and toHDF5 each item
        for i,o in enumerate(self.listProperty):

            try:
            #attempt to use given name
                name = o.name
                self.toHDF5item(list_node, name, o)
            except:
            #using the given name didn't work, try again with an iterative name
                try:
                    name = self.listElementName+str(i)
                    self.toHDF5item(list_node, name, o)
                except PauseError:
                    raise PauseError
                except Exception as e:
                    logger.warning('Uncaught exception on list item {} in ListProp.toHDF5item() in {}.\n{}\n{}\n'.format(i,self.name,str(e),str(traceback.format_exc())))
                    raise PauseError
        return list_node

    def toHDF5item(self, list_node, name, o):
        #try to save it in various ways
        if hasattr(o, 'toHDF5'):
        #use toHDF5() of the object if available
            try:
                o.toHDF5(list_node, name=name)
            except PauseError:
                raise PauseError
            except Exception as e:
                logger.warning('While trying toHDF5() on list item {} in ListProp.toHDF5() in {}.\n{}\n{}\n'.format(name, self.name, str(e), str(traceback.format_exc())))
                raise PauseError
        else:
        #try to save it as an attribute, then as a dataset.  If that fails, save its pickle
            try:
                #if it of a known well-behaved type, just go ahead and save to HDF5 attrs (more efficient than dataset)
                list_node.attrs[name] = o
            except:
                #if it is an array, saving to attrs will fail, but we can (and should) save it as a dataset
                try:
                    list_node[name] = o
                except:
                    #else just pickle it
                    try:
                        list_node[name] = pickle.dumps(o)
                    except Exception as e:
                        logger.exception('While picking list item {} in ListProp.toHDF5() in')
                        raise PauseError

    def fromHDF5(self, hdf):
        """ListProp has a special fromHDF5 method because we do not try to load any of the normal properties.  We only
        load things into the listProperty."""

        #do not call super

        #load the listProperty
        try:
            self.listProperty = [self.listElementType(i, self.experiment, **self.listElementKwargs).fromHDF5(hdf[i]) for i in hdf]
        except PauseError:
            raise PauseError
        except Exception as e:
            logger.warning('in {} in ListProp.fromHDF5() for hdf node {}\n{}\n{}\n'.format(self.name, hdf.name, e, traceback.format_exc()))
            raise PauseError
        self.refreshGUI()
        return self

    def toHardware(self):
        #go through the listProperty and toXML each item
        output = ''

        for i, o in enumerate(self.listProperty):
            #give the index number as the XML tag, this will only be used if the item does not have its own toHardware()
            output += self.HardwareProtocol(o, self.listElementName+str(i))

        return '<{}>{}</{}>\n'.format(self.name, output, self.name)


class Numpy1DProp(Prop):
    array = Member()
    dtype = Member()
    hdf_dtype = Member()
    zero = Member()

    def __init__(self, name, experiment, description='', dtype=float, hdf_dtype=float, zero=None):
        super(Numpy1DProp, self).__init__(name, experiment, description)
        self.dtype = dtype
        self.hdf_dtype = hdf_dtype
        self.zero = zero
        #create zero length array
        self.array = numpy.zeros(0, dtype=dtype)
        self.properties += ['array']

    def __len__(self):
        return len(self.array)

    def add(self, index):
        zero = numpy.zeros(1, dtype=self.dtype)
        if self.zero is not None:
            zero.fill(self.zero)
        self.array = numpy.insert(self.array, index, zero)

    def remove(self, index):
        self.array = numpy.delete(self.array, index)

    def toHDF5(self, hdf, name=None):
        try:
            hdf.create_dataset(self.name, data=self.array, dtype=self.hdf_dtype)#, compression="gzip", chunks=True)
        except Exception as e:
            logger.warning('While trying to create dataset in Numpy1DProp.toHDF5() in '+self.name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            raise PauseError

    def fromHDF5(self, hdf):
        try:
            self.array = hdf.value.astype(self.dtype)
        except Exception as e:
            logger.warning(' in Numpy1DProp.fromHDF5() in {} for hdf node {}\n{}\n{}\n'.format(self.name, hdf.name, e, traceback.format_exc()))
            raise PauseError


class Numpy2DProp(Prop):
    array = Member()
    dtype = Member()
    hdf_dtype = Member()
    zero = Member()

    def __init__(self, name, experiment, description='', dtype=float, hdf_dtype=float, zero=None):
        super(Numpy2DProp, self).__init__(name, experiment, description)
        self.dtype = dtype
        self.hdf_dtype = hdf_dtype
        self.zero = zero
        #create zero by zero size array
        self.array = numpy.zeros((0, 0), dtype=dtype)
        self.properties += ['array']

    def addRow(self, index):
        zero=numpy.zeros(self.array.shape[1], dtype=self.dtype)
        if self.zero is not None:
            zero.fill(self.zero)
        self.array=numpy.insert(self.array, index, zero, axis=0)

    def addColumn(self, index):
        zero=numpy.zeros(self.array.shape[0], dtype=self.dtype)
        if self.zero is not None:
            zero.fill(self.zero)
        self.array = numpy.insert(self.array, index, zero, axis=1)

    def removeRow(self, index):
        self.array = numpy.delete(self.array, index, axis=0)

    def removeColumn(self, index):
        self.array = numpy.delete(self.array, index, axis=1)

    def toHDF5(self, hdf, name=None):
        try:
            hdf.create_dataset(self.name, data=self.array, dtype=self.hdf_dtype)#, compression="gzip", chunks=True)
        except Exception as e:
            logger.warning('While trying to create dataset in Numpy2DProp.toHDF5() in '+self.name+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            raise PauseError

    def fromHDF5(self, hdf):
        self.array = hdf.value.astype(self.dtype)

    def toHardware(self):
        try:
            valueStr = '\n'.join([' '.join(map(str, i)) for i in self.array])
        except Exception as e:
            logger.warning('Exception in Numpy2DProp.toHardware() in '+self.name+' .\n'+str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name, valueStr, self.name)
