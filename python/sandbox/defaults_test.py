import time

def myFunc(a=time.time()):
    return a

class myClass(object):
    def __init__(self,a=time.time()):
       self.a=a

call1=time.time()
time.sleep(.1)
call2=time.time()
time.sleep(.1)
print call1, call2
print 'Function calls are the same every time:',call1==call2
       
result1=myFunc()
time.sleep(.1)
result2=myFunc()
time.sleep(.1)
print result1, result2
print 'Python module methods do not process default arguments every time:',result1==result2
       
instance1=myClass()
time.sleep(.1)
instance2=myClass()
time.sleep(.1)
print instance1.a, instance2.a
print 'Python class methods do not process default arguments every time:',instance1.a==instance2.a
