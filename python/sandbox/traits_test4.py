from traits.api import HasTraits, Instance, Float

class c1(HasTraits):
    f=Float(5)
    
    _on_trait_changed(self):
        parent.changed
    
class c2(HasTraits):
    i=Instance(c1)
    
    def _i_changed(self,old,new):
        print "changed!"