import numpy as np


def get_r(index_1: float, index_2: float, polarization: chr) -> float:
    if polarization == 's':
        return (index_1 - index_2) / (index_1 + index_2)

    if polarization == 'p':
        return (index_2 - index_1) / (index_1 + index_2)


def get_t(index_1: float, index_2: float) -> float:
    return 2 * index_1 / (index_1 + index_2)


def get_matrix_n(index_1: float, index_2: float, thickness: float, polarization: chr, wavelength: float) -> np.array:
    r = get_r(index_1, index_2, polarization)
    t = get_t(index_1, index_2)

    # Mn = [[a,b],[c,d]]
    kz = 2 * np.pi * index_1 * thickness / wavelength

    if kz.imag > 35:
        kz = kz.real + 35j

    a = np.exp(-1j * kz)
    b = r * np.exp(-1j * kz)
    c = r * np.exp(1j * kz)
    thickness = np.exp(1j * kz)

    result = np.array([[a, b], [c, thickness]], dtype=complex) * (1 / t)
    return result


def get_matrix_0(index_1: float, index_2: float, polarization: chr) -> np.array:
    r_0_1 = get_r(index_1, index_2, polarization)
    matrix_n = get_t(index_1, index_2) * np.array([[1, r_0_1], [r_0_1, 1]], dtype=complex)

    return matrix_n


def tmm(polarization: chr, index_list: np.array, thickness_list: np.array, wavelength: float) -> float:
    matrix_t = get_matrix_0(index_list[0], index_list[1], polarization)

    for i in range(1, len(index_list) - 1):
        matrix_n = get_matrix_n(index_list[i], index_list[i + 1], thickness_list[i], polarization, wavelength)
        matrix_t = np.dot(matrix_t, matrix_n)

    r = abs(matrix_t[1][0] / matrix_t[0][0]) ** 2

    return r