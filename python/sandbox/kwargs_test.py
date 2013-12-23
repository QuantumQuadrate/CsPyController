class c(object):
    def __init__(self,name,kwargs):
        print name
        print kwargs['AO']
        
a={'BO':6,'AO':5}
c('fred',a)