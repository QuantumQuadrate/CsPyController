import numpy

class c():
    def __init__(self):
        self.a = 2
        self.f2 = numpy.vectorize(self.f1)


    def f1(self, x):
        return x + self.a


    def f3(self, x):
        return self.f2(x)+2

d=c()
e=d.f3(numpy.arange(10))
print e