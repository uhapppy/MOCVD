import time

from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
import pygad
import numpy as np

from essential.script import convert
from essential.tmm import tmm
from essential.layer import get_reflectance, LayerForResult, get_layer_nk_fb


class ResultSessionSignals(QObject):
    progress_bar = pyqtSignal(int)
    chisquare = pyqtSignal(float)
    best_chisquare = pyqtSignal(float)
    result = pyqtSignal(tuple, list, list, list)
    graph_signal_mat = pyqtSignal(list)
    graph_signal_fit = pyqtSignal(list)
    graph_signal_best = pyqtSignal(list)


class ResultSession(QRunnable):
    def __init__(self, peak_param, algo_param, wavelength_mat, n_mat, k_mat):
        super().__init__()
        print(peak_param)
        self.peak_param = peak_param
        self.fb_term = len(peak_param) // 3 - 1

        self.algo_param = algo_param
        self.counter = 0

        self.wavelength_mat = []
        self.n_mat = []
        self.k_mat = []

        for i, wavelength in enumerate(wavelength_mat):
            if wavelength >= algo_param["wavelength_min"] and wavelength <= algo_param["wavelength_max"]:
                self.wavelength_mat.append(wavelength)
                self.n_mat.append(n_mat[i])
                self.k_mat.append(k_mat[i])

        self.chi_square_best = np.inf

        self.generation_completed = 0
        self.solution_completed = 0
        self.value = 0

        self.gene_space = []
        self.create_gene_space()

        self.signals = (ResultSessionSignals())

    def create_gene_space(self):

        self.gene_space.append(self.peak_param["thickness"])
        self.gene_space.append(self.peak_param["n inf"])
        self.gene_space.append(self.peak_param["eg"])
        for i in range(0, self.fb_term):
            self.gene_space.append(self.peak_param[f"center_{i}"])
            self.gene_space.append(self.peak_param[f"width_{i}"])
            self.gene_space.append(self.peak_param[f"area_{i}"])

        self.algo_param["gene_space"] = self.gene_space
        self.algo_param["num_genes"] = len(self.gene_space)

    def run_genetic(self, ga_instance, solution, solution_idx):


        n_inf = solution[1]
        band_gap = solution[2]

        center = []
        width = []
        area = []
        for i in range(0, self.fb_term):
            center.append(solution[3 + 3 * i])
            width.append(solution[4 + 3 * i])
            area.append(solution[5 + 3 * i])

        n, k = get_layer_nk_fb(fb_term=self.fb_term, experimental_wavelength=self.wavelength_mat, n_inf=n_inf,
                               band_gap=band_gap, center=center, width=width, area=area)

        residual_n = n - self.n_mat
        residual_k = k - self.k_mat

        chi_square = (np.sum(residual_n ** 2) + np.sum(residual_k ** 2)) / len(self.wavelength_mat)

        if self.generation_completed < ga_instance.generations_completed:
            self.generation_completed = ga_instance.generations_completed
            self.solution_completed = 0
            self.value = self.generation_completed * ga_instance.sol_per_pop

        elif self.generation_completed >= ga_instance.generations_completed:
            self.solution_completed += 1
            self.value = self.generation_completed * ga_instance.sol_per_pop + self.solution_completed

        self.signals.chisquare.emit(chi_square)
        self.signals.progress_bar.emit(self.value)

        if chi_square < self.chi_square_best:
            self.chi_square_best = chi_square
            self.wavelength_best = self.wavelength_mat
            self.n_best = n
            self.k_best = k
            self.signals.best_chisquare.emit(self.chi_square_best)
            self.signals.graph_signal_best.emit([self.wavelength_best, self.n_best, self.k_best])
        else:
            self.signals.graph_signal_fit.emit([self.wavelength_mat, n, k])
            time.sleep(0.01)

        return -chi_square

    @pyqtSlot()
    def run(self):
        self.signals.graph_signal_mat.emit([self.wavelength_mat, self.n_mat, self.k_mat])
        param = self.algo_param
        param.pop("wavelength_min")
        param.pop("wavelength_max")
        self.ga_instance = pygad.GA(**param, fitness_func=self.run_genetic)
        self.ga_instance.run()

        self.signals.result.emit(self.ga_instance.best_solution(), self.wavelength_mat, self.n_mat, self.k_mat)
        pass
