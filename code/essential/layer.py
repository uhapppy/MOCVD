import os

import numpy as np
from PyQt6 import QtWidgets
from scipy.interpolate import interp1d

from essential.script import convert
from essential.tmm import tmm
from tabs.analysis.menu_windows_analysis.layer_param.layer_param import LayerParamWindowAnalysis



def create_repertory(folder_path):
    repertory = []

    files = np.array(os.listdir(folder_path))

    for file in files:

        layer_name = ""

        file_name = os.path.basename(file)

        for char in file_name:
            if char == "_" or char == "." or char == " ":
                break
            else:
                layer_name += char

        if layer_name not in [layer.name for layer in repertory]:
            repertory.append(
                LayerForRepertory(name=layer_name, nk_files=[os.path.join(folder_path, file)]))
        else:
            for layer in repertory:
                if layer.name == layer_name:
                    layer.nk_files.append(os.path.join(folder_path, file))
                    break

    return repertory


def one_term_fb(center, width, area, band_gap, wavelength):
    h = 4.1357e-15

    c = 299792458

    B = 2 * center
    C = (B ** 2 + width ** 2) / 4
    A = area * width / (2 * np.pi)

    e = (h * c / (wavelength * 1e-9))

    q = (1 / 2) * np.sqrt(4 * C - B ** 2)

    b_0 = (A / q) * (((-1 / 2) * B ** 2) + band_gap * B - band_gap ** 2 + C)

    c_0 = (A / q) * ((1 / 2) * B * (band_gap ** 2 + C) - 2 * band_gap * C)

    n_term = (b_0 * e + c_0) / (e ** 2 - B * e + C)

    k_term = A / (e ** 2 - B * e + C)

    return n_term, k_term


def get_layer_nk_file(nk_file, experimental_wavelength):
    output = convert(nk_file)
    mat_wavelength = output[0]
    mat_n = output[1]
    mat_k = output[2]

    n_interpolation = interp1d(mat_wavelength, mat_n, kind='linear', fill_value="extrapolate")
    k_interpolation = interp1d(mat_wavelength, mat_k, kind='linear', fill_value="extrapolate")

    n_out = n_interpolation(experimental_wavelength)
    k_out = k_interpolation(experimental_wavelength)

    # we update the n and k of the layer
    return n_out, k_out


def get_layer_nk_fb(fb_term, experimental_wavelength, center, width, area, band_gap, n_inf):
    h = 4.1357e-15
    c = 299792458

    n_out = np.array([])
    k_out = np.array([])

    for wavelength in experimental_wavelength:
        n = n_inf
        k = 0
        for i in range(0, fb_term):
            n_term, k_term = one_term_fb(center[i], width[i], area[i], band_gap, wavelength)

            n = n + n_term
            k = k + k_term

        k = (((h * c / (wavelength * 1e-9)) - band_gap) ** 2) * k

        n_out = np.append(n_out, n)
        k_out = np.append(k_out, k)

    return n_out, k_out


def get_reflectance(solution, layers, wavelength_exp):
    n_sample = np.zeros(shape=(len(layers), len(wavelength_exp)))
    k_sample = np.zeros(shape=(len(layers), len(wavelength_exp)))

    thickness_sample = np.array([])
    solution_offset = 0

    for i, layer in enumerate(layers):

        if layer.nk_file is not None:

            n_sample[i], k_sample[i] = get_layer_nk_file(nk_file=layer.nk_file,
                experimental_wavelength=wavelength_exp)

            if i != 0 and i != len(layers) - 1:
                thickness_sample = np.append(thickness_sample, solution[solution_offset])
                solution_offset += 1
            else:
                thickness_sample = np.append(thickness_sample, np.inf)

        elif layer.fb_term is not None:

            thickness = solution[solution_offset]
            thickness_sample = np.append(thickness_sample, thickness)

            n_inf = solution[solution_offset + 1]
            band_gap = solution[solution_offset + 2]

            n_out = np.array([])
            k_out = np.array([])

            center = []
            width = []
            area = []
            current_offset = 0
            for j in range(layer.fb_term):
                center.append(solution[current_offset + 3])
                width.append(solution[current_offset + 4])
                area.append(solution[current_offset + 5])
                current_offset += 3

            n_out, k_out = get_layer_nk_fb(fb_term=layer.fb_term,experimental_wavelength=wavelength_exp, n_inf=n_inf,
                                                 band_gap=band_gap, center=center, width=width, area=area)

            n_sample[i], k_sample[i] = n_out, k_out
            solution_offset += 3 * layer.fb_term + 3

    reflection_inside = np.array([])

    for i, wavelength in enumerate(wavelength_exp):
        # substrate , unknown tickness , air
        layer_n = np.array([n[i] for n in n_sample])
        layer_k = np.array([k[i] for k in k_sample])

        # we create a complex refractive index for each layer
        layer_index = layer_n + 1j * layer_k

        # we calculate the reflectance of the sample for the current wavelength and add it to the array

        reflection_inside = np.append(reflection_inside, tmm(polarization='s', index_list=layer_index,
                                                             thickness_list=thickness_sample,
                                                             wavelength=wavelength))

    return reflection_inside


class LayerForParamAnalysis:

    def __init__(self, name, nk_file=None, fb_term=None):
        self.name = name

        self.fb_term = fb_term
        self.nk_file = nk_file

        self.param_window = LayerParamWindowAnalysis(name, fb_term)

        self.button = QtWidgets.QPushButton("Parameters")
        self.button.clicked.connect(self.window_control)

        self.delete_button = QtWidgets.QPushButton("Delete")



    def window_control(self):

        self.param_window.update_thickness_input()

        if self.param_window.isHidden():
            self.param_window.show()
        else:
            self.param_window.hide()


class LayerForRepertory:

    def __init__(self, name, nk_files):
        self.name = name
        self.nk_files = nk_files
        self.button = QtWidgets.QRadioButton(name)



class LayerForAnalysis:

    def __init__(self, name, nk_file=None, fb_term=None, data=None):
        self.name = name

        self.fb_term = fb_term
        self.nk_file = nk_file

        self.data = data


class LayerForResult:
    def __init__(self, name, nk_file=None, fb_term=None , first_or_last=None):
        self.name = name

        self.fb_term = fb_term
        self.nk_file = nk_file

        self.first_or_last = first_or_last





