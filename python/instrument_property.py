'''instrument_property.py
This file contains the mechanism for a property that describes some setting of an instrument.  A Prop can be saved and loaded.
A Prop can have properties of its own.
A Prop has extensions like EvalProp from a setting that takes some string input and is evaluated.
'''
from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

from atom.api import Atom, Str, Bool, Int, Float, List, Member, Value, observe
from enaml.validator import Validator

import pickle, traceback
import cs_evaluate

class Prop(Atom):
    '''The base class for all stored info about instruments and their properties.'''
    
    name=Str()
    description=Str()
    experiment=Member()
    properties=Member()
    doNotSendToHardware=Member()
    
    def __init__(self,name,experiment,description=''):
        self.experiment=experiment #keep track of the experiment so we can get variables and such
        self.name = name #name must be compatible with being a python variable name, and also an XML tag
        self.description=description #English language description, including units and hints about possible values
        self.properties=['description']  #things that are evaluated (if they define evaluate()) and saved to xml.  This is a list of the STRING of variable names (i.e. 'enable', not just: enable)
        self.doNotSendToHardware=[]
    
    def evaluate(self):
        #go through the properties list and evaluate
        for p in self.properties:
            try:
                o=getattr(self,p)
            except:
                #if the item isn't found
                logger.warning('In Prop.evaluate for '+self.name+': Property '+p+' does not exist.')
                continue
            if hasattr(o,'evaluate'): #check if it has an evaluate method.  If not, do nothing.
                try:
                    o.evaluate() #evaluate it
                except PauseError:
                    raise PauseError
                except Exception as e:
                    logger.warning('Evaluating '+p+' in '+self.name+'.properties.\n'+str(e)+str(traceback.format_exc())+'\n')
                    raise PauseError
    
    def toHDF5(self,hdf_parent_node):
        '''This function provides generic behavior to save a Prop as an HDF5 group.  The choice of group has been made because a Prop in
        general can have subproperties, and using a dataset would limit this behavior.
        We go through the properties list.  If an item has its own toHDF5 method, that will be used.
        Else, it will be pickled using python's human readable pickling format. And saved to the HDF5 as a string.
        We assume that settings files will only ever be accessed as read-only and so variable length strings are not bothered with.
        The node name is self.name, because nodes must have unique names, and so node types are not used.'''
        
        #create the group that represents this Prop
        my_node=hdf_parent_node.create_group(self.name)
        
        #go through the list of properties:
        for p in self.properties:
            
            #convert the string name to an actual object
            try:
                o=getattr(self,p)
            except:
                logger.warning('In Prop.toXML() for class '+self.name+': item '+p+' in properties list does not exist.\n')
                continue
            
            
            if hasattr(o,'toHDF5'):
            #use toHDF5() of the object if available
                try:
                    o.toHDF5(my_node)
                except Exception as e:
                    logger.warning('While trying '+p+'.toHDF5() in Prop.toHDF5() in '+self.name+'.\n'+str(e)+'\n')
                    raise PauseError
            else:
                #try to save it directly as a dataset.  If that fails, save its pickle
                try:
                    #if it of a known well-behaved type, just go ahead and save to HDF5 dataset
                    my_node[p]=o
                except:
                    #else just pickle it
                    try:
                        my_node[p]=pickle.dumps(o)
                    except Exception as e:
                        logger.warning('While picking '+p+' in Prop.toHDF5() in '+self.name+'.\n'+str(e)+'\n')
                        raise PauseError
    
    def fromHDF5(self,hdf):
        '''This function provides generic XML loading behavior for this package.
        First, version tags are checked.
        If an object has its own fromXML method, that will be used.  Else, it will be assumed that the XML is a pickle string, and
        it will be loaded using python's human-readable pickling format.
        self is the object corresponding to the top level tag in xmlNode, and its children are what will be loaded here.'''
        
        version=None
        
        #hdf node is guaranteed to have a name
        self.name=hdf.name
        
        #check version
        if 'version' in hdf:
            if hasattr(self,'version'):
                if hdf['version'].value!=self.version:
                    logger.warning('Current '+self.name+' version is '+self.version+', you are loading from version: '+hdf['version'].value)
            else:
                logger.warning('Code object '+self.name+' has no version, but HDF5 node has version: '+version)
        elif hasattr(self,'version'):
            logger.warning('Code object '+self.name+' has version '+self.version+' but HSDF5 node has no version tag.')
        
        for i in hdf:
            #check to see if this is one of the properties we care to load
            if i not in self.properties:
                logger.warning('Prop.fromHDF5(): HDF5 has item: '+i+', but this is not in the '+self.name+'.properties list.  It will not be loaded.\n')
            else:
                #load in all other tags into variables
                try:
                    #identify the variable to be loaded
                    var=getattr(self,i)
                    exists=True
                except:
                    logger.warning('in '+self.name+' in Prop.fromHDF5().  Will attempt to load '+i+' which was not previously defined in '+self.name+'.\n')
                    exists=False
                if exists:
                    if hasattr(var,'fromHDF5'):
                        #set it using its own method
                        #this will preserve the instance identity
                        var.fromHDF5(hdf[i])
                    else:
                        #check to see if it is stored as a dataset
                        if isInstance(h5py._hl.dataset.DataSet):
                            try:
                                #try to unpickle it
                                x=pickle.loads(hdf[i].value)
                            except:
                                #if unpickling failed, just use the stored value
                                try:
                                    x=hdf[i].value
                                except:
                                    logger.warning('Exception trying to load value for HDF5 node {} in {}.fromHDF5()'.format(i,self.name))
                            try:
                                setattr(self,i,x)
                            except Exception as e:
                                logger.warning('in '+self.name+' in Prop.fromHDF5() while unpickling existing variable '+i+' in '+self.name+'\n'+str(e)+'\n')
                        elif isInstance(h5py._hl.group.Group):
                            logger.warning('Cannot load HDF5 Group '+i+' without an fromHDF5() method in '+self.name)
                        else:
                            logger.warning('Cannot load HDF5 node {} which is of type {} in {}.fromHDF5()'.format(i,type(i),self.name))
                else:
                    #variable was not pre-existing
                    #assume it is a pickle, and write a new variable
                    #this will create a new instance identity
                    try:
                        setattr(self,i,pickle.loads(hdf[i].value))
                    except Exception as e:
                        logger.warning('in '+self.name+' prop.fromHDF5() while unpickling new variable '+i+' in '+self.name+'\n'+str(e)+'\n')
        
        return self
    
    def toXML(self):
        '''This function provides generic XML saving behavior for this package.
        It goes through the properties list. If an item has its own toXML method, that will be used.
        Else, it will be pickled using python's human-readable pickling format.'''
        output=''
        
        #go through list of single properties:
        for p in self.properties: # I use a for loop instead of list comprehension so I can have more detailed error reporting.
            
            #convert the string name to an actual object
            try:
                o=getattr(self,p)
            except:
                logger.warning('In Prop.toXML() for class '+self.name+': item '+p+' in properties list does not exist.\n')
                continue
            
            #defer to the separate function for the XML protocol
            output+=self.XMLProtocol(o,p)
            
        return '<{}>{}</{}>\n'.format(self.name,output,self.name)
    
    def XMLProtocol(self,o,name):
        '''A separate function with just the toXML protocol, so we can reuse it independently of toXML(self)'''
        #if it has its own toXML method, use it
        if hasattr(o,'toXML'):
            try:
                return o.toXML()
            except Exception as e:
                logger.warning('While trying '+name+'.toXML() in Prop.XMLProtocol() in '+self.name+'.\n'+str(e)+'\n')
                return ''
        
        #else just pickle it
        else:
            try:
                return '<{}>{}</{}>\n'.format(name,pickle.dumps(o),name)
            except Exception as e:
                logger.warning('While picking '+name+' in Prop.XMLProtocol() in '+self.name+'.\n'+str(e)+'\n')
                return ''

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
                    continue
                
                output+=self.HardwareProtocol(o,p)
        
        try:
            return '<{}>{}</{}>\n'.format(self.name,output,self.name)
        except Exception as e:
            logger.warning('While in format() in Prop.toHardware() in '+self.name+'.\n'+str(e)+'\n')
            return ''
    
    def HardwareProtocol(self,o,name):
        '''A separate function with just the toHardware protocol, so we can reuse it independently of toXML(self)'''
        #if it has its own toHardware method, use it
        if hasattr(o,'toHardware'):
            try:
                return o.toHardware()
            except Exception as e:
                logger.warning('In Prop.HardwareProtocol() for class '+self.name+' while trying '+name+'.toHardware.\n'+str(e)+'\n')
                return ''

        #else just give str(o)
        else:
            try:
                return '<{}>{}</{}>\n'.format(name,str(o),name)
            except Exception as e:
                logger.warning('In str('+name+') in Prop.HardwareProtocol() for '+self.name+'.\n'+str(e)+'\n')
                return ''
    
    def fromXML(self,xmlNode):
        '''This function provides generic XML loading behavior for this package.
        First, version tags are checked.
        If an object has its own fromXML method, that will be used.  Else, it will be assumed that the XML is a pickle string, and
        it will be loaded using python's human-readable pickling format.
        self is the object corresponding to the top level tag in xmlNode, and its children are what will be loaded here.'''
        
        version=None
        
        try:
            self.name=xmlNode.tag
        except Exception as e:
            logger.warning('Bad xml tag: '+xmlNode.tag+', in Prop.fromXML() in '+self.name+'.\n'+str(e))
        
        for child in xmlNode:
            
            #check to see if this is one of the properties we care to load
            if child.tag not in self.properties:
                logger.warning('Prop.fromXML(): XML has tag: '+child.tag+', but this is not in the '+self.name+'.properties list.  It will not be loaded.\n')
            else:            
                #check if the version tags match
                if child.tag=='version':
                    version=pickle.loads(child.text)
                    if hasattr(self,'version'):
                        if version!=self.version:
                            logger.warning('Current '+xmlNode.tag+' version is '+self.version+', you are loading from version: '+version)
                    else:
                        logger.warning('Code object '+self.name+' has no version, but XML node '+xmlNode.tag+' has version: '+version)
                
                #load in all other tags into variables
                else:
                    try:
                        #identify the variable to be loaded
                        var=getattr(self,child.tag)
                        exists=True
                    except:
                        logger.warning('in '+self.name+' in Prop.fromXML() while loading '+child.tag+' which was not previously defined in '+xmlNode.tag+'\n')
                        exists=False
                    if exists:
                        if hasattr(var,'fromXML'):
                            #set it using its own method
                            #this will preserve the instance identity
                            var.fromXML(child)
                        else:
                            #assume it is a pickle, and overwrite the existing variable
                            #this will overwrite the instance identity
                            try:
                                setattr(self,child.tag,pickle.loads(child.text))
                            except Exception as e:
                                logger.warning('in '+self.name+' in Prop.fromXML() while unpickling existing variable '+child.tag+' in '+xmlNode.tag+'\n'+str(e)+'\n')
                    else:
                        #variable was not pre-existing
                        #assume it is a pickle, and write a new variable
                        #this will create a new instance identity
                        try:
                            setattr(self,child.tag,pickle.loads(child.text))
                        except Exception as e:
                            logger.warning('in '+self.name+' prop.fromXML() while unpickling new variable '+child.tag+' in '+xmlNode.tag+'\n'+str(e)+'\n')
        
        #if we didn't see any version tag
        if (version is None) and hasattr(self,'version'):
            logger.warning('Code has version '+self.version+' but XML node '+xmlNode.tag+' has no version tag.')
        
        return self
    
    def call_evaluate(self,changed):
        '''This function exists to allow Atom calls to evaluate() when something is changed.  @observe passes the 'changed' parameter, whereas evaluate() takes no parameters'''
        self.evaluate()

# class EvalPropValidator(Validator):
    # valid=Bool()
    # def validate(self,text):
        # return self.valid

class EvalProp(Prop,Validator):

    '''The base class for any Prop that has a function, and can be evaluated to a value.'''
    
    function=Str()
    valid=Bool()
    placeholder=Str('')
    #validator=EvalPropValidator()
    #refresh=Bool()
    
    def __init__(self,name,experiment,description='',function=''):
        super(EvalProp,self).__init__(name,experiment,description)
        self.function=function
        self.properties+=['function']
        #self.valid=True
        #self.refresh=False #this value doesn't matter, we just toggle it update the Enaml field validation
        #start tracking function here, instead of with @observe, so that it doesn't update on initialization
        self.observe('function', self.call_evaluate)
    
    def evaluate(self):
        '''This is the evaluation function that gets run programmatically during experiments and initialization.  It will pause an experiment if an evaluation fails.'''
        self.valid=self.evalfunc(self.function)
        #self.validator.valid=self.valid
        #print 'evaluate: self.valid='+str(self.valid)
        #self.refreshGUI()
        #if the experiment is running then pause it
        if (not self.valid) and (self.experiment is not None) and (self.experiment.status!='idle'):
            raise PauseError
    
    #def refreshGUI(self):
    #    '''Signals the GUI to update whether or not a red error box is shown, based on self.valid'''
    #    self.refresh=not self.refresh
    
    def validate(self,text):
        '''This is the evaluation function that gets run on user GUI input.'''
        self.valid=self.evalfunc(text)
        return self.valid
    
    def evalfunc(self,function):
        #If necessary we could call super(EvalProp,self).evaluate() to evaluate things in the properties list.  But I don't think an evalProp will ever need to do that.
        
        #Use experiment.vars, if available
        try:
            vars=self.experiment.vars
        except:
            logger.warning('EvalProp '+self.name+' has no experiment assigned in evaluate().')
            vars={}
        
        #evaluate the 'function' and store it in 'value'
        try:
            value=cs_evaluate.evalWithDict(function,varDict=vars,errStr='evaluating property {}, {}, {}\n'.format(self.name,self.description,self.function))
            if value is not None:
               self.value=value
            else:
                #evaluation failed, error will already have been logged in cs_evaluate.evalWithDict
                return False
        except TypeError as e:
            #this type of error is raised by Atom type checking
            logger.warning('TypeError while evaluating:\nproperty: '+self.name+'\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e)+'\n')
            return False
        except Exception as e:
            logger.warning('Exception in EvalProp.evaluate() in '+self.name+'.\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e)+'\n')
            return False
        return True
    
    def toHardware(self):
        try:
            valueStr=str(self.value)
        except Exception as e:
            logger.warning('Exception in str(self.value) in EvalProp.toHardware() in '+self.name+' .\n'+str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name,valueStr,self.name)
    

class StrProp(EvalProp):
    value=Str()
    placeholder='string'

class IntProp(EvalProp):
    value=Int()
    placeholder='integer'
    
    def toHDF5(self,hdf):
        

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
    value=Int()
    low=Int()
    high=Int()
    numberType='Int'

class FloatRangeProp(RangeProp):
    value=Float()
    low=Float()
    high=Float()
    numberType='Float'

class FloatProp(EvalProp):
    value=Float()
    placeholder='float'

class BoolProp(EvalProp):
    value=Bool()
    placeholder='boolean'

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
        self.placeholder=','.join([str(i) for i in self.allowedValues])

class ListProp(Prop):
    listProperty=List()
    listElementType=Member()
    listElementName=Member()
    listElementKwargs=Member()
    
    def __init__(self,name,experiment,description='',listProperty=None,
                    listElementType=None,listElementName='element',listElementKwargs={}):
        super(ListProp,self).__init__(name,experiment,description)
        
        #we need the following if statement, because otherwise the listProperty of different instances of ListProp
        #are all set to point to the SAME default empty list []
        #default arguments are evaluated during definition, not during a call
        if listProperty is None:
            self.listProperty=[]
        else:
            self.listProperty=listProperty
        self.listElementType=listElementType
        self.listElementName=listElementName
        self.listElementKwargs=listElementKwargs
    
    def __iter__(self): 
        return iter(self.listProperty)
    
    def __len__(self):
        return len(self.listProperty)
    
    def __getitem__(self, i):
        return self.listProperty[i]
    
    def append(self,x):
        self.listProperty.append(x)
    
    def pop(self,i):
        self.listProperty.pop(i)
    
    def remove(self,x):
        self.listProperty.remove(x)
    
    def add(self):
        new=self.listElementType(self.listElementName,self.experiment,**self.listElementKwargs)
        self.listProperty.append(new)
        return new
    
    def index(self,x):
        return self.listProperty.index(x)
    
    def evaluate(self):
        
        #go through the listProperty and evaluate each item
        for i,o in enumerate(self.listProperty):
            if hasattr(o,'evaluate'): #check if it has an evaluate method.  If not, do nothing.
                try:
                    o.evaluate() #evaluate it
                except Exception as e:
                    logger.warning('Evaluating list item '+str(i)+' '+o.name+' in ListProp.evaluate() in '+self.name+'.\n'+str(e))
                    raise PauseError
    
    def toXML(self):
        #go through the listProperty and toXML each item
        output=''
        
        for i,o in enumerate(self.listProperty):
            try:
                output+=self.XMLProtocol(o,self.listElementName) #give the index number as the XML tag, this will only be used if the item does not have its own toXML()
            except PauseError:
                raise PauseError
            except Exception as e:
                logger.warning('Evaluating list item '+str(i)+' in ListProp.evaluate() in'+self.name+'.\n'+str(e))
        
        return '<{}>{}</{}>\n'.format(self.name,output,self.name)
    
    def toHardware(self):
        #go through the listProperty and toXML each item
        output=''
        
        for i,o in enumerate(self.listProperty):
            output+=self.HardwareProtocol(o,self.listElementName) #give the index number as the XML tag, this will only be used if the item does not have its own toHardware()
        
        return '<{}>{}</{}>\n'.format(self.name,output,self.name)
    
    def fromXML(self,xmlNode):
        # in a listProp XML all the elements are part of self.listProperty
        # you may need to override this in a subclass if listElementType.__init__ takes in other things besides name and experiment
        try:
            #so we don't lose our list identity
            #while self.listProperty: #go until the list is empty
            #    self.listProperty.pop()
            self.listProperty=[self.listElementType(self.listElementName,self.experiment,**self.listElementKwargs).fromXML(child) for i, child in enumerate(xmlNode)]
        except Exception as e:
            logger.warning('in '+self.name+' in ListProp.fromXML() for xml tag: '+xmlNode.tag+'.\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
        return self
