from atom.api import Atom, Enum, Typed, observe, Str, List, Value, Int

class EnumHolder(Atom):
    value=Value()
    allowedValues=List()
    
    def __init__(self,allowedValues,default):
        self.allowedValues=allowedValues
        self.value=default
    
    @observe('value')
    def value_changed(self,changed):
        if not (changed['value'] in self.allowedValues):
            raise TypeError('Attempt to assign {} but the only allowed values are: {}'.format(changed['value'],self.allowedValues))

            
class observerTest(Atom):
    value=Int()
    
    def __init__(self,default):
        self.value=default
    
    @observe('value')
    def valueChanged(self,changed):
        print 'You tried to change the value of value to {} but right now it is {}'.format(changed['value'],self.value)