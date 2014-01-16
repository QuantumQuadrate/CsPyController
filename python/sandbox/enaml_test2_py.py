import enaml
from enaml.qt.qt_application import QtApplication
import threading
from atom.api import Atom, Str, observe, Typed
from enaml.validator import Validator

class myValidator(Validator):
    
    def validate(self,text):
        if text=='bad':
            return False
        elif text=='error':
            try:
                raise Exception
            except:
                return False
            return False
        return True

class prop(Atom):
    function=Str()
    value=Str()
    validator=myValidator()
    
    @observe('function')
    def evaluate(self,changed):
        print '_observed_function called'
        self.value=self.function+'hihi'

def guiThread(myProp):
    with enaml.imports():
        from enaml_test2 import Main
    
    app = QtApplication()
    
    view = Main(myProp=myProp)
    view.show()
    app.start()

def new():

    myProp=prop()
    
    threading.Thread(target=guiThread,args=[myProp]).start()
    return myProp

if __name__ == '__main__':
    myProp=prop()
    guiThread(myProp)
