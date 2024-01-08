import os
import sys
import numpy as np
import csv
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog

from essential.layer import get_layer_nk_fb
from essential.script import convert_from_abc, convert_to_abc


class ResultFBTabAnalysis(QtWidgets.QWidget):
    def __init__(self, layer, partial_solution, wavelength, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ResultFBTabAnalysis.ui'), self)

        self.export_spread_button.clicked.connect(self.save_solution_spread)

        self.export_index_button.clicked.connect(self.save_index)

        self.unit_combobox.currentIndexChanged.connect(self.update_ui)
        self.include_n_check.stateChanged.connect(self.update_ui)
        self.include_k_check.stateChanged.connect(self.update_ui)

        self.parameters_type_combobox.currentIndexChanged.connect(self.table_solution)

        self.layer = layer
        self.partial_solution = partial_solution

        self.thickness = None
        self.n_infinity = None
        self.band_gap = None

        self.centers = np.array([])
        self.widths = np.array([])
        self.areas = np.array([])

        self.a = np.array([])
        self.b = np.array([])
        self.c = np.array([])

        self.wavelength = np.array(wavelength)
        self.energy = 1239.84187 / self.wavelength

        self.n = None
        self.k = None

        self.initiate()
        self.update_ui()

    def initiate(self):
        if self.layer.first_or_last == True:
            self.partial_solution.insert(0, 9999.999999)

        self.thickness = self.partial_solution[0]
        self.n_infinity = self.partial_solution[1]
        self.band_gap = self.partial_solution[2]

        self.centers = np.array(self.partial_solution[3::3])
        self.widths = np.array(self.partial_solution[4::3])
        self.areas = np.array(self.partial_solution[5::3])

        self.a, self.b, self.c = convert_to_abc(self.centers, self.widths, self.areas,self.band_gap)

        self.thickness_output.setValue(self.thickness)
        self.n_inf_output.setValue(self.n_infinity)
        self.eg_output.setValue(self.band_gap)

        for i in range(0, len(self.wavelength)):
            self.index_table.insertRow(i)

        for i in range(0, self.layer.fb_term):
            self.solution_table.insertRow(i)
            button = QtWidgets.QCheckBox()
            button.setChecked(True)
            button.stateChanged.connect(self.update_ui)
            self.solution_table.setCellWidget(i, 0, button)

        self.table_solution()

        # self.solution_table.itemChanged.connect(self.update_ui)

        self.n_inf_output.valueChanged.connect(self.update_ui)
        self.eg_output.valueChanged.connect(self.update_ui)
        self.thickness_output.valueChanged.connect(self.update_ui)

    def get_peaks(self):

        self.n_infinity = self.n_inf_output.value()
        self.band_gap = self.eg_output.value()
        self.thickness = self.thickness_output.value()

        self.centers = np.array([])
        self.widths = np.array([])
        self.areas = np.array([])

        self.a = np.array([])
        self.b = np.array([])
        self.c = np.array([])

        if self.parameters_type_combobox.currentIndex() == 0:
            for i in range(0, self.solution_table.rowCount()):
                self.centers = np.append(self.centers, float(self.solution_table.item(i, 1).text()))
                self.widths = np.append(self.widths, float(self.solution_table.item(i, 2).text()))
                self.areas = np.append(self.areas, float(self.solution_table.item(i, 3).text()))

            self.a, self.b, self.c = convert_to_abc(self.centers, self.widths, self.areas,self.band_gap)

        elif self.parameters_type_combobox.currentIndex() == 1:
            for i in range(0, self.solution_table.rowCount()):
                self.a = np.append(self.a, float(self.solution_table.item(i, 1).text()))
                self.b = np.append(self.b, float(self.solution_table.item(i, 2).text()))
                self.c = np.append(self.c, float(self.solution_table.item(i, 3).text()))

            self.centers, self.widths, self.areas = convert_from_abc(self.a, self.b, self.c,self.band_gap)

    def get_nk(self):

        centers = np.array([])
        widths = np.array([])
        areas = np.array([])
        for i in range(0, self.solution_table.rowCount()):
            if self.solution_table.cellWidget(i, 0).isChecked() == True:
                centers = np.append(centers, self.centers[i])
                widths = np.append(widths, self.widths[i])
                areas = np.append(areas, self.areas[i])

        self.n, self.k = get_layer_nk_fb(len(centers), self.wavelength, centers, widths, areas,
                                         self.band_gap, self.n_infinity)
        # self.n, self.k = get_layer_nk_fb(self.layer.fb_term, self.wavelength, self.centers, self.widths, self.areas,
        #                                  self.band_gap, self.n_infinity)

    def table_index(self):
        try:
            self.index_table.itemChanged.disconnect()
        except:
            pass
        for i in range(0, len(self.wavelength)):
            if self.unit_combobox.currentIndex() == 0:

                self.index_table.setHorizontalHeaderLabels(["Wavelength (nm)", "n", "k"])
                self.index_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.wavelength[i])))
            elif self.unit_combobox.currentIndex() == 1:

                self.index_table.setHorizontalHeaderLabels(["Energy (eV)", "n", "k"])
                self.index_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.energy[i])))

            self.index_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.n[i])))
            self.index_table.setItem(i, 2, QtWidgets.QTableWidgetItem("{:.6f}".format(self.k[i])))
        self.index_table.itemChanged.connect(self.update_ui)

    def table_solution(self):
        try:
            self.solution_table.itemChanged.disconnect()
        except:
            pass

        for i in range(0, self.layer.fb_term):
            if self.parameters_type_combobox.currentIndex() == 0:
                self.solution_table.setHorizontalHeaderLabels(["Include", "Center (eV)", "Width (eV)", "Area (1/eV)"])
                self.solution_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.centers[i])))
                self.solution_table.setItem(i, 2, QtWidgets.QTableWidgetItem("{:.6f}".format(self.widths[i])))
                self.solution_table.setItem(i, 3, QtWidgets.QTableWidgetItem("{:.6f}".format(self.areas[i])))
            elif self.parameters_type_combobox.currentIndex() == 1:
                self.solution_table.setHorizontalHeaderLabels(["Include", "A", "B (eV)", "C (eV^2)"])
                self.solution_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.a[i])))
                self.solution_table.setItem(i, 2, QtWidgets.QTableWidgetItem("{:.6f}".format(self.b[i])))
                self.solution_table.setItem(i, 3, QtWidgets.QTableWidgetItem("{:.6f}".format(self.c[i])))

        # header = self.solution_table.horizontalHeader()
        # header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.solution_table.itemChanged.connect(self.update_ui)

    def nk_peak_sum(self):
        self.graph_nk_peak_sum = pg.PlotWidget()
        styles = {'color': 'k', 'font-size': '20px'}

        pen_n = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DashLine)
        pen_k = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DotLine)

        if self.unit_combobox.currentIndex() == 0:

            if self.include_n_check.isChecked() == True:
                self.graph_nk_peak_sum.plot(self.wavelength, self.n, pen=pen_n)
            if self.include_k_check.isChecked() == True:
                self.graph_nk_peak_sum.plot(self.wavelength, self.k, pen=pen_k)

            self.graph_nk_peak_sum.setLabel('bottom', 'Wavelength', units='m', **styles)
            self.graph_nk_peak_sum.getAxis('bottom').setScale(1e-9)
        elif self.unit_combobox.currentIndex() == 1:
            if self.include_n_check.isChecked() == True:
                self.graph_nk_peak_sum.plot(self.energy, self.n, pen=pen_n)
            if self.include_k_check.isChecked() == True:
                self.graph_nk_peak_sum.plot(self.energy, self.k, pen=pen_k)
            self.graph_nk_peak_sum.setLabel('bottom', 'Energy', units='eV', **styles)

        n_legend = pg.PlotDataItem(pen=pen_n)
        k_legend = pg.PlotDataItem(pen=pen_k)
        if self.include_n_check.isChecked() == True and self.include_k_check.isChecked() == True:
            legend = pg.LegendItem(pen="k")
            legend.addItem(n_legend, 'n')
            legend.addItem(k_legend, 'k')
            legend.setParentItem(self.graph_nk_peak_sum.graphicsItem())

        self.graph_nk_peak_sum.showGrid(x=True, y=True)
        self.graph_nk_peak_sum.setBackground('w')
        self.graph_nk_peak_sum.setTitle("sum of selected peak", color="k", size="20pt")
        self.graph_nk_peak_sum.setLabel('left', 'Index', units='a.u.', **styles)

        # self.graph_layout.addWidget(self.graph_nk_peak_sum)
        self.graph_tab_holder.addTab(self.graph_nk_peak_sum, "sum of selected peak")

    def nk_peak(self):
        self.graph_nk_peak = pg.PlotWidget()
        color_list = ["r", "g", "b", "c", "m", "y"]
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_nk_peak.showGrid(x=True, y=True)
        self.graph_nk_peak.setBackground('w')
        self.graph_nk_peak.setTitle("selected peak", color="k", size="20pt")
        self.graph_nk_peak.setLabel('left', 'Index', units='a.u.', **styles)

        legend = pg.LegendItem(pen="k")
        pen_n = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DashLine)
        pen_k = pg.mkPen(color="k", width=2, style=QtCore.Qt.PenStyle.DotLine)
        n_legend = pg.PlotDataItem(pen=pen_n)
        k_legend = pg.PlotDataItem(pen=pen_k)
        legend.setParentItem(self.graph_nk_peak.graphicsItem())

        if self.include_n_check.isChecked() == True and self.include_k_check.isChecked() == True:
            legend.addItem(n_legend, 'n')
            legend.addItem(k_legend, 'k')

        if self.unit_combobox.currentIndex() == 0:
            self.graph_nk_peak.setLabel('bottom', 'Wavelength', units='m', **styles)
            self.graph_nk_peak.getAxis('bottom').setScale(1e-9)
        elif self.unit_combobox.currentIndex() == 1:
            self.graph_nk_peak.setLabel('bottom', 'Energy', units='eV', **styles)

        peaks_n = []
        peaks_k = []

        for i in range(0, self.solution_table.rowCount()):
            n, k = get_layer_nk_fb(1, self.wavelength, np.array([self.centers[i]]), np.array([self.widths[i]]),
                                   np.array([self.areas[i]]),
                                   self.band_gap,self.n_infinity)

            peaks_n.append(n)
            peaks_k.append(k)

        for i in range(0, self.solution_table.rowCount()):

            if self.solution_table.cellWidget(i, 0).isChecked() == True:

                if self.unit_combobox.currentIndex() == 0:
                    pen_legend = pg.mkPen(color=color_list[i], width=2)
                    pen_for_n = pg.mkPen(color=color_list[i], width=2, style=QtCore.Qt.PenStyle.DashLine)
                    pen_for_k = pg.mkPen(color=color_list[i], width=2, style=QtCore.Qt.PenStyle.DotLine)

                    if self.include_n_check.isChecked():
                        self.graph_nk_peak.plot(self.wavelength, peaks_n[i], pen=pen_for_n)
                    if self.include_k_check.isChecked():
                        self.graph_nk_peak.plot(self.wavelength, peaks_k[i], pen=pen_for_k)

                    legend.addItem(pg.PlotDataItem(pen=pen_legend), f"peak {i + 1}")


                elif self.unit_combobox.currentIndex() == 1:
                    pen_legend = pg.mkPen(color=color_list[i], width=2)
                    pen_for_n = pg.mkPen(color=color_list[i], width=2, style=QtCore.Qt.PenStyle.DashLine)
                    pen_for_k = pg.mkPen(color=color_list[i], width=2, style=QtCore.Qt.PenStyle.DotLine)

                    if self.include_n_check.isChecked():
                        self.graph_nk_peak.plot(self.energy, peaks_n[i], pen=pen_for_n)
                    if self.include_k_check.isChecked():
                        self.graph_nk_peak.plot(self.energy, peaks_k[i], pen=pen_for_k)

                    legend.addItem(pg.PlotDataItem(pen=pen_legend), f"peak {i + 1}")

        # self.graph_layout.addWidget(self.graph_nk_peak)
        self.graph_tab_holder.addTab(self.graph_nk_peak, "nk peak")

    def update_ui(self):
        # for i in reversed(range(self.graph_layout.count())):
        #     self.graph_layout.itemAt(i).widget().setParent(None)

        self.graph_tab_holder.clear()

        self.n_infinity = self.n_inf_output.value()
        self.band_gap = self.eg_output.value()
        self.thickness = self.thickness_output.value()

        self.get_peaks()
        self.get_nk()
        self.table_index()
        self.nk_peak_sum()
        self.nk_peak()

    def save_index(self):
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



    def save_solution_spread(self):

        spread = self.spread_input.value()

        name, _ = QFileDialog.getSaveFileName()
        if name == "":
            return

        file = open(name, 'w')
        file.write(f"Number of Terms ,  {self.layer.fb_term}\n")
        file.write(f"\n")
        file.write(f"Parameter , Min , Max \n")
        file.write(f"\n")

        file.write(f"Thickness (nm) , {self.thickness * (1 - spread)} , {self.thickness * (1 + spread)} \n")

        if self.layer.fb_term > 0:
            file.write(f"n infinity , {self.n_infinity * (1 - spread)} , {self.n_infinity * (1 + spread)} \n")
            file.write(f"Band Gap (eV) , {self.band_gap * (1 - spread)} , {self.band_gap * (1 + spread)} \n")
            file.write(f"\n")
            file.write(f"Units ,{self.parameters_type_combobox.currentIndex()} \n")
            file.write(f"\n")
            for i in range(0, self.layer.fb_term):
                if self.parameters_type_combobox.currentIndex() == 0:
                    file.write(f"Peak {i + 1} \n")
                    file.write(
                        f"Center (eV) {i} , {self.centers[i] * (1 - spread)} , {self.centers[i] * (1 + spread)} \n")
                    file.write(
                        f"Width (eV) {i} , {self.widths[i] * (1 - spread)} , {self.widths[i] * (1 + spread)} \n")
                    file.write(
                        f"Area (1/eV) {i} , {self.areas[i] * (1 - spread)} , {self.areas[i] * (1 + spread)} \n")

                if self.parameters_type_combobox.currentIndex() == 1:
                    file.write(f"Peak {i + 1} \n")
                    file.write(
                        f"A {i} , {self.a[i] * (1 - spread)} , {self.a[i] * (1 + spread)} \n")
                    file.write(
                        f"B (eV) {i} , {self.b[i] * (1 - spread)} , {self.b[i] * (1 + spread)} \n")
                    file.write(
                        f"C (eV^2) {i} , {self.c[i] * (1 - spread)} , {self.c[i] * (1 + spread)} \n")

        file.close()
