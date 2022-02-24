import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic

form_class = uic.loadUiType("main_window.ui")[0]

class MyWindow(QDialog, form_class):
    def __init__(self):
        super().__init__()
        self.setUI()
        
    def setUI(self):
        self.setupUi(self)

        
# class MyWindow(QMainWindow, form_class): // Qt Designer form template에 따라 상속 class도 달라짐 체크
#     def __init__(self):
#         super().__init__()
#         self.setUI()
        
#     def setUI(self):
#         self.setupUi(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()