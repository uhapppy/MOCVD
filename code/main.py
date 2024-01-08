import os
import sys
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtGui import QFont, QFontDatabase
from tabs.data_tab import DataTab
from tabs.analysis.analyse_tab import AnalysisTab
from tabs.mat.mat_tab import MatTab


np.seterr(divide = 'ignore')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'MainWindow.ui'), self)

        self.data_tab = DataTab()
        self.analysis_tab = AnalysisTab()
        self.mat_tab = MatTab()


        child_widgets = self.data_tab.findChildren(QtWidgets.QLineEdit)
        for child_widget in child_widgets:
            child_widget.textChanged.connect(self.unlock_analysis_tab)

        self.main_tab_holder.addTab(self.data_tab, "Data Setup")
        self.main_tab_holder.addTab(self.analysis_tab, "Data Analysis Tool")
        self.main_tab_holder.addTab(self.mat_tab, "Mat file Analysis Tool")
        self.main_tab_holder.currentChanged.connect(self.tabs_update)




        self.unlock_analysis_tab()
        self.resize(560, 365)






    def unlock_analysis_tab(self):
        result = self.data_tab.check_if_can_send()
        if result:
            self.main_tab_holder.setTabEnabled(1, True)
        else:
            self.main_tab_holder.setTabEnabled(1, False)


    def tabs_update(self, index):
        if index == 0:
            self.resize(560, 365)
        if index == 1:
            self.analysis_tab.file_data = self.data_tab.send_data()
            self.analysis_tab.update_tab(self.data_tab.mat_folder.text())
            self.resize(1470, 1100)
        if index == 2:
            self.resize(1470, 1100)
        if index == 3:
            self.simulation_tab.update_tab(self.data_tab.mat_folder.text())
            self.resize(1470, 1100)


if __name__ == "__main__":

    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        print("ok_1")
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        print("ok_2")
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)


    app.setStyle("fusion")

    window = MainWindow()
    window.show()
    app.exec()
