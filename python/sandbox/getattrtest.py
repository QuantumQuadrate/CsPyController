class parent(object):
     def func(self):
         print "parent func"

class child(parent):
     def func2(self):
        print "child func2"

myinst=child()
print hasattr(child,'func2')
print hasattr(child,'func')