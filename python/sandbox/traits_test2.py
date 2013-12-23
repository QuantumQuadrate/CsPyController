from traits.api import HasTraits, Str, Instance

class Prop(HasTraits):
    txt=Str('hi')
    def __init__(self,text):
        super(Prop,self).__init__()
        self.txt=text

class myClass(HasTraits):
    str1=Str
    a=Instance(Prop)
    #a=Prop('hiya')
    
    def __init__(self,text):
        super(myClass,self).__init__()
        self.a=Prop(text)
        self.str1='str1 text'
        
b=myClass('hey')
print b.a.txt
print b.editable_traits()
b.print_traits()
