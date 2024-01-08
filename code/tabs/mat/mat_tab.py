import os

import matplotlib
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFileDialog

from essential.script import convert
from tabs.mat.param_window.algoparam import AlgoParam
from tabs.mat.param_window.layer_param import LayerParamWindow
from tabs.mat.result.result import Result
from tabs.mat.result.result_session import ResultSession


class MatTab(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'MatTab.ui'), self)

        self.algo_button.clicked.connect(self.show_algo_param_window)
        self.peak_button.clicked.connect(self.show_peak_param_window)
        self.file_output.textChanged.connect(self.update_tab)
        self.term_input.valueChanged.connect(self.update_tab)

        self.file_button.clicked.connect(self.choise_file)
        self.start_button.clicked.connect(self.run_algo)

        self.threadpool = QtCore.QThreadPool()
        self.algo_window = AlgoParam()
        self.update_tab()

    def update_tab(self):

        self.peak_window = LayerParamWindow(name=self.file_output.text(), term=self.term_input.value())
        self.tab_holder.clear()

        if os.path.exists(self.file_output.text()):
            self.start_button.setEnabled(True)
            self.file = self.file_output.text()


            result = convert(self.file)

            self.wavelength_mat = result[0]
            self.n_mat = result[1]
            self.k_mat = result[2]

            self.create_graph_file()
            self.create_update_graph()

        else:
            self.start_button.setEnabled(False)
            print("file not found")

    def run_algo(self):
        self.tab_holder.clear()
        self.create_graph_file()
        self.create_update_graph()

        algo_param = self.algo_window.get_param()
        peak_data = self.peak_window.get_data()

        self.progress_bar.setMaximum(((algo_param["num_generations"] + 2) * algo_param["sol_per_pop"]))
        self.progress_bar.setValue(0)

        self.tab_holder.setTabEnabled(1, True)

        session = ResultSession(peak_param=peak_data, algo_param=algo_param, wavelength_mat=self.wavelength_mat,
                                n_mat=self.n_mat, k_mat=self.k_mat)

        session.signals.progress_bar.connect(self.progress_bar.setValue)
        session.signals.chisquare.connect(self.chisquare_output.setValue)
        session.signals.best_chisquare.connect(self.best_chisquare_output.setValue)
        session.signals.graph_signal_fit.connect(self.update_graph_fit)
        session.signals.graph_signal_mat.connect(self.update_graph_mat)
        session.signals.graph_signal_best.connect(self.update_graph_best)
        session.signals.result.connect(self.display_result)

        self.threadpool.start(session)

    def display_result(self, solution, wavelength_mat, n_mat, k_mat):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.update_graph_fit([[], [], []])
        self.best_chisquare_output.setValue(-solution[1])
        self.result_window = Result(solution=solution[0], wavelength_mat=wavelength_mat, n_mat=n_mat, k_mat=k_mat)
        self.tab_holder.addTab(self.result_window, "Result")
    def create_update_graph(self):

        self.graph_update = pg.PlotWidget()

        self.graph_update.setBackground((255, 255, 255))
        # self.graph_sample.setBackground((32, 31, 33))
        self.graph_update.setTitle("Live result", color="k", size="20pt")
        self.graph_update.showGrid(x=True, y=True)

        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Index', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)

        pen_1_n = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_2_n = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.PenStyle.SolidLine)
        pen_3_n = pg.mkPen(color=(0, 255, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine)

        pen_1_k = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.PenStyle.DashLine)
        pen_2_k = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.PenStyle.DashLine)
        pen_3_k = pg.mkPen(color=(0, 255, 0), width=3, style=QtCore.Qt.PenStyle.DashLine)

        self.graph_update.addLegend()

        self.graph_update.plot([], [], pen=pen_2_n, name="MAT n")
        self.graph_update.plot([], [], pen=pen_2_k, name="MAT k")

        self.graph_update.plot([], [], pen=pen_3_n, name="Fit n")
        self.graph_update.plot([], [], pen=pen_3_k, name="Fit k")

        self.graph_update.plot([], [], pen=pen_1_n, name="Best n")
        self.graph_update.plot([], [], pen=pen_1_k, name="Best k")

        self.tab_holder.addTab(self.graph_update, "Live graph")
        self.tab_holder.setTabEnabled(1, False)


    def update_graph_fit(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[2].setData(graph_data[0], graph_data[1])
        list_plot[3].setData(graph_data[0], graph_data[2])
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Index', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix='n', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()

    def update_graph_mat(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[0].setData(graph_data[0], graph_data[1])
        list_plot[1].setData(graph_data[0], graph_data[2])
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Index', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix='n', **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()
        self.tab_holder.setTabEnabled(1, True)
        self.tab_holder.setCurrentIndex(1)

    def update_graph_best(self, graph_data):
        list_plot = self.graph_update.listDataItems()
        list_plot[4].setData(graph_data[0], graph_data[1])
        list_plot[5].setData(graph_data[0], graph_data[2])
        # self.graph_update.setXRange(graph_data[0][0]-20, graph_data[0][-1]+20)
        # self.graph_update.setYRange(0, graph_data[1].max())
        styles = {'color': 'k', 'font-size': '20px'}
        self.graph_update.setLabel('left', 'Index', units='a.u.', **styles)
        self.graph_update.setLabel('bottom', 'Wavelength', units='m', unitPrefix="n", **styles)
        self.graph_update.getAxis('bottom').setScale(1e-9)
        self.graph_update.addLegend()

    def choise_file(self):
        file, _ = QFileDialog.getOpenFileName()

        if file == "":
            return

        self.file_output.setText(file)

    def show_peak_param_window(self):
        if self.peak_window.isVisible():
            self.peak_window.hide()
        else:
            self.peak_window.show()

    def show_algo_param_window(self):
        if self.algo_window.isVisible():
            self.algo_window.hide()
        else:
            self.algo_window.show()

    def create_graph_file(self):
        self.graph_file = pg.PlotWidget()
        styles = {'color': 'k', 'font-size': '20px'}

        pen_n = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.PenStyle.SolidLine)
        pen_k = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.PenStyle.DashLine)

        self.graph_file.plot(self.wavelength_mat, self.n_mat, pen=pen_n)

        self.graph_file.plot(self.wavelength_mat, self.k_mat, pen=pen_k)

        self.graph_file.setLabel('bottom', 'Wavelength', units='m', **styles)
        self.graph_file.getAxis('bottom').setScale(1e-9)

        n_legend = pg.PlotDataItem(pen=pen_n)
        k_legend = pg.PlotDataItem(pen=pen_k)

        legend = pg.LegendItem(pen="k")
        legend.addItem(n_legend, 'n')
        legend.addItem(k_legend, 'k')
        legend.setParentItem(self.graph_file.graphicsItem())

        self.graph_file.showGrid(x=True, y=True)
        self.graph_file.setBackground('w')
        self.graph_file.setTitle("Index From MAT File", color="k", size="20pt")
        self.graph_file.setLabel('left', 'Index', units='a.u.', **styles)

        # self.graph_layout.addWidget(self.graph_nk_peak_sum)
        self.tab_holder.addTab(self.graph_file, "nk File")
