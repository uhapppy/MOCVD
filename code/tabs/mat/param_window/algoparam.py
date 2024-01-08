import os
import sys
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets, uic




class AlgoParam(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AlgoParamWindow.ui'), self)




    def get_param(self):
        param = dict()

        param["wavelength_min"] = float(self.wave_min_input.text())
        param["wavelength_max"] = float(self.wave_max_input.text())


        param["num_generations"] = self.generation_input.value()
        param["num_parents_mating"] = self.mating_input.value()
        param["sol_per_pop"] = self.solution_input.value()


        param["parent_selection_type"] = self.selection_type_combobox.currentText().replace(" ", "_").lower()
        param["keep_parents"] = self.parent_input.value()
        param["keep_elitism"] = self.elite_input.value()
        param["K_tournament"] = self.k_input.value()

        param["crossover_type"] = self.crossover_combobox.currentText().replace(" ", "_").lower()
        param["crossover_probability"] = self.crossover_probability_input.value()

        param["mutation_type"] = self.mutation_combobox.currentText().replace(" ", "_").lower()
        param["mutation_probability"] = self.mutation_probability_input.value()

        return param



