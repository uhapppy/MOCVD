import numpy as np
from scipy.interpolate import interp1d


# this function return the lamp spectrum
def get_lamp_spectrum(background_uv_file, background_nir_file, silicon_uv_file, silicon_nir_file,
                      silicon_reference_file, *args, **kwargs):
    # we load the background data from file
    wavelength_background_uv, intensity_background_uv = np.loadtxt(background_uv_file, skiprows=13, unpack=True)
    wavelength_background_nir, intensity_background_nir = np.loadtxt(background_nir_file, skiprows=2, unpack=True)

    # we load the silicon data from file
    wavelength_si_uv, intensity_si_uv = np.loadtxt(silicon_uv_file, skiprows=13, unpack=True)
    wavelength_si_nir, intensity_si_nir = np.loadtxt(silicon_nir_file, skiprows=2, unpack=True)

    # we substract the background data (noise) from the silicon data
    corrected_intensity_si_uv = intensity_si_uv - intensity_background_uv
    corrected_intensity_si_nir = intensity_si_nir - intensity_background_nir

    # we load the silicon reference data from file
    wavelength_si_ref, reflectance_si_ref = np.loadtxt(silicon_reference_file, skiprows=1, unpack=True)

    # we interpolate the reference data to have the reflectance of the reference for the same wavelength as the
    # experimental silicon  data
    nir_interpolation = interp1d(wavelength_si_ref, reflectance_si_ref, kind='quadratic', fill_value="extrapolate")
    uv_interpolation = interp1d(wavelength_si_ref, reflectance_si_ref, kind='cubic', fill_value="extrapolate")

    ref_reflectance_nir = nir_interpolation(wavelength_si_nir)
    ref_reflectance_uv = uv_interpolation(wavelength_si_uv)

    # we extract the lamp spectrum by using the formula : I_light = I_sample/reflectance_sample
    intensity_light_nir = corrected_intensity_si_nir / ref_reflectance_nir
    intensity_light_uv = corrected_intensity_si_uv / ref_reflectance_uv

    lamp_spectrum = np.row_stack((wavelength_si_nir, wavelength_si_uv, intensity_light_nir, intensity_light_uv))

    return lamp_spectrum


# this function return the stiched experimental reflectance of the sample
def get_stitch_reflectance(background_uv_file, background_nir_file, sample_uv_file, sample_nir_file, lamp_spectrum,
                           limit,scaling, *args, **kwargs):
    # we load the background data from file
    wavelength_background_uv, intensity_background_uv = np.loadtxt(background_uv_file, skiprows=13, unpack=True)
    wavelength_background_nir, intensity_background_nir = np.loadtxt(background_nir_file, skiprows=2, unpack=True)

    # we load the sample data from file
    wavelength_sample_uv, intensity_sample_uv = np.loadtxt(sample_uv_file, skiprows=13, unpack=True)
    wavelength_sample_nir, intensity_sample_nir = np.loadtxt(sample_nir_file, skiprows=2, unpack=True)

    # we substract the background data (noise) from the sample data
    intensity_sample_uv = intensity_sample_uv - intensity_background_uv
    intensity_sample_nir = intensity_sample_nir - intensity_background_nir

    # we load the lamp spectrum calculated before
    wavelength_lamp_nir = lamp_spectrum[0]
    wavelength_lamp_uv = lamp_spectrum[1]
    intensity_lamp_nir = lamp_spectrum[2]
    intensity_lamp_uv = lamp_spectrum[3]

    # we calculate the reflectance of the sample by using the formula : reflectance = I_reflected/I_incident
    # in our case this convert to : reflectance = I_sample/I_lamp
    reflectance_sample_nir = intensity_sample_nir / intensity_lamp_nir
    reflectance_sample_uv = intensity_sample_uv / intensity_lamp_uv

    # we create 4 array that will store the reflectance and the wavelength of the 4 part of the spectra (uv ,
    # middle uv , middle nir ,nir) instead of the 2 part (uv , nir) that we have at the beginning
    new_reflectance_uv = np.array([])
    new_reflectance_nir = np.array([])

    new_wavelength_uv = np.array([])
    new_wavelength_nir = np.array([])

    middle_reflectance_uv = np.array([])
    middle_reflectance_nir = np.array([])

    middle_wavelength_uv = np.array([])
    middle_wavelength_nir = np.array([])

    # we then split the spectra in 4 part
    for wavelength in wavelength_sample_uv:
        if wavelength < 649:
            new_wavelength_uv = np.append(new_wavelength_uv, wavelength)
            new_reflectance_uv = np.append(new_reflectance_uv,
                                           reflectance_sample_uv[wavelength_sample_uv == wavelength])
        if 649 <= wavelength < 861:
            middle_wavelength_uv = np.append(middle_wavelength_uv, wavelength)
            middle_reflectance_uv = np.append(middle_reflectance_uv,
                                              reflectance_sample_uv[np.where(wavelength_sample_uv == wavelength)])

    for wavelength in wavelength_sample_nir:
        if wavelength >= 861:
            new_wavelength_nir = np.append(new_wavelength_nir, wavelength)
            new_reflectance_nir = np.append(new_reflectance_nir,
                                            reflectance_sample_nir[wavelength_sample_nir == wavelength])
        if 649 <= wavelength < 861:
            middle_wavelength_nir = np.append(middle_wavelength_nir, wavelength)
            middle_reflectance_nir = np.append(middle_reflectance_nir,
                                               reflectance_sample_nir[wavelength_sample_nir == wavelength])

    # we then interpolate both part of the middle spectra
    interpolation_uv = interp1d(middle_wavelength_uv, middle_reflectance_uv, kind='cubic', fill_value="extrapolate")
    interpolation_nir = interp1d(middle_wavelength_nir, middle_reflectance_nir, kind='cubic', fill_value="extrapolate")

    average = np.arange(649, 861, 0.36)

    # we then calculate the reflectance of the middle spectra for each wavelength in the average array using the interpolation
    interpolate_reflectance_uv = interpolation_uv(average)
    interpolate_reflectance_nir = interpolation_nir(average)

    # we then calculate the average of the reflectance of the middle spectra for each wavelength in the average array
    interpolate_reflectance_average = (interpolate_reflectance_uv + interpolate_reflectance_nir) / 2

    # we then put the 3 part of the spectra together
    reflectance = np.concatenate((new_reflectance_uv, interpolate_reflectance_average, new_reflectance_nir))
    wavelength = np.concatenate((new_wavelength_uv, average, new_wavelength_nir))

    # we then cut the spectra to have the interval that we want
    cut_wavelength = np.array([])
    cut_reflectance = np.array([])

    for i, wavelength in enumerate(wavelength):
        if limit[1] >= wavelength >= limit[0]:
            cut_wavelength = np.append(cut_wavelength, wavelength)
            cut_reflectance = np.append(cut_reflectance, reflectance[i])

    stitch_reflectance = np.array([cut_wavelength, cut_reflectance])

    return dict(cut_wavelength=cut_wavelength,
                cut_reflectance=cut_reflectance*scaling,
                reflectance_sample_nir=reflectance_sample_nir*scaling,
                reflectance_sample_uv=reflectance_sample_uv*scaling,
                wavelength_sample_nir=wavelength_sample_nir*scaling,
                wavelength_sample_uv=wavelength_sample_uv*scaling,
                )


def convert_from_abc(a, b, c ,Eg):
    center = b / 2
    width = np.sqrt(4 * c - b ** 2)
    area = 2 * np.pi * a / width
    return center, width, area


def convert_to_abc(center, width, area,Eg):
    b = 2 * center
    c = (b ** 2 + width ** 2) / 4
    a = area * width / (2 * np.pi)
    return a, b, c


def get_type(txt_file):
    file = open(txt_file, "r")
    lines = file.readlines()

    if lines[1] == "ANGSTROMS\n" and lines[2] == "NK\n":
        return 1
    elif lines[1] == "eV\n" and lines[2] == "e1e2\n":
        return 2
    elif lines[1] == "nm\n" and lines[2] == "nk\n":
        return 3
    elif lines[1] == "eV\n" and lines[2] == "nk\n":
        return 4
    elif lines[1] == "um\n" and lines[2] == "nk\n":
        return 5
    else:
        return 0


def get_index_type_1(file):
    data = np.loadtxt(file, skiprows=3)
    wavelength = data[:, 0] / 10
    n = data[:, 1]
    k = data[:, 2]
    output = np.array([wavelength, n, k])
    return output


def get_index_type_2(file):
    data = np.loadtxt(file, skiprows=3)
    hc = 1239.85
    wavelength = hc / data[:, 0]
    e1 = data[:, 1]
    e2 = data[:, 2]

    r = np.array(np.sqrt(e1 ** 2 + e2 ** 2))
    phi = np.array(np.arctan(e2 / e1))  # (in degrees, not rad)

    n = np.array(np.sqrt(r) * np.cos(phi / 2))
    k = np.sqrt(np.array(np.sqrt(r) * np.sin(phi / 2)) ** 2)

    output = np.array([wavelength, n, k])
    return output


def get_index_type_3(file):
    data = np.loadtxt(file, skiprows=3)
    wavelength = data[:, 0]
    n = data[:, 1]
    k = data[:, 2]
    output = np.array([wavelength, n, k])
    return output


def get_index_type_4(file):
    data = np.loadtxt(file, skiprows=3)
    hc = 1239.85
    wavelength = hc / data[:, 0]
    n = data[:, 1]
    k = data[:, 2]
    output = np.array([wavelength, n, k])
    return output


def get_index_type_5(file):
    data = np.loadtxt(file, skiprows=3)
    wavelength = data[:, 0] * 1000
    n = data[:, 1]
    k = data[:, 2]
    output = np.array([wavelength, n, k])
    return output


def convert(file):
    identity = get_type(file)
    if identity == 1:
        return get_index_type_1(file)
    elif identity == 2:
        return get_index_type_2(file)
    elif identity == 3:
        return get_index_type_3(file)
    elif identity == 4:
        return get_index_type_4(file)
    elif identity == 5:
        return get_index_type_5(file)
    else:
        print("this file type is not supported yet")

