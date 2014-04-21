import time, threading
import enaml
from enaml.qt.qt_application import QtApplication
#from MVC_Model import Model
from atom.api import Atom, observe, Typed, ForwardTyped, Member


class Model(Atom):
    text = Member()

    def __init__(self):
        self.text = 'hi'
        threading.Thread(target=self.go).start()

    def go(self):
        for i in xrange(10):
            self.text = str(i)
            time.sleep(1)


class Controller(Atom):

    model = Member()
    view = Member()

    def __init__(self,model=None,view=None):
        self.model=model
        self.view=view

    @observe('model.text')
    def rewrite(self, change):
        self.view.text = self.model.text

if __name__ == '__main__':
    model = Model()
    with enaml.imports():
        from MVC_View import View
    app = QtApplication()
    view = View()
    controller = Controller(model=model, view=view)
    view.show()
    app.start()
