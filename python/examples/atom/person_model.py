# person_model.py
from atom.api import Atom, Unicode

class Person(Atom):
    first_name = Unicode()
    last_name = Unicode()
    
    def __init__(self,*args,**kwargs):
        super(Person,self).__init__(*args,**kwargs)
        self.var1=5