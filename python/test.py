

import enaml
from enaml.qt.qt_application import QtApplication

if __name__=='__main__':
    with enaml.imports():
        from test_enaml import Mainone
    app = QtApplication()
    main = Mainone()
    main.show()
    main.activate_window()
    main.send_to_front()
    app.start()