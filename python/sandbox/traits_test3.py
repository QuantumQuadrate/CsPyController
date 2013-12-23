from enthought.traits.api import HasTraits, Str

class myclass(HasTraits):
    a=Str

c=myclass()
c.a='hi'
print c.a
c.a=5
print c.a