import sys

from gmui.app import App
from gmui.window import Window

app = App(sys.argv)
main_window = Window()
main_window.show()
app.exec()
