# main.py
import enaml
from enaml.qt.qt_application import QtApplication

from person_model import Person

import threading

def guiThread(john):
    with enaml.imports():
        from person_view import PersonView
    
    app = QtApplication()
    
    view = PersonView(person=john)
    view.show()
    app.start()

def new():

    john = Person(first_name='John', last_name='Doe')
    
    threading.Thread(target=guiThread,args=[john]).start()
    return john

if __name__ == '__main__':
    new()