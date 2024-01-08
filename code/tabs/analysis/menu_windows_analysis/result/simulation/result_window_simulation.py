import os
import numpy as np
from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
from PyQt6.QtWidgets import QFileDialog
import colour
from colour.plotting import *
import colour.colorimetry as colorimetry



from scipy.interpolate import interp1d
from essential.layer import get_reflectance
from essential.tmm import tmm
from tabs.analysis.menu_windows_analysis.result.analysis.result_fb_tab_analysis import ResultFBTabAnalysis
from tabs.analysis.menu_windows_analysis.result.analysis.result_mat_tab_analysis import ResultMATTabAnalysis
from tabs.analysis.menu_windows_analysis.result.simulation.result_fb_tab_simulation import ResultFBTabSimulation
from tabs.analysis.menu_windows_analysis.result.simulation.result_mat_tab_simulation import ResultMATTabSimulation


class ResultWindowSimulation(QtWidgets.QWidget):
    def __init__(self, layer_list, solution,min,max,points, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ResultWindowSimulation.ui'), self)
        self.unit_combobox.currentIndexChanged.connect(self.update_ui)
        self.result_tab_holder.currentChanged.connect(self.check_update)
        self.export_button.clicked.connect(self.save_table)


        self.solution = solution
        self.wavelength = np.linspace(start=min, stop=max, num=points)
        self.energy = 1239.84187 / self.wavelength

        self.layer_list = layer_list

        for i in range(0, len(self.wavelength)):
            self.reflectance_table.insertRow(i)



        self.reflectance_peaks = None



        solution_start = 0

        for layer in self.layer_list:

            if layer.first_or_last == True:
                if layer.fb_term is not None:
                    self.result_tab_holder.addTab(
                        ResultFBTabSimulation(layer, self.solution[solution_start:(solution_start + 2 + layer.fb_term * 3)],
                                            self.wavelength), layer.name)
                    solution_start += (2 + layer.fb_term * 3)

                elif layer.fb_term is None:
                    self.result_tab_holder.addTab(ResultMATTabSimulation
                                                  (layer, 9999.999999, self.wavelength),
                                                  layer.name)


            else:
                if layer.fb_term is not None:
                    self.result_tab_holder.addTab(
                        ResultFBTabSimulation(layer, self.solution[solution_start:(solution_start + 3 + layer.fb_term * 3)],
                                            self.wavelength), layer.name)
                    solution_start += (3 + layer.fb_term * 3)
                elif layer.fb_term is None:
                    self.result_tab_holder.addTab(ResultMATTabSimulation(layer, self.solution[solution_start], self.wavelength),
                                                  layer.name)
                    solution_start += 1

        self.update_ui()


    def simulation_hide(self):
        pass

    def check_update(self, index):
        if index == 0:
            self.update_ui()

    def update_ui(self):
        for i in reversed(range(0,self.main_graph_layout.count())):
            self.main_graph_layout.itemAt(i).widget().setParent(None)

        self.get_reflectance_peaks()
        self.table()
        self.graph_reflectance()
        self.frame_color()

    def get_reflectance_peaks(self):
        reflection_inside = np.array([])
        thickness = np.array([])
        n_layers = np.zeros(shape=(len(self.layer_list), len(self.wavelength)))
        k_layers = np.zeros(shape=(len(self.layer_list), len(self.wavelength)))

        for i in range(0, self.result_tab_holder.count() - 1):
            tab = self.result_tab_holder.widget(i + 1)

            if tab.layer.first_or_last:
                thickness = np.append(thickness, np.inf)
            else:
                thickness = np.append(thickness, tab.thickness_output.value())

            n_layers[i] = tab.n
            k_layers[i] = tab.k


        for i, wavelength in enumerate(self.wavelength):
            # substrate , unknown tickness , air
            layer_n = np.array([n[i] for n in n_layers])
            layer_k = np.array([k[i] for k in k_layers])

            # we create a complex refractive index for each layer
            layer_index = layer_n + 1j * layer_k

            # we calculate the reflectance of the sample for the current wavelength and add it to the array

            reflection_inside = np.append(reflection_inside,
                                          tmm(polarization='s', index_list=layer_index, thickness_list=thickness,
                                              wavelength=wavelength))

        self.reflectance_peaks = reflection_inside

    def table(self):
        if self.unit_combobox.currentIndex() == 0:
            self.reflectance_table.setHorizontalHeaderLabels(['Wavelength (nm)', "Reflectance"])
            for i in range(0, len(self.wavelength)):
                self.reflectance_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.wavelength[i])))
                self.reflectance_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.reflectance_peaks[i])))


        elif self.unit_combobox.currentIndex() == 1:
            self.reflectance_table.setHorizontalHeaderLabels(['Energy (eV)', "Reflectance"])
            for i in range(0, len(self.energy)):
                self.reflectance_table.setItem(i, 0, QtWidgets.QTableWidgetItem("{:.6f}".format(self.energy[i])))
                self.reflectance_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:.6f}".format(self.reflectance_peaks[i])))

    def save_table(self):
        name, _ = QFileDialog.getSaveFileName()
        if name == "":
            return

        file = open(name, 'w')
        if self.unit_combobox.currentIndex() == 0:
            file.write(f"Wavelength (nm) , Experimental , Solution , Peaks  \n")
            for i in range(0, len(self.wavelength)):
                file.write(
                    f"{self.wavelength[i]} , {self.reflectance_peaks[i]} \n")
        elif self.unit_combobox.currentIndex() == 1:
            file.write(f"Energy (eV) , Experimental , Solution , Peaks  \n")
            for i in range(0, len(self.energy)):
                file.write(
                    f"{self.energy[i]} , {self.reflectance_peaks[i]} \n")

        file.close()





    def frame_color(self):
        #cmfs = colour.STANDARD_OBSERVERS_CMFS['CIE 1931 2 Degree Standard Observer']
        #illuminant = colour.ILLUMINANTS_RELATIVE_SPDS['D65']


        interpolation = interp1d(self.wavelength, self.reflectance_peaks, kind='quadratic', fill_value="extrapolate")
        wavelength= np.arange(350, 900, 1)
        reflectance = interpolation(wavelength)
        dict_reflectance = dict(zip(wavelength,reflectance ))
        distribution = colorimetry.SpectralDistribution(data = dict_reflectance)
        XYZbulk = colorimetry.sd_to_XYZ(sd=distribution)
        RGBbulk = colour.XYZ_to_sRGB(XYZbulk / 100)
        if max(RGBbulk > 1):  RGBbulk = RGBbulk / max(RGBbulk)
        color = colour.notation.RGB_to_HEX(RGBbulk)
        self.solution_peak_color_frame.setStyleSheet(f"background-color: {color}")



    def graph_reflectance(self):
        self.graph = pg.PlotWidget()

        self.graph.setBackground('w')
        self.graph.setTitle('Reflectance')
        self.graph.showGrid(x=True, y=True)
        self.graph.addLegend()

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph.setLabel('left', 'Reflectance', units='a.u.', **styles)

        if self.unit_combobox.currentIndex() == 0:
            self.graph.plot(self.wavelength, self.reflectance_peaks, pen=pg.mkPen('b', width=2), name='Peaks')
            self.graph.setLabel('bottom', 'Wavelength', units='m', **styles)
            self.graph.getAxis('bottom').setScale(1e-9)

        if self.unit_combobox.currentIndex() == 1:

            self.graph.plot(self.energy, self.reflectance_peaks, pen=pg.mkPen('b', width=2), name='Peaks')
            self.graph.setLabel('bottom', 'Energy', units='eV', **styles)

        self.main_graph_layout.addWidget(self.graph)
