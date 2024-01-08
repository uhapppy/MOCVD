from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
import pygad
import numpy as np

from essential.script import convert
from essential.tmm import tmm
from essential.layer import get_reflectance, LayerForResult


class AnalyseSessionSignals(QObject):
    progress_bar = pyqtSignal(int)
    chisquare = pyqtSignal(float)
    result = pyqtSignal(tuple, list, list, list)
    graph_signal_exp = pyqtSignal(list)
    graph_signal_fit = pyqtSignal(list)
    graph_signal_best = pyqtSignal(list)


class AnalyseSession(QRunnable):
    def __init__(self, layer_list, algo_param, reflectance_exp, wavelength_exp):
        super().__init__()

        self.layers = layer_list
        self.algo_param = algo_param
        self.reflectance_exp = reflectance_exp
        self.wavelength_exp = wavelength_exp

        self.wavelength_best = None
        self.reflectance_best = None
        self.chisquare_best = np.inf

        self.generation_completed = 0
        self.solution_completed = 0
        self.value = 0

        self.gene_space = []
        self.create_gene_space()

        self.signals = (AnalyseSessionSignals())

    def create_gene_space(self):
        for i, layer in enumerate(self.layers):

            if i > 0 and i < len(self.layers) - 1:
                self.gene_space.append(layer.data["thickness"])

            if layer.fb_term is not None:
                self.gene_space.append(layer.data["n inf"])
                self.gene_space.append(layer.data["eg"])

                for i in range(layer.fb_term):
                    self.gene_space.append(layer.data[f"center_{i}"])
                    self.gene_space.append(layer.data[f"width_{i}"])
                    self.gene_space.append(layer.data[f"area_{i}"])

        self.algo_param["gene_space"] = self.gene_space
        self.algo_param["num_genes"] = len(self.gene_space)

    def run_genetic(self, ga_instance, solution, solution_idx):

        reflectance_genetic = get_reflectance(solution=solution, wavelength_exp=self.wavelength_exp,
                                              layers=self.layers)

        residual = reflectance_genetic - self.reflectance_exp

        chisquare = np.sum(np.square(residual) / len(residual))
        #chisquare = np.sum(np.square(residual) / self.reflectance_exp)

        if self.generation_completed < ga_instance.generations_completed:
            self.generation_completed = ga_instance.generations_completed
            self.solution_completed = 0
            self.value = self.generation_completed * ga_instance.sol_per_pop


        elif self.generation_completed >= ga_instance.generations_completed:
            self.solution_completed += 1
            self.value = self.generation_completed * ga_instance.sol_per_pop + self.solution_completed

        self.signals.chisquare.emit(chisquare)
        self.signals.progress_bar.emit(self.value)

        if chisquare < self.chisquare_best:
            self.chisquare_best = chisquare
            self.wavelength_best = self.wavelength_exp
            self.reflectance_best = reflectance_genetic
            self.signals.graph_signal_best.emit([self.wavelength_best, self.reflectance_best])


        self.signals.graph_signal_fit.emit([self.wavelength_exp, reflectance_genetic])

        return -chisquare

    @pyqtSlot()
    def run(self):
        self.signals.graph_signal_exp.emit([self.wavelength_exp, self.reflectance_exp])
        param = self.algo_param
        param.pop("wavelength_min")
        param.pop("wavelength_max")
        self.ga_instance = pygad.GA(**param, fitness_func=self.run_genetic)
        self.ga_instance.run()

        layers_output = []
        for i, layer in enumerate(self.layers):
            if i ==0 or i==len(self.layers)-1:
                layers_output.append(LayerForResult(layer.name,layer.nk_file,layer.fb_term,True))
            else:
                layers_output.append(LayerForResult(layer.name,layer.nk_file,layer.fb_term,False))


        self.signals.result.emit(self.ga_instance.best_solution(), self.wavelength_exp, self.reflectance_exp,
                                 layers_output)
