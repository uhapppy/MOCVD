import os
import sys
import numpy as np
import csv
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog

from essential.layer import get_layer_nk_file
from essential.script import convert_from_abc


class ResultMATTabSimulation(QtWidgets.QWidget):
    def __init__(self,layer,thickness,wavelength, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ResultMATTabSimulation.ui'), self)
        self.export_button.clicked.connect(self.export_index)
        self.unit_combobox.currentIndexChanged.connect(self.update_ui)
        self.layer = layer
        self.thickness = thickness

        self.wavelength = np.array(wavelength)
        self.energy = 1239.84187 / self.wavelength



        self.n , self.k = get_layer_nk_file(self.layer.nk_file,self.wavelength)
        self.initiate()
        self.update_ui()



    def initiate(self):
        for i in range(0, len(self.wavelength)):
            self.index_table.insertRow(i)

        if self.layer.first_or_last == True:
            self.thickness_output.setEnabled(False)

        self.thickness_output.setValue(self.thickness)
        self.thickness_output.valueChanged.connect(self.update_ui)



    def table_index(self):
        for i in range(0, len(self.wavelength)):
            if self.unit_combobox.currentIndex() == 0:

                self.index_table.setHorizontalHeaderLabels(["Wavelength (nm)", "n", "k"])
                self.index_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.wavelength[i])))
            elif self.unit_combobox.currentIndex() == 1:

                self.index_table.setHorizontalHeaderLabels(["Energy (eV)", "n", "k"])
                self.index_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.energy[i])))

            self.index_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.n[i])))
            self.index_table.setItem(i, 2, QtWidgets.QTableWidgetItem("{:.6f}".format(self.k[i])))


    def graph(self):
        self.graph_nk = pg.PlotWidget()
        styles = {'color': 'k', 'font-size': '20px'}

        pen_n = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DashLine)
        pen_k = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DotLine)

        if self.unit_combobox.currentIndex() == 0:
            self.graph_nk.plot(self.wavelength, self.n, pen=pen_n)
            self.graph_nk.plot(self.wavelength, self.k, pen=pen_k)
            self.graph_nk.setLabel('bottom', 'Wavelength', units='m', **styles)
            self.graph_nk.getAxis('bottom').setScale(1e-9)

        elif self.unit_combobox.currentIndex() == 1:
            self.graph_nk.plot(self.energy, self.n, pen=pen_n)
            self.graph_nk.plot(self.energy, self.k, pen=pen_k)
            self.graph_nk.setLabel('bottom', 'Energy', units='eV', **styles)



        n_legend = pg.PlotDataItem(pen=pen_n)
        k_legend = pg.PlotDataItem(pen=pen_k)
        legend = pg.LegendItem(pen="k")
        legend.addItem(n_legend, 'n')
        legend.addItem(k_legend, 'k')
        legend.setParentItem(self.graph_nk.graphicsItem())

        self.graph_nk.showGrid(x=True, y=True)
        self.graph_nk.setBackground('w')
        self.graph_nk.setTitle("Index graph", color="k", size="20pt")
        self.graph_nk.setLabel('left', 'Index', units='a.u.', **styles)

        self.graph_layout.addWidget(self.graph_nk)

    def update_ui(self):
        for i in reversed(range(self.graph_layout.count())):
            self.graph_layout.itemAt(i).widget().setParent(None)

        self.thickness = self.thickness_output.value()
        self.table_index()
        self.graph()

    def export_index(self):
        name, _ = QFileDialog.getSaveFileName()
        if name == "":
            return

        file = open(name, 'w')
        if self.unit_combobox.currentIndex() == 0:
            file.write(f"Wavelength (nm)  n  k  \n")
            file.write("nm\n")
            file.write("nk\n")
            for i in range(0, len(self.wavelength)):
                file.write(f"{self.wavelength[i]}  {self.n[i]}  {self.k[i]} \n")
        elif self.unit_combobox.currentIndex() == 1:
            file.write(f"Energy (eV)  n  k  \n")
            file.write("eV\n")
            file.write("nk\n")
            for i in range(0, len(self.energy)):
                file.write(f"{self.energy[i]}  {self.n[i]}  {self.k[i]} \n")



        file.close()