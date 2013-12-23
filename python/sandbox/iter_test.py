from collections import Iterable
from enthought.traits.api import HasTraits, Instance

class c(HasTraits):
    def __init__(self):
        self.data=[1,2,3]

    def __iter__(self):
        return data

class d(c):
    def __init__(self):
        super(d,self).__init__()

class otherGuy(HasTraits):
    myGuy=Instance(Iterable)
    
    def __init__(self):
        myGuy=d()

        if isinstance(myGuy, Iterable):
            print 'yes'
        else:
            print 'no'
            
a=otherGuy()