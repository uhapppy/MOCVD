import os
import sys
import numpy as np
import csv
import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog

from essential.script import convert_from_abc


class LayerParamWindowAnalysis(QtWidgets.QWidget):
    def __init__(self, name, term, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'LayerParamWindow.ui'), self)
        self.save_button.clicked.connect(self.save_parameters)
        self.load_button.clicked.connect(self.load_parameters)

        self.parameters_type_combobox.currentTextChanged.connect(self.update_thing)

        self.scroll_area_contents_layout = QtWidgets.QVBoxLayout()
        self.scroll_area_contents.setLayout(self.scroll_area_contents_layout)

        self.term = term
        self.name = name
        self.first_or_last = False
        self.groups = []

        self.build_ui()
        self.hide()

    def build_ui(self):
        self.setWindowTitle(f"Layer parameters: {self.name}")
        self.name_label.setText(self.name)

        if self.term is not None:

            for i in range(self.term):
                self.create_group_peak(i)
            self.update_thing()
            self.adjustSize()

        elif self.term is None:
            self.n_inf_frame.hide()
            self.eg_frame.hide()

            self.option_group.hide()
            self.scroll_area.hide()

            self.adjustSize()

    def update_thickness_input(self):
        if self.first_or_last is True:
            self.thickness_min_input.setValue(9999.999999)
            self.thickness_max_input.setValue(9999.999999)
            self.thickness_min_input.setEnabled(False)
            self.thickness_max_input.setEnabled(False)
        elif self.first_or_last is False and (
                self.thickness_min_input.isEnabled() is False or self.thickness_max_input.isEnabled() is False):

            self.thickness_min_input.setValue(0)
            self.thickness_max_input.setValue(0)
            self.thickness_min_input.setEnabled(True)
            self.thickness_max_input.setEnabled(True)

        elif self.first_or_last is False and self.thickness_min_input.isEnabled() is True and self.thickness_max_input.isEnabled() is True:
            self.thickness_min_input.setEnabled(True)
            self.thickness_max_input.setEnabled(True)

    def update_thing(self):

        for group in self.groups:
            if self.parameters_type_combobox.currentText() == "Center,Width,Area":
                group.param_label_1.setText("Center (eV)")
                group.param_label_2.setText("Width (eV)")
                group.param_label_3.setText("Area (1/eV)")
                group.frame_4.hide()
            if self.parameters_type_combobox.currentText() == "A,B,C":
                group.param_label_1.setText("A")
                group.param_label_2.setText("B (eV)")
                group.param_label_3.setText("C (eV^2)")
                group.frame_4.show()

    def create_group_peak(self, peak_index):
        group = QtWidgets.QGroupBox()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'PeakGroup.ui'), group)
        group.setTitle(f"Peak {peak_index + 1}")


        group.param_label_min_1.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_min_2.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_min_3.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_min_4.setFont(QtGui.QFont("MS Shell Dlg 2", 8))

        group.param_label_max_1.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_max_2.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_max_3.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.param_label_max_4.setFont(QtGui.QFont("MS Shell Dlg 2", 8))



        group.input_min_1.setFont(QtGui.QFont("MS Shell Dlg 2", 8))

        group.input_min_2.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.input_min_2.valueChanged.connect(self.abc_check)
        group.input_min_3.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.input_min_3.valueChanged.connect(self.abc_check)

        group.input_min_4.setFont(QtGui.QFont("MS Shell Dlg 2", 8))



        group.input_max_1.setFont(QtGui.QFont("MS Shell Dlg 2", 8))

        group.input_max_2.valueChanged.connect(self.abc_check)
        group.input_max_2.setFont(QtGui.QFont("MS Shell Dlg 2", 8))
        group.input_max_3.valueChanged.connect(self.abc_check)
        group.input_max_3.setFont(QtGui.QFont("MS Shell Dlg 2", 8))

        group.input_max_4.setFont(QtGui.QFont("MS Shell Dlg 2", 8))

        self.groups.append(group)
        self.scroll_area_contents.layout().addWidget(group)


    def abc_check(self):
        for group in self.groups:
            if self.parameters_type_combobox.currentText() == "A,B,C":
                c_min = group.input_min_3.value()
                c_max = group.input_max_3.value()

                b_min = group.input_min_2.value()
                b_max = group.input_max_2.value()

                group.input_max_4.setValue(4*c_max-b_max**2)
                group.input_min_4.setValue(4*c_min-b_min**2)







    def save_parameters(self):

        name, _ = QFileDialog.getSaveFileName()
        if name == "":
            return

        file = open(name, 'w')
        file.write(f"Number of Terms ,  {self.term}\n")
        file.write(f"\n")
        file.write(f"Parameter , Min , Max \n")
        file.write(f"\n")

        file.write(f"Thickness (nm) , {self.thickness_min_input.text()} , {self.thickness_max_input.text()} \n")

        if self.term > 0:
            file.write(f"n infinity , {self.n_inf_min_input.text()} , {self.n_inf_max_input.text()} \n")
            file.write(f"Band Gap (eV) , {self.eg_min_input.text()} , {self.eg_max_input.text()} \n")
            file.write(f"\n")
            file.write(f"Units ,{self.parameters_type_combobox.currentIndex()} \n")
            file.write(f"\n")
            if self.parameters_type_combobox.currentText() == "Center,Width,Area":
                for i, group in enumerate(self.groups):
                    file.write(f"Peak {i + 1} \n")
                    file.write(
                        f"{group.param_label_1.text()} {i} eV , {group.input_min_1.text()} , {group.input_max_1.text()} \n")
                    file.write(
                        f"{group.param_label_2.text()} {i} eV , {group.input_min_2.text()} , {group.input_max_2.text()} \n")
                    file.write(
                        f"{group.param_label_3.text()} {i} 1/eV , {group.input_min_3.text()} , {group.input_max_3.text()} \n")

            elif self.parameters_type_combobox.currentText() == "A,B,C":
                for i, group in enumerate(self.groups):
                    file.write(f"Peak {i + 1} \n")
                    file.write(
                        f"{group.param_label_1.text()} {i}  , {group.input_min_1.text()} , {group.input_max_1.text()} \n")
                    file.write(
                        f"{group.param_label_2.text()} {i} eV , {group.input_min_2.text()} , {group.input_max_2.text()} \n")
                    file.write(
                        f"{group.param_label_3.text()} {i} eV^2 , {group.input_min_3.text()} , {group.input_max_3.text()} \n")


        file.close()

    def load_parameters(self):
        file, _ = QFileDialog.getOpenFileName()

        if file == "":
            return

        data = csv.reader(open(file))
        rows = [row for row in data]

        number_of_terms = int(rows[0][1])

        self.thickness_min_input.setValue(float(rows[4][1]))
        self.thickness_max_input.setValue(float(rows[4][2]))

        if number_of_terms > 0:
            self.n_inf_min_input.setValue(float(rows[5][1]))
            self.n_inf_max_input.setValue(float(rows[5][2]))
            self.eg_min_input.setValue(float(rows[6][1]))
            self.eg_max_input.setValue(float(rows[6][2]))

            self.parameters_type_combobox.setCurrentIndex(int(rows[8][1]))

            for i in range(number_of_terms):
                if i < self.term:
                    self.groups[i].input_min_1.setValue(float(rows[11 + 4 * i][1]))
                    self.groups[i].input_min_2.setValue(float(rows[12 + 4 * i][1]))
                    self.groups[i].input_min_3.setValue(float(rows[13 + 4 * i][1]))

                    self.groups[i].input_max_1.setValue(float(rows[11 + 4 * i][2]))
                    self.groups[i].input_max_2.setValue(float(rows[12 + 4 * i][2]))
                    self.groups[i].input_max_3.setValue(float(rows[13 + 4 * i][2]))

        self.update_thing()
        self.update_thickness_input()

    def get_data(self):
        data = dict()

        if self.first_or_last is True:
            pass

        if self.first_or_last is False:
            data["thickness"] = dict(low=self.thickness_min_input.value(),high = self.thickness_max_input.value())

        if self.term is not None:
            data["n inf"] = dict(low=self.n_inf_min_input.value(), high=self.n_inf_max_input.value())
            data["eg"] = dict(low=self.eg_min_input.value(),high= self.eg_max_input.value())
            if self.parameters_type_combobox.currentIndex() == 0:
                for i in range(self.term):
                    data[f"center_{i}"] = dict(low=self.groups[i].input_min_1.value(),
                                                                         high= self.groups[i].input_max_1.value())
                    data[f"width_{i}"] = dict(low=self.groups[i].input_min_2.value(),
                                                                          high=self.groups[i].input_max_2.value())
                    data[f"area_{i}"] = dict(low=self.groups[i].input_min_3.value(),
                                                                          high =self.groups[i].input_max_3.value())
            if self.parameters_type_combobox.currentIndex() == 1:
                for i in range(self.term):

                    a_min = self.groups[i].input_min_1.value()
                    b_min = self.groups[i].input_min_2.value()
                    c_min = self.groups[i].input_min_3.value()

                    a_max = self.groups[i].input_max_1.value()
                    b_max = self.groups[i].input_max_2.value()
                    c_max = self.groups[i].input_max_3.value()

                    if 4*c_min - b_min**2 < 0 or 4*c_max - b_max**2 < 0:
                        print("Error: Negative discriminant")
                        return None


                    center_min, width_min, area_min = convert_from_abc(a_min,
                                                                       b_min,
                                                                       c_min,
                                                                       self.eg_min_input.value())
                    center_max, width_max, area_max = convert_from_abc(a_max,
                                                                       b_max,
                                                                       c_max,
                                                                       self.eg_max_input.value())

                    data[f"center_{i}"] = dict(low=center_min,high= center_max)
                    data[f"width_{i}"] = dict(low=width_min, high=width_max)
                    data[f"area_{i}"] = dict(low=area_min, high=area_max)

        return data
