from atom.api import Atom, Str, Bool, Int, Float, List, Member

from enaml.validator import Validator
import logging, pickle, traceback
logger = logging.getLogger(__name__)
import cs_evaluate
from cs_errors import PauseError
import time

class Prop(Atom):
    '''The base class for all stored info about instruments and their properties.'''
    
    name=Str()
    description=Str()
    experiment=Member()
    properties=Member()
    
    def __init__(self,name,experiment,description=''):
        self.experiment=experiment #keep track of the experiment so we can get variables and such
        self.name = name #name must be compatible with being a python variable name, and also an XML tag
        self.description=description #English language description, including units and hints about possible values
        self.properties=['description']  #things that are evaluated (if they define evaluate()) and saved to xml.  This is a list of the STRING of variable names (i.e. 'enable', not just: enable)
    
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
                    logger.warning('Evaluating '+p+' in '+self.name+'.properties.\n'+str(e)+str(traceback.print_exc())+'\n')
                    raise PauseError
    
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
        '''This function provides generic hardware communiation XML for this package.  It is similar to toXML(self),
        but in the end it puts out str(value) of each property, which is useful to the hardware, and does not put out any of the
        function information that leads to those values.'''
        output=''
        
        #go through list of single properties:
        for p in self.properties: # I use a for loop instead of list comprehension so I can have more detailed error reporting.
            
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
            logger.warning('While in format() in Prop.XMLProtocol() in '+self.name+'.\n'+str(e)+'\n')
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

class EvalProp(Prop): #,Validator):
    '''The base class for any Prop that has a function, and can be evaluated to a value.'''
    
    function=Str()
    valid=Bool(True)
    refresh=Bool()
    
    def __init__(self,name,experiment,description='',function=''):
        super(EvalProp,self).__init__(name,experiment,description)
        self.function=function
        self.properties+=['function']
        self.valid=True
        self.refresh=False #this value doesn't matter, we just toggle it update the Enaml field validation
    
    def setGUI(self,GUI):
        self.GUI=GUI
    
    def evaluate(self):
        #If necessary we could call super(EvalProp,self).evaluate() to evaluate things in the properties list.  But I don't think an evalProp will ever need to do that.
        
        #Use experiment.vars, if available
        try:
            vars=self.experiment.vars
        except:
            logger.warning('EvalProp '+self.name+' has no experiment assigned in evaluate().')
            vars={}
        
        #evaluate the 'function' and store it in 'value'
        try:
            self.value=cs_evaluate.evalWithDict(self.function,varDict=vars,errStr='evaluating property {}, {}, {}\n'.format(self.name,self.description,self.function))
            self.valid=True
            self.refresh= not self.refresh
        except TypeError as e:
            #self.value=None
            
            self.valid=False
            self.refresh= not self.refresh
            #logger.warning('TraitError while evaluating property: '+self.name+'\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e))
            #raise PauseError
        except Exception as e:
            logger.warning('Exception in EvalProp.evaluate() in '+self.name+'.\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e)+'\n')
            raise PauseError
        
    def validate(self,text,component):
        #implement this for validation on enaml fields
        #self.function=text
        #self.evaluate()
        return text, self.valid
    
    def toHardware(self):
        try:
            valueStr=str(self.value)
        except Exception as e:
            logger.warning('Exception in str(self.value) in EvalProp.toHardware() in '+self.name+' .\n'+str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name,valueStr,self.name)
    
    def _function_changed(self,val):
        self.evaluate()
    
class StrProp(EvalProp):
    value=Str()

class IntProp(EvalProp):
    value=Int()

class FloatProp(EvalProp):
    value=Float()

class BoolProp(EvalProp):
    value=Bool()

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
        new=self.listElementType(self.listElementName+str(len(self.listProperty)),self.experiment,'',self.listElementKwargs)
        self.listProperty.append(new)
        return new
    
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
                output+=self.XMLProtocol(o,self.listElementName+str(i)) #give the index number as the XML tag, this will only be used if the item does not have its own toXML()
            except PauseError:
                raise PauseError
            except Exception as e:
                logger.warning('Evaluating list item '+str(i)+' in ListProp.evaluate() in'+self.name+'.\n'+str(e))
        
        return '<{}>{}</{}>\n'.format(self.name,output,self.name)
    
    def toHardware(self):
        #go through the listProperty and toXML each item
        output=''
        
        for i,o in enumerate(self.listProperty):
            output+=self.HardwareProtocol(o,self.listElementName+str(i)) #give the index number as the XML tag, this will only be used if the item does not have its own toHardware()
        
        return '<{}>{}</{}>\n'.format(self.name,output,self.name)
    
    def fromXML(self,xmlNode):
        # in a listProp XML all the elements are part of self.listProperty
        # you may need to override this in a subclass if listElementType.__init__ takes in other things besides name and experiment
        try:
            #so we don't lose our list identity
            while self.listProperty: #go until the list is empty
                self.listProperty.pop()
            self.listProperty+=[self.listElementType(str(i),self.experiment,description='',kwargs=self.listElementKwargs).fromXML(child) for i, child in enumerate(xmlNode)]
        except Exception as e:
            logger.warning('in '+self.name+' in ListProp.fromXML() for xml tag: '+xmlNode.tag+'.\n'+str(e)+'\n'+str(traceback.print_exc())+'\n')
        return self
