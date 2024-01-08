import os

import matplotlib
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets, uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from essential.analyse_session import AnalyseSession
from essential.layer import LayerForParamAnalysis, create_repertory, LayerForAnalysis
from essential.script import get_lamp_spectrum, get_stitch_reflectance, convert
from essential.simulation_session import SimulationSession
from tabs.analysis.menu_windows_analysis.algo_param.algoparam import AlgoParam
from tabs.analysis.menu_windows_analysis.result.analysis.result_window_analysis import ResultWindowAnalysis
from tabs.analysis.menu_windows_analysis.result.simulation.result_window_simulation import ResultWindowSimulation

matplotlib.use('QtAgg')


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, layout="tight")
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class AnalysisTab(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalyseTab.ui'), self)

        self.scroll_contents_layout = QtWidgets.QVBoxLayout()
        self.scroll_area_layers_contents.setLayout(self.scroll_contents_layout)

        self.add_layer_button.clicked.connect(self.add_layer)
        self.delete_all_button.clicked.connect(self.remove_all_layers)

        self.threadpool = QtCore.QThreadPool()

        # self.mat_combobox.hide()
        self.fb_spinbox.hide()
        self.fb_label.hide()

        self.file_data = None

        self.stack = []

        self.layers_repertory = []

        self.result_window = None
        self.simulation_window = None
        self.result_button.clicked.connect(self.show_result_window)

        self.algo_param_window = AlgoParam()
        self.algo_param_button.clicked.connect(self.show_algo_param_window)

        self.start_button.clicked.connect(self.start_analysis)
        self.simulation_button.clicked.connect(self.start_simulation)

        self.create_update_graph()

    def update_tab(self, folder_path):

        for i in range(0, self.graph_tab_holder.count() - 1):
            self.graph_tab_holder.removeTab(0)

        self.layers_repertory = []

        for i in reversed(range(self.scroll_contents_layout.count())):
            self.scroll_contents_layout.itemAt(i).widget().setParent(None)

        if os.path.exists(folder_path):

            self.layers_repertory = create_repertory(folder_path)

            for layer in self.layers_repertory:
                layer.button.clicked.connect(self.get_files)
                self.scroll_area_layers_contents.layout().addWidget(layer.button)
        else:

            print("mat folder path does not exist")

        self.layers_repertory[0].button.setChecked(True)
        self.get_files()



        self.create_graph_mat()
        self.create_graph_background()
        self.create_graph_lamp()
        self.create_graph_sample()

        self.graph_tab_holder.setCurrentIndex(0)

    def get_files(self):
        for layer in self.layers_repertory:
            if layer.button.isChecked():
                files = layer.nk_files

        self.mat_combobox.clear()
        for file in files:
            self.mat_combobox.addItem(str(file))

    def show_algo_param_window(self):
        if self.algo_param_window.isHidden():
            self.algo_param_window.show()
        else:
            self.algo_param_window.hide()

    def show_result_window(self):
        if self.result_window.isHidden():
            self.result_window.show()
        else:
            self.result_window.hide()

    def add_layer(self):

        index = self.analysis_table.rowCount()
        self.analysis_table.insertRow(index)

        for layer in self.layers_repertory:
            if layer.button.isChecked():
                self.analysis_table.setItem(index, 0, QtWidgets.QTableWidgetItem(layer.name))
                if self.mat_radio_button.isChecked():
                    use_layer = LayerForParamAnalysis(name=layer.name, nk_file=self.mat_combobox.currentText())
                    self.analysis_table.setItem(index, 1, QtWidgets.QTableWidgetItem("Mat file"))
                    self.analysis_table.setItem(index, 2, QtWidgets.QTableWidgetItem(self.mat_combobox.currentText()))



                elif self.fb_radio_button.isChecked():
                    use_layer = LayerForParamAnalysis(name=layer.name, fb_term=int(self.fb_spinbox.value()))
                    self.analysis_table.setItem(index, 1, QtWidgets.QTableWidgetItem("FB"))
                    self.analysis_table.setItem(index, 3, QtWidgets.QTableWidgetItem(str(self.fb_spinbox.value())))

        self.analysis_table.setCellWidget(index, 4, use_layer.button)
        use_layer.delete_button.clicked.connect(self.remove_layer)
        self.analysis_table.setCellWidget(index, 5, use_layer.delete_button)


        self.stack.append(use_layer)

        for i, layer in enumerate(self.stack):
            if i == 0 or i == len(self.stack) - 1:
                layer.param_window.first_or_last = True
            else:
                layer.param_window.first_or_last = False

    def remove_layer(self):
        print("remove layer")
        to_replace = []
        for i in range(0,len(self.stack)):
            if self.sender() is self.analysis_table.cellWidget(i, 5):
                self.analysis_table.removeRow(i)
            else:
                 to_replace.append(self.stack[i])

        self.stack = to_replace
        for i, layer in enumerate(self.stack):
            if i == 0 or i == len(self.stack) - 1:
                layer.param_window.first_or_last = True
            else:
                layer.param_window.first_or_last = False


    def remove_last_layer(self):
        self.analysis_table.removeRow(len(self.stack) - 1)
        self.stack.pop()


    def remove_all_layers(self):
        for i in range(len(self.stack)):
            self.remove_last_layer()

    def create_graph_mat(self):

        for layer in self.layers_repertory:

            pen_1 = pg.mkPen(color=(255, 0, 0), width=2, style=QtCore.Qt.PenStyle.SolidLine)
            pen_2 = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.PenStyle.SolidLine)
            graph = pg.PlotWidget()
            # graph.addLegend()

            for file in layer.nk_files:
                legend = pg.LegendItem()
                output = convert(file)
                wavelength = output[0]
                n = output[1]
                k = output[2]
                graph.plot(wavelength, n, pen=pen_1, symbol='x', symbolPen=(255, 0, 0), symbolBrush=(0, 0, 0),
                           symbolSize=8,
                           name='n')
                graph.plot(wavelength, k, pen=pen_2, symbol='o', symbolPen=(0, 0, 255), symbolBrush=(0, 0, 0),
                           symbolSize=8,
                           name='k')

                item_1 = pg.PlotDataItem(pen=pen_1, symbol='x', symbolPen=(255, 0, 0), symbolBrush=(0, 0, 0),
                                         symbolSize=8)
                item_2 = pg.PlotDataItem(pen=pen_2, symbol='o', symbolPen=(0, 0, 255), symbolBrush=(0, 0, 0),
                                         symbolSize=8)
                legend.addItem(item_1, 'n')
                legend.addItem(item_2, 'k')
                legend.setParentItem(graph.graphicsItem())

            styles = {'color': 'k', 'font-size': '20px'}
            graph.showGrid(x=True, y=True)
            graph.setBackground('w')
            graph.setTitle(layer.name, color="k", size="20pt")
            graph.setLabel('left', 'Index', units='a.u.', **styles)
            graph.setLabel('bottom', 'Wavelength', units='m', **styles)
            graph.getAxis('bottom').setScale(1e-9)

            # self.graph_tab_holder.addTab(graph, layer.name)
            self.graph_tab_holder.insertTab(0, graph, layer.name)

    def create_graph_lamp(self):
        lamp_spectrum = get_lamp_spectrum(**self.file_data)
        self.graph_lamp = pg.PlotWidget()

        x_1 = lamp_spectrum[0]  # wavelength nir
        y_1 = lamp_spectrum[2]  # intensity nir
        x_2 = lamp_spectrum[1]  # wavelength uv
        y_2 = lamp_spectrum[3]  # intensity uv

        self.graph_lamp.setBackground('w')
        self.graph_lamp.setTitle("Lamp spectrum", color="k", size="20pt")
        self.graph_lamp.showGrid(x=True, y=True)

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_lamp.setLabel('left', 'Intensity', units='count', **styles)
        self.graph_lamp.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_lamp.getAxis('bottom').setScale(1e-9)

        pen_1 = pg.mkPen(color=(255, 0, 0), width=2, style=QtCore.Qt.PenStyle.SolidLine)
        pen_2 = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.PenStyle.SolidLine)

        # self.graph_lamp.setXRange(200, 1000)
        # self.graph_lamp.setYRange(0, 1.1 * max(max(y_1), max(y_2)))
        # self.graph_lamp.plot(x_1, y_1, pen=pen_1, name="NIR", symbol='o', symbolSize=5, symbolBrush=('b'))
        self.graph_lamp.addLegend()
        self.graph_lamp.plot(x_1, y_1, pen=pen_1, name="NIR")
        self.graph_lamp.plot(x_2, y_2, pen=pen_2, name="UV")

        # self.layout_lamp = QtWidgets.QGridLayout()
        # self.layout_lamp.addWidget(self.graph_lamp)
        # self.lamp_graph_tab.setLayout(self.layout_lamp)

        # self.graph_tab_holder.addTab(self.graph_lamp, "Lamp spectrum")
        self.graph_tab_holder.insertTab(0, self.graph_lamp, "Lamp spectrum")

    def create_graph_background(self):

        background_uv_file = self.file_data["background_uv_file"]
        background_nir_file = self.file_data["background_nir_file"]

        wavelength_background_uv, intensity_background_uv = np.loadtxt(background_uv_file, skiprows=13, unpack=True)
        wavelength_background_nir, intensity_background_nir = np.loadtxt(background_nir_file, skiprows=2, unpack=True)

        self.graph_background = pg.PlotWidget()

        self.graph_background.setBackground('w')
        self.graph_background.setTitle("Background", color="k", size="20pt")
        self.graph_background.showGrid(x=True, y=True)

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_background.setLabel('left', 'Intensity', units='count', **styles)
        self.graph_background.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_background.getAxis('bottom').setScale(1e-9)

        pen_1 = pg.mkPen(color=(255, 0, 0), width=2, style=QtCore.Qt.PenStyle.SolidLine)
        pen_2 = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.PenStyle.SolidLine)

        # self.graph_lamp.setXRange(200, 1000)
        # self.graph_lamp.setYRange(0, 1.1 * max(max(y_1), max(y_2)))
        # self.graph_lamp.plot(x_1, y_1, pen=pen_1, name="NIR", symbol='o', symbolSize=5, symbolBrush=('b'))
        self.graph_background.addLegend()
        self.graph_background.plot(wavelength_background_nir, intensity_background_nir, pen=pen_1, name="NIR")
        self.graph_background.plot(wavelength_background_uv, intensity_background_uv, pen=pen_2, name="UV")

        # self.layout_background = QtWidgets.QGridLayout()
        # self.layout_background.addWidget(self.graph_background)
        # self.background_graph_tab.setLayout(self.layout_background)

        # self.graph_tab_holder.addTab(self.graph_background, "Background")

        self.graph_tab_holder.insertTab(0, self.graph_background, "Background")

    def create_graph_sample(self):

        lamp_spectrum = get_lamp_spectrum(**self.file_data)

        result = get_stitch_reflectance(limit=[0, 3000], lamp_spectrum=lamp_spectrum, **self.file_data)

        self.graph_sample = pg.PlotWidget()

        self.graph_sample.setBackground((255, 255, 255))
        # self.graph_sample.setBackground((32, 31, 33))
        self.graph_sample.setTitle("Sample", color="w", size="20pt")
        self.graph_sample.showGrid(x=True, y=True)

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_sample.setLabel('left', 'Reflectance', units='a.u.', **styles)
        self.graph_sample.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_sample.getAxis('bottom').setScale(1e-9)

        pen_1 = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_2 = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_3 = pg.mkPen(color=(0, 255, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)

        # pen_3 = pg.mkPen(color=(0, 255, 0), width=5, style=QtCore.Qt.PenStyle.DashLine)

        # self.graph_lamp.setXRange(200, 1000)
        # self.graph_lamp.setYRange(0, 1.1 * max(max(y_1), max(y_2)))
        # self.graph_lamp.plot(x_1, y_1, pen=pen_1, name="NIR", symbol='o', symbolSize=5, symbolBrush=('b'))
        self.graph_sample.addLegend()

        self.graph_sample.plot(result["cut_wavelength"], result["cut_reflectance"], pen=pen_3, name="Stitched")
        self.graph_sample.plot(result["wavelength_sample_nir"], result["reflectance_sample_nir"], pen=pen_1, name="NIR")
        self.graph_sample.plot(result["wavelength_sample_uv"], result["reflectance_sample_uv"], pen=pen_2, name="UV")

        # self.layout_sample = QtWidgets.QGridLayout()
        # self.layout_sample.addWidget(self.graph_sample)
        # self.sample_graph_tab.setLayout(self.layout_sample)

        # self.graph_tab_holder.addTab(self.graph_sample, "Sample")

        self.graph_tab_holder.insertTab(0, self.graph_sample, "Sample")


    def start_simulation(self):
        self.simulation_window=None

        simulation_stack = []

        if len(self.stack) <= 2:
            print("Not enough layers")
            return None
        for layer in self.stack:
            data = layer.param_window.get_data()
            if data is None:
                return None
            new_layer = LayerForAnalysis(name=layer.name, fb_term=layer.fb_term, nk_file=layer.nk_file,
                                         data=data)
            simulation_stack.append(new_layer)

        simulation_session = SimulationSession(simulation_stack)
        list_layer , solution = simulation_session.get_result()

        self.simulation_window = ResultWindowSimulation(layer_list=list_layer, solution=solution,min=self.min_input.value(),max=self.max_input.value(),points=self.point_input.value())
        self.simulation_window.show()






    def start_analysis(self):
        self.result_window=None
        simulation_stack = []

        if len(self.stack) <= 2:
            print("Not enough layers")
            return None
        for layer in self.stack:
            data = layer.param_window.get_data()
            if data is None:
                return None
            new_layer = LayerForAnalysis(name=layer.name, fb_term=layer.fb_term, nk_file=layer.nk_file,
                                         data=data)
            simulation_stack.append(new_layer)

        self.graph_tab_holder.removeTab(self.graph_tab_holder.count() - 1)
        self.create_update_graph()

        self.start_button.setEnabled(False)
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.result_button.setEnabled(False)

        algo_param = self.algo_param_window.get_param()

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(((algo_param["num_generations"] + 2) * algo_param["sol_per_pop"]))

        lamp_spectrum = get_lamp_spectrum(**self.file_data)

        result = get_stitch_reflectance(limit=[algo_param["wavelength_min"], algo_param["wavelength_max"]],
                                        lamp_spectrum=lamp_spectrum, **self.file_data)

        analysis_session = AnalyseSession(layer_list=simulation_stack, algo_param=algo_param,
                                          reflectance_exp=result["cut_reflectance"],
                                          wavelength_exp=result["cut_wavelength"])
        analysis_session.signals.progress_bar.connect(self.update_progress_bar_generation)
        analysis_session.signals.chisquare.connect(self.update_chisquare)
        analysis_session.signals.result.connect(self.create_result_window)
        analysis_session.signals.graph_signal_fit.connect(self.update_graph_fit)
        analysis_session.signals.graph_signal_exp.connect(self.update_graph_exp)
        analysis_session.signals.graph_signal_best.connect(self.update_graph_best)

        self.threadpool.start(analysis_session)

    def create_update_graph(self):

        self.graph_update = pg.PlotWidget()

        self.graph_update.setBackground((255, 255, 255))
        # self.graph_sample.setBackground((32, 31, 33))
        self.graph_update.setTitle("Live result", color="k", size="20pt")
        self.graph_update.showGrid(x=True, y=True)

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Reflectance', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)

        pen_1 = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_2 = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_3 = pg.mkPen(color=(0, 255, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        self.graph_update.addLegend()

        self.graph_update.plot([], [], pen=pen_2, name="Exp")
        self.graph_update.plot([], [], pen=pen_3, name="Fit")
        self.graph_update.plot([], [], pen=pen_1, name="Best")

        self.graph_tab_holder.addTab(self.graph_update, "Live graph")
        self.graph_tab_holder.setTabEnabled(self.graph_tab_holder.count() - 1, False)
        self.graph_tab_holder.setCurrentIndex(0)

    def update_graph_fit(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[1].setData(graph_data[0], graph_data[1])
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Reflectance', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix='n', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()

    def update_graph_exp(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[0].setData(graph_data[0], graph_data[1])
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Reflectance', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix='n', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()
        self.graph_tab_holder.setTabEnabled(self.graph_tab_holder.count() - 1, True)
        self.graph_tab_holder.setCurrentIndex(self.graph_tab_holder.count() - 1)

    def update_graph_best(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[2].setData(graph_data[0], graph_data[1])
        # self.graph_update.setXRange(graph_data[0][0]-20, graph_data[0][-1]+20)
        # self.graph_update.setYRange(0, graph_data[1].max())
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Reflectance', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix="n", **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()

    def update_progress_bar_generation(self, value):
        self.progress_bar.setValue(value)

    def update_chisquare(self, chisquare):
        self.chisquare_output.setValue(chisquare)

    def create_result_window(self, result, wavelength_exp, reflectance_exp, layer_list):
        self.progress_bar.setValue(self.progress_bar.maximum())

        solution = result[0]
        chisquare = -result[1]

        self.result_window = ResultWindowAnalysis(layer_list=layer_list,
                                                  wavelength_exp=wavelength_exp,
                                                  reflectance_exp=reflectance_exp,
                                                  solution=solution,
                                                  chisquare=chisquare)

        self.result_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.update_graph_fit([[], []])
        self.result_window.show()
