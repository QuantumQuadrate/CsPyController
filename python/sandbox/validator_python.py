import enaml
from enaml.qt.qt_application import QtApplication
from atom.api import Atom, Str
import threading

class TextHolder(Atom):
    text=Str()

def guiThread(myTextHolder):
    with enaml.imports():
        from validator_enaml import Main
    app = QtApplication()
    main=Main(textHolder=myTextHolder)
    main.show()
    app.start()

def new():
    myTextHolder=TextHolder()
    #start in a new thread so you can continue to use the shell
    threading.Thread(target=guiThread,args=[myTextHolder]).start()
    return myTextHolder

if __name__ == '__main__':
    myTextHolder=TextHolder()
    #start without creating a new thread
    guiThread(myTextHolder)
