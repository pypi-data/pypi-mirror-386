#
# tools for power3d app
#
import os
import numpy
import scipy.constants as codata
import h5py

from dabax.dabax_xraylib import DabaxXraylib
try: import xraylib
except: pass

from xoppylib.scattering_functions.fresnel import reflectivity_fresnel
from xoppylib.xoppy_xraylib_util import nist_compound_list, density
from xoppylib.mlayer import MLayer

from scipy.interpolate import interp2d, RectBivariateSpline
from srxraylib.util.h5_simple_writer import H5SimpleWriter
#
# calculation
#
def integral_2d(data2D,h=None,v=None, method=0):
    if h is None:
        h = numpy.arange(data2D.shape[0])
    if v is None:
        v = numpy.arange(data2D.shape[1])

    if method == 0:
        totPower2 = numpy.trapz(data2D, v, axis=1)
        totPower2 = numpy.trapz(totPower2, h, axis=0)
    else:
        totPower2 = data2D.sum() * (h[1] - h[0]) * (v[1] - v[0])

    return totPower2


def integral_3d(data3D, e=None, h=None, v=None, method=0):
    if e is None:
        e = numpy.arange(data3D.shape[0])
    if h is None:
        h = numpy.arange(data3D.shape[1])
    if v is None:
        v = numpy.arange(data3D.shape[2])

    if method == 0:

        totPower2 = numpy.trapz(data3D, v, axis=2)
        totPower2 = numpy.trapz(totPower2, h, axis=1)
        totPower2 = numpy.trapz(totPower2, e, axis=0)
    else:
        totPower2 = data3D.sum() * (e[1] - e[0]) * (h[1] - h[0]) * (v[1] - v[0])

    return totPower2


def calculate_component_absorbance_and_transmittance(
    e0, h0, v0,
    substance="Si",
    thick=0.5,
    angle=3.5,
    defection=1, # deflection 0=H 1=V
    dens="?",
    roughness=0.0,
    flags=0,  # 0=Filter 1=Mirror 2 = Aperture 3 magnifier, 4 screen rotation, 5 thin object filter, 6 multilayer, 7 External file
    hgap=1000.0,                             # used if flag in (0, 1, 2, 6, 7)
    vgap=1000.0,                             # used if flag in (0, 1, 2, 6, 7)
    hgapcenter=0.0,                          # used if flag in (0, 1, 2, 6, 7)
    vgapcenter=0.0,                          # used if flag in (0, 1, 2, 6, 7)
    gapshape=0,     # 0=rectangle, 1=circle  # used if flag in (0, 1, 2, 6, 7)
    hmag=1.0,
    vmag=1.0,
    hrot=0.0,       # used if flag in (0, 4, 7)
    vrot=0.0,       # used if flag in (0, 4, 7)
    thin_object_file='',
    thin_object_thickness_outside_file_area=0.0,
    thin_object_back_profile_flag=0,
    thin_object_back_profile_file='',
    multilayer_file='',
    external_reflectivity_file='',
    verbose=1,
    material_constants_library=None,
    ):

    if material_constants_library is None:
        try:    material_constants_library = xraylib
        except: material_constants_library = DabaxXraylib()
    #
    # important: the transmittance calculated here is referred on axes perp to the beam
    # therefore they do not include geometrical corrections for correct integral
    #

    e = e0.copy()
    h = h0.copy()
    v = v0.copy()

    transmittance = numpy.ones((e.size,h.size,v.size))
    E = e.copy()
    H = h.copy()
    V = v.copy()

    # initialize results

    #
    # get undefined densities
    #
    if flags in [0,1,5]:
        try:  # apply written value
            rho = float(dens)
        except:  # in case of ?
            rho = density(substance, material_constants_library=material_constants_library)
            print("Density for %s: %g g/cm3" % (substance, rho))
        dens = rho

    txt = ""

    txt_rotation = ""
    txt_rotation += '      H rotation angle [deg]: %f \n' % (hrot)
    txt_rotation += '      V rotation angle [deg]: %f \n' % (vrot)

    txt_aperture = ""
    txt_aperture += '      H gap [mm]: %f \n' % (hgap)
    txt_aperture += '      V gap [mm]: %f \n' % (vgap)
    txt_aperture += '      H gap center [mm]: %f \n' % (hgapcenter)
    txt_aperture += '      V gap center [mm]: %f \n' % (vgapcenter)


    if flags == 0:
        txt += '      *****   oe  [Filter] *************\n'
        txt += '      Material: %s\n' % (substance)
        txt += '      Density [g/cm^3]: %f \n' % (dens)
        txt += '      thickness [mm] : %f \n' % (thick)
        txt += txt_rotation
        txt += txt_aperture
    elif flags == 1:
        txt += '      *****   oe  [Mirror] *************\n'
        txt += '      Material: %s\n' % (substance)
        txt += '      Density [g/cm^3]: %f \n' % (dens)
        txt += '      grazing angle [mrad]: %f \n' % (angle)
        txt += '      roughness [A]: %f \n' % (roughness)
        txt += txt_aperture
    elif flags == 2:
        txt += '      *****   oe  [Aperture] *************\n'
        txt += txt_aperture
    elif flags == 3:
        txt += '      *****   oe  [Magnifier] *************\n'
        txt += '      H magnification: %f \n' % (hmag)
        txt += '      V magnification: %f \n' % (vmag)
    elif flags == 4:
        txt += '      *****   oe  [Screen rotated] *************\n'
        txt += txt_rotation
    elif flags == 5:
        txt += '      *****   oe  [Thin object filter] *************\n'
        txt += '      File with thickness for front surface [h5, OASYS-format]: %s \n' % (thin_object_file)
        if thin_object_back_profile_flag == 0:
            txt += '      Back surface set to z(x,y)=0\n'
        elif thin_object_back_profile_flag == 1:
            txt += '      File with thickness for back surface [h5, OASYS-format]: %s \n' % (thin_object_back_profile_file)
    elif flags == 6:
        txt += '      *****   oe  [Multilayer] *************\n'
        txt += '      File with multilayer parameters from XOPPY/Multilayer [h5]: %s \n' % (multilayer_file)
        txt += '      grazing angle [mrad]: %f \n' % (angle)
        txt += txt_aperture
    elif flags == 7:
        txt += '      *****   oe  [External Reflectivity File] *************\n'
        txt += '      File with multilayer parameters and incident angle (energy scan) from XOPPY/Multilayer [h5]: %s \n' % (multilayer_file)
        txt += txt_rotation
        txt += txt_aperture

    if flags == 0:  # filter
        for j, energy in enumerate(e):
            tmp = material_constants_library.CS_Total_CP(substance, energy / 1000.0)
            transmittance[j, :, :] = numpy.exp(-tmp * dens * (thick / 10.0))

        # rotation
        H = h / numpy.cos(vrot * numpy.pi / 180)
        V = v / numpy.cos(hrot * numpy.pi / 180)

        # aperture
        if gapshape == 0:
            h_indices_bad = numpy.where(numpy.abs(H - hgapcenter) > (0.5 * hgap))
            if len(h_indices_bad) > 0:
                transmittance[:, h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V - vgapcenter) > (0.5 * vgap))
            if len(v_indices_bad) > 0:
                transmittance[:, :, v_indices_bad] = 0.0
        elif gapshape == 1:
            for i in range(H.size):
                for j in range(V.size):
                    if (((H[i] - hgapcenter) / (hgap / 2)) ** 2 + ((V[j] - vgapcenter) / (vgap / 2)) ** 2) > 1:
                        transmittance[:, i, j] = 0.0

        absorbance = 1.0 - transmittance

    elif flags == 1:  # mirror
        tmp = numpy.zeros(e.size)

        for j, energy in enumerate(e):
            tmp[j] = material_constants_library.Refractive_Index_Re(substance, energy / 1000.0, dens)

        if tmp[0] == 0.0:
            raise Exception("Probably the substrance %s is wrong" % substance)

        delta = 1.0 - tmp
        beta = numpy.zeros(e.size)

        for j, energy in enumerate(e):
            beta[j] = material_constants_library.Refractive_Index_Im(substance, energy / 1000.0, dens)

        try:
            (rs, rp, runp) = reflectivity_fresnel(refraction_index_beta=beta, refraction_index_delta=delta, \
                                                  grazing_angle_mrad=angle, roughness_rms_A=roughness, \
                                                  photon_energy_ev=e)
        except:
            raise Exception("Failed to run reflectivity_fresnel")

        for j, energy in enumerate(e):
            transmittance[j, :, :] = rs[j]

        # rotation
        if defection == 0:  # horizontally deflecting
            H = h / numpy.sin(angle * 1e-3)
        elif defection == 1:  # vertically deflecting
            V = v / numpy.sin(angle * 1e-3)

        # size
        absorbance = 1.0 - transmittance

        if gapshape == 0:
            h_indices_bad = numpy.where(numpy.abs(H - hgapcenter) > (0.5 * hgap))
            if len(h_indices_bad) > 0:
                transmittance[:, h_indices_bad, :] = 0.0
                absorbance[:, h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V - vgapcenter) > (0.5 * vgap))
            if len(v_indices_bad) > 0:
                transmittance[:, :, v_indices_bad] = 0.0
                absorbance[:, :, v_indices_bad] = 0.0
        elif gapshape == 1:  # circle
            for i in range(H.size):
                for j in range(V.size):
                    if (((H[i] - hgapcenter) / (hgap / 2)) ** 2 + ((V[j] - vgapcenter) / (vgap / 2)) ** 2) > 1:
                        transmittance[:, i, j] = 0.0
                        absorbance[:, i, j] = 0.0

    elif flags == 2:  # aperture
        if gapshape == 0:
            h_indices_bad = numpy.where(numpy.abs(H - hgapcenter) > (0.5 * hgap))
            if len(h_indices_bad) > 0:
                transmittance[:, h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V - vgapcenter) > (0.5 * vgap))
            if len(v_indices_bad) > 0:
                transmittance[:, :, v_indices_bad] = 0.0
        elif gapshape == 1:  # circle
            for i in range(H.size):
                for j in range(V.size):
                    if (((H[i] - hgapcenter) / (hgap / 2))**2 + ((V[j] - vgapcenter)/ (vgap / 2))**2) > 1:
                        transmittance[:, i, j] = 0.0

        absorbance = 1.0 - transmittance

    elif flags == 3:  # magnifier
        H = h * hmag
        V = v * vmag

        absorbance = 1.0 - transmittance

    elif flags == 4:  # rotation screen
        H = h / numpy.cos(vrot * numpy.pi / 180)
        V = v / numpy.cos(hrot * numpy.pi / 180)

        absorbance = 1.0 - transmittance

    elif flags == 5:  # thin object filter
        H = h
        V = v

        # FRONT surface
        xx, yy, zz = read_surface_file(file_name=thin_object_file)
        thick_pre = zz.T * 1e3 # im mm
        xx *= 1e3 # im mm
        yy *= 1e3 # im mm

        f = RectBivariateSpline(xx,
                                yy,
                                thick_pre)
        thick_interpolated = f(h, v)

        # outside definition (supposed centered)
        h_indices_bad = numpy.where(numpy.abs(H) > (xx.max()))
        if len(h_indices_bad) > 0:
            thick_interpolated[h_indices_bad, :] = thin_object_thickness_outside_file_area * 1e3 # in mm
        v_indices_bad = numpy.where(numpy.abs(V) > (yy.max()))
        if len(v_indices_bad) > 0:
            thick_interpolated[:, v_indices_bad] = thin_object_thickness_outside_file_area * 1e3 # in mm

        # BACK surface
        if thin_object_back_profile_flag == 0:
            thick_interpolated_back = 0.0
        elif thin_object_back_profile_flag == 1:
            xx, yy, zz = read_surface_file(file_name=thin_object_back_profile_file)
            thick_pre = zz.T * 1e3 # im mm
            xx *= 1e3 # im mm
            yy *= 1e3 # im mm

            f = RectBivariateSpline(xx,
                                    yy,
                                    thick_pre)
            thick_interpolated_back = f(h, v)

            # outside definition (supposed centered) is set to zero
            h_indices_bad = numpy.where(numpy.abs(H) > (xx.max()))
            if len(h_indices_bad) > 0:
                thick_interpolated_back[h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V) > (yy.max()))
            if len(v_indices_bad) > 0:
                thick_interpolated_back[:, v_indices_bad] = 0.0

        # total thickness is |front - back profiles|
        thick_interpolated = numpy.abs(thick_interpolated - thick_interpolated_back)

        for j, energy in enumerate(e):
            tmp = material_constants_library.CS_Total_CP(substance, energy / 1000.0)
            transmittance[j, :, :] = numpy.exp(-tmp * dens * (thick_interpolated[:, :] / 10.0))

        absorbance = 1.0 - transmittance

    elif flags == 6:  # multilayer
        tmp = numpy.zeros(e.size)
        try:
            f = h5py.File(multilayer_file, 'r')
            density1 = f["MLayer/parameters/density1"][()]
            density2 = f["MLayer/parameters/density2"][()]
            densityS = f["MLayer/parameters/densityS"][()]
            gamma1 = numpy.array(f["MLayer/parameters/gamma1"])
            material1 = f["MLayer/parameters/material1"][()]
            material2 = f["MLayer/parameters/material2"][()]
            materialS = f["MLayer/parameters/materialS"][()]
            mlroughness1 = numpy.array(f["MLayer/parameters/mlroughness1"])
            mlroughness2 = numpy.array(f["MLayer/parameters/mlroughness2"])
            roughnessS = f["MLayer/parameters/roughnessS"][()]
            np = f["MLayer/parameters/np"][()]
            npair = f["MLayer/parameters/npair"][()]
            thick = numpy.array(f["MLayer/parameters/thick"])

            thetaN = numpy.array(f["MLayer/parameters/thetaN"])
            energyN = numpy.array(f["MLayer/parameters/energyN"])
            theta1 = numpy.array(f["MLayer/parameters/theta1"])

            f.close()

            if isinstance(material1, bytes): material1 = material1.decode("utf-8")
            if isinstance(material2, bytes): material2 = material2.decode("utf-8")
            if isinstance(materialS, bytes): materialS = materialS.decode("utf-8")

            if verbose:
                print("===== data read from file: %s ======" % multilayer_file)
                print("density1      = ", density1)
                print("density2      = ", density2)
                print("densityS      = ", densityS)
                print("gamma1        = ", gamma1)
                print("material1  (even, closer to substrte) = ", material1)
                print("material2  (odd)                      = ", material2)
                print("materialS  (substrate)                = ", materialS)
                print("mlroughness1  = ", mlroughness1)
                print("mlroughness2  = ", mlroughness2)
                print("roughnessS    = ", roughnessS)
                print("np            = ", np)
                print("npair         = ", npair)
                print("thick         = ", thick)
                print("thetaN        = ", thetaN)
                print("theta1        = ", theta1)
                print("energyN        = ", energyN)
                print("=====================================\n\n")

            out = MLayer.initialize_from_bilayer_stack(
                material_S=materialS, density_S=densityS, roughness_S=roughnessS,
                material_E=material1, density_E=density1, roughness_E=mlroughness1[0],
                material_O=material2, density_O=density2, roughness_O=mlroughness2[0],
                bilayer_pairs=np,
                bilayer_thickness=thick[0],
                bilayer_gamma=gamma1[0],
            )

            rs, rp = out.scan_energy(e, theta1=numpy.degrees(angle * 1e-3), h5file="") # result R in aplitude
            rs = numpy.abs(rs)
            rp = numpy.abs(rp)

        except:
            raise Exception("Error reading file: %s" % multilayer_file)

        if defection == 0:  # horizontally deflecting
            for j, energy in enumerate(e):
                transmittance[j, :, :] = rp[j]**2
            H = h / numpy.sin(angle * 1e-3)
        elif defection == 1:  # vertically deflecting
            for j, energy in enumerate(e):
                transmittance[j, :, :] = rs[j]**2
            V = v / numpy.sin(angle * 1e-3)

        # size
        absorbance = 1.0 - transmittance

        if gapshape == 0:
            h_indices_bad = numpy.where(numpy.abs(H - hgapcenter) > (0.5 * hgap))
            if len(h_indices_bad) > 0:
                transmittance[:, h_indices_bad, :] = 0.0
                absorbance[:, h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V - vgapcenter) > (0.5 * vgap))
            if len(v_indices_bad) > 0:
                transmittance[:, :, v_indices_bad] = 0.0
                absorbance[:, :, v_indices_bad] = 0.0
        elif gapshape == 1:  # circle
            for i in range(H.size):
                for j in range(V.size):
                    if (((H[i] - hgapcenter) / (hgap / 2)) ** 2 + ((V[j] - vgapcenter) / (vgap / 2)) ** 2) > 1:
                        transmittance[:, i, j] = 0.0
                        absorbance[:, i, j] = 0.0

    elif flags == 7:  # external reflectivity file

        try:
            a = numpy.loadtxt(external_reflectivity_file)
            energy0 = a[:, 0]
            refl0 = a[:, -1]
            refl = numpy.interp(e, energy0, refl0, left=0, right=0)
        except:
            raise Exception("Error extracting reflectivity from file: %s" % external_reflectivity_file)

        for j, energy in enumerate(e):
            transmittance[j, :, :] = refl[j]

        # rotation
        H = h / numpy.cos(vrot * numpy.pi / 180)
        V = v / numpy.cos(hrot * numpy.pi / 180)

        # size
        absorbance = 1.0 - transmittance

        if gapshape == 0:
            h_indices_bad = numpy.where(numpy.abs(H - hgapcenter) > (0.5 * hgap))
            if len(h_indices_bad) > 0:
                transmittance[:, h_indices_bad, :] = 0.0
                absorbance[:, h_indices_bad, :] = 0.0
            v_indices_bad = numpy.where(numpy.abs(V - vgapcenter) > (0.5 * vgap))
            if len(v_indices_bad) > 0:
                transmittance[:, :, v_indices_bad] = 0.0
                absorbance[:, :, v_indices_bad] = 0.0
        elif gapshape == 1:  # circle
            for i in range(H.size):
                for j in range(V.size):
                    if (((H[i] - hgapcenter) / (hgap / 2))  ** 2 + ((V[j] - vgapcenter) / (vgap / 2)) ** 2) > 1:
                        transmittance[:, i, j] = 0.0
                        absorbance[:, i, j] = 0.0
    else:
        raise NotImplementedError("Not implemented option: flags=%d" % flags)

    return transmittance, absorbance, E, H, V, txt

def apply_transmittance_to_incident_beam(transmittance, p0, e0, h0, v0,
    flags=0,
    hgap=1000.0,
    vgap=1000.0,
    hgapcenter=0.0,
    vgapcenter=0.0,
    hmag=1.0,
    vmag=1.0,
    interpolation_flag=0,
    interpolation_factor_h=1.0,
    interpolation_factor_v=1.0,
    slit_crop=0,
    ):

    p = p0.copy()
    e = e0.copy()
    h = h0.copy()
    v = v0.copy()

    # coordinates to send: the same as incident beam (perpendicular to the optical axis)
    # except for the magnifier
    if flags == 3:  # magnifier  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        h *= hmag
        v *= vmag

    p_transmitted = p * transmittance / (h[0] / h0[0]) / (v[0] / v0[0])

    if (slit_crop == 1 and flags == 2):
        print("Cropping to %g mm x %g mm" % (hgap,vgap))
        h_d = numpy.where(numpy.abs(h - hgapcenter) <= (0.5 * hgap))[0]
        v_d = numpy.where(numpy.abs(v - vgapcenter) <= (0.5 * vgap))[0]

        p_transmitted = p_transmitted[:, h_d[0]:(h_d[-1]), v_d[0]:v_d[-1]].copy()
        e = e
        h = h[h_d[0]:h_d[-1]].copy()
        v = v[v_d[0]:v_d[-1]].copy()

    if interpolation_flag == 1:

        h_old = h
        v_old = v
        p_transmitted_old = p_transmitted

        nh = int(h_old.size * interpolation_factor_h)
        nv = int(v_old.size * interpolation_factor_v)
        p_transmitted = numpy.zeros((e.size, nh, nv))

        print("Interpolating from ",p_transmitted_old.shape, " to ", p_transmitted.shape)
        h = numpy.linspace(h_old[0], h_old[-1], nh)
        v = numpy.linspace(v_old[0], v_old[-1], nv)



        for i in range(e.size):
            f = RectBivariateSpline(h_old,
                                    v_old,
                                    p_transmitted_old[i, :, :])
            p_transmitted_i = f(h, v)
            p_transmitted[i, :, :] = p_transmitted_i

    return p_transmitted, e, h, v


#
# file io
#

# copied from OASYS1
def read_surface_file(file_name, subgroup_name = "surface_file"):
    if not os.path.isfile(file_name): raise ValueError("File " + file_name + " not existing")

    file = h5py.File(file_name, 'r')
    xx = file[subgroup_name + "/X"][()]
    yy = file[subgroup_name + "/Y"][()]
    zz = file[subgroup_name + "/Z"][()]

    return xx, yy, zz

def load_radiation_from_h5file(file_h5, subtitle="XOPPY_RADIATION"):

    hf = h5py.File(file_h5, 'r')

    if not subtitle in hf:
        raise Exception("XOPPY_RADIATION not found in h5 file %s"%file_h5)

    try:
        p = hf[subtitle + "/Radiation/stack_data"][:]
        e = hf[subtitle + "/Radiation/axis0"][:]
        h = hf[subtitle + "/Radiation/axis1"][:]
        v = hf[subtitle + "/Radiation/axis2"][:]
    except:
        raise Exception("Error reading h5 file %s \n"%file_h5 + "\n" + str(e))

    code = "unknown"

    try:
        if hf[subtitle + "/parameters/METHOD"][()] == 0:
            code = 'US'
        elif hf[subtitle + "/parameters/METHOD"][()] == 1:
            code = 'URGENT'
        elif hf[subtitle + "/parameters/METHOD"][()] == 2:
            code = 'SRW'
        elif hf[subtitle + "/parameters/METHOD"][()] == 3:
            code = 'pySRU'
    except:
        pass

    hf.close()

    return e, h, v, p, code


def write_radiation_to_h5file(e,h,v,p,
                       creator="xoppy",
                       h5_file="wiggler_radiation.h5",
                       h5_entry_name="XOPPY_RADIATION",
                       h5_initialize=True,
                       h5_parameters=None,
                       ):

    if h5_initialize:
        h5w = H5SimpleWriter.initialize_file(h5_file,creator=creator)
    else:
        h5w = H5SimpleWriter(h5_file,None)
    h5w.create_entry(h5_entry_name,nx_default=None)
    h5w.add_stack(e,h,v,p,stack_name="Radiation",entry_name=h5_entry_name,
        title_0="Photon energy [eV]",
        title_1="X gap [mm]",
        title_2="Y gap [mm]")
    h5w.create_entry("parameters",root_entry=h5_entry_name,nx_default=None)
    if h5_parameters is not None:
        for key in h5_parameters.keys():
            h5w.add_key(key,h5_parameters[key], entry_name=h5_entry_name+"/parameters")
    print("File written to disk: %s"%h5_file)


def write_txt_file(calculated_data, input_beam_content, filename="tmp.txt", method="3columns"):

    p0, e0, h0, v0 = input_beam_content # .get_content("xoppy_data")
    transmittance, absorbance, E, H, V = calculated_data

    #
    #
    #
    p = p0.copy()
    p_spectral_power = p * codata.e * 1e3

    absorbed3d = p_spectral_power * absorbance / (H[0] / h0[0]) / (V[0] / v0[0])
    absorbed2d = numpy.trapz(absorbed3d, E, axis=0)

    f = open(filename, 'w')
    if method == "3columns":
        for i in range(H.size):
            for j in range(V.size):
                f.write("%g  %g  %g\n" % (H[i]*1e-3, V[i]*1e-3, absorbed2d[i,j]*1e6))
    elif method == "matrix":
        f.write("%10.5g" % 0)
        for i in range(H.size):
            f.write(", %10.5g" % (H[i] * 1e-3))
        f.write("\n")

        for j in range(V.size):
                f.write("%10.5g" % (V[j] * 1e-3))
                for i in range(H.size):
                    f.write(", %10.5g" % (absorbed2d[i,j] * 1e6))
                f.write("\n")
    else:
        raise Exception("File type not understood.")
    f.close()

    print("File written to disk: %s" % filename)


def write_h5_file(calculated_data, input_beam_content, filename="tmp.txt",EL1_FLAG=1,EL1_HMAG=1.0,EL1_VMAG=1.0):

    p0, e0, h0, v0 = input_beam_content #.get_content("xoppy_data")
    transmittance, absorbance, E, H, V = calculated_data

    #
    #
    #
    p = p0.copy()
    e = e0.copy()
    h = h0.copy()
    v = v0.copy()
    p_spectral_power = p * codata.e * 1e3

    try:
        h5w = H5SimpleWriter.initialize_file(filename, creator="power3Dcomponent.py")
        txt = "\n\n\n"
        txt += info_total_power(p, e, v, h, transmittance, absorbance, EL1_FLAG=EL1_FLAG)
        h5w.add_key("info", txt, entry_name=None)
    except:
        print("ERROR writing h5 file (info)")


    try:
        #
        # source
        #
        entry_name = "source"

        h5w.create_entry(entry_name, nx_default=None)

        h5w.add_stack(e, h, v, p, stack_name="Radiation stack", entry_name=entry_name,
                      title_0="Photon energy [eV]",
                      title_1="X [mm] (normal to beam)",
                      title_2="Y [mm] (normal to beam)")

        h5w.add_image(numpy.trapz(p_spectral_power, E, axis=0) , H, V,
                      image_name="Power Density", entry_name=entry_name,
                      title_x="X [mm] (normal to beam)",
                      title_y="Y [mm] (normal to beam)")

        h5w.add_dataset(E, numpy.trapz(numpy.trapz(p_spectral_power, v, axis=2), h, axis=1),
                        entry_name=entry_name, dataset_name="Spectral power",
                        title_x="Photon Energy [eV]",
                        title_y="Spectral density [W/eV]")

    except:
        print("ERROR writing h5 file (source)")

    try:
        #
        # optical element
        #
        entry_name = "optical_element"

        h5w.create_entry(entry_name, nx_default=None)

        h5w.add_stack(E, H, V, transmittance, stack_name="Transmittance stack", entry_name=entry_name,
                      title_0="Photon energy [eV]",
                      title_1="X [mm] (o.e. coordinates)",
                      title_2="Y [mm] (o.e. coordinates)")

        absorbed = p_spectral_power * absorbance / (H[0] / h0[0]) / (V[0] / v0[0])
        h5w.add_image(numpy.trapz(absorbed, E, axis=0), H, V,
                      image_name="Absorbed Power Density on Element", entry_name=entry_name,
                      title_x="X [mm] (o.e. coordinates)",
                      title_y="Y [mm] (o.e. coordinates)")

        h5w.add_dataset(E, numpy.trapz(numpy.trapz(absorbed, v, axis=2), h, axis=1),
                        entry_name=entry_name, dataset_name="Absorbed Spectral Power",
                        title_x="Photon Energy [eV]",
                        title_y="Spectral density [W/eV]")

        #
        # transmitted
        #

        # coordinates to send: the same as incident beam (perpendicular to the optical axis)
        # except for the magnifier
        if EL1_FLAG == 3:  # magnifier <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            h *= EL1_HMAG
            v *= EL1_VMAG

        transmitted = p_spectral_power * transmittance / (h[0] / h0[0]) / (v[0] / v0[0])
        h5w.add_image(numpy.trapz(transmitted, E, axis=0), h, v,
                      image_name="Transmitted Power Density on Element", entry_name=entry_name,
                      title_x="X [mm] (normal to beam)",
                      title_y="Y [mm] (normal to beam)")

        h5w.add_dataset(E, numpy.trapz(numpy.trapz(transmitted, v, axis=2), h, axis=1),
                        entry_name=entry_name, dataset_name="Transmitted Spectral Power",
                        title_x="Photon Energy [eV]",
                        title_y="Spectral density [W/eV]")
    except:
        print("ERROR writing h5 file (optical element)")

    try:
        h5_entry_name = "XOPPY_RADIATION"

        h5w.create_entry(h5_entry_name,nx_default=None)
        h5w.add_stack(e, h, v, transmitted,stack_name="Radiation",entry_name=h5_entry_name,
            title_0="Photon energy [eV]",
            title_1="X gap [mm]",
            title_2="Y gap [mm]")
    except:
        print("ERROR writing h5 file (adding XOPPY_RADIATION)")

    print("File written to disk: %s" % filename)

#
# info
#
def info_total_power(p, e, v, h, transmittance, absorbance, EL1_FLAG=1):
    txt = ""
    txt += "\n\n\n"
    power_input = integral_3d(p, e, h, v, method=0) * codata.e * 1e3
    txt += '      Input beam power: %f W\n'%(power_input)

    power_transmitted = integral_3d(p * transmittance, e, h, v, method=0) * codata.e * 1e3
    power_absorbed = integral_3d(p * absorbance, e, h, v, method=0) * codata.e * 1e3

    power_lost = power_input - ( power_transmitted +  power_absorbed)
    if numpy.abs( power_lost ) > 1e-9:
        txt += '      Beam power not considered (removed by o.e. acceptance): %6.3f W (accepted: %6.3f W)\n' % \
               (power_lost, power_input - power_lost)

    txt += '      Beam power absorbed by optical element: %6.3f W\n' % power_absorbed

    if EL1_FLAG == 1:
        txt += '      Beam power reflected after optical element: %6.3f W\n' % power_transmitted
    else:
        txt += '      Beam power transmitted after optical element: %6.3f W\n' % power_transmitted

    return txt

if __name__ == "__main__":
    GAPH = 0.002
    GAPV = 0.002
    HSLITPOINTS = 601
    VSLITPOINTS = 401
    PHOTONENERGYMIN = 7000.0
    PHOTONENERGYMAX = 8000.0
    PHOTONENERGYPOINTS = 20

    e0 = numpy.linspace(PHOTONENERGYMIN, PHOTONENERGYMAX, PHOTONENERGYPOINTS)
    h0 = numpy.linspace(-0.5 * GAPH, 0.5 * GAPH, HSLITPOINTS)
    v0 = numpy.linspace(-0.5 * GAPV, 0.5 * GAPV, VSLITPOINTS)



    transmittance, absorbance, E, H, V, txt  = calculate_component_absorbance_and_transmittance(
                    e0, # energy in eV
                    h0, # h in mm
                    v0, # v in mm
                    substance='Be',
                    thick=0.5,
                    angle=3.0,
                    defection=1,
                    dens='?',
                    roughness=0.0,
                    flags=6, # 0 = Filter, 2=Aperture, 5 = Thin object filter, 6=Multilayer, 7 External File
                    hgap=0.2e-3,
                    vgap=0.1e-3,
                    hgapcenter=0.1e-3,
                    vgapcenter=0.1e-3,
                    gapshape=1, # 0=rect
                    hmag=1.0,
                    vmag=1.0,
                    hrot=0.0,
                    vrot=0.0,
                    thin_object_file='/home/srio/Oasys/lens.h5',
                    thin_object_thickness_outside_file_area=163e-6,
                    thin_object_back_profile_flag=0, # 0= z=0, 1=Back profile from file z(x,y)
                    thin_object_back_profile_file='/home/srio/Oasys/lens.h5',
                    multilayer_file='/home/srio/Oasys/multilayerTiC.h5',
                    )

    from srxraylib.plot.gol import plot_image, plot

    plot(e0, transmittance[:,0,0],
         e0, absorbance[:,0,0],
         xtitle="Photon energy [eV]", legend=["Transmittance","Absorbance"], show=0)
    plot_image(transmittance[0,:,:], h0, v0,title="Transmittance at E=%g eV" % (e0[0]),
               xtitle="H [m]",ytitle="V [m]",aspect='auto')