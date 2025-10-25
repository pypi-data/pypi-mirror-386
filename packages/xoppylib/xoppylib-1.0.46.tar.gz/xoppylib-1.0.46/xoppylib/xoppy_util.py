import sys, os, numpy, platform, six

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib import figure as matfig
    import pylab
except ImportError:
    print(sys.exc_info()[1])
    pass

from dabax.dabax_xraylib import DabaxXraylib
try: import xraylib
except: pass

import scipy.constants as codata

def package_dirname(package):
    """Return the directory path where package is located.

    """
    if isinstance(package, six.string_types):
        package = __import__(package, fromlist=[""])
    filename = package.__file__
    dirname = os.path.dirname(filename)
    return dirname

class locations:
    @classmethod
    def home_bin(cls):
        if platform.system() == "Windows":
            return package_dirname("xoppylib") + "\\bin\\windows\\"
        else:
            return package_dirname("xoppylib") + "/bin/" + str(sys.platform) + "/"

    @classmethod
    def home_doc(cls):
        if platform.system() == "Windows":
            return package_dirname("xoppylib") + "\\doc_txt/"
        else:
            return package_dirname("xoppylib") + "/doc_txt/"

    @classmethod
    def home_data(cls):
        if platform.system() == "Windows":
            return package_dirname("xoppylib") + "\\data/"
        else:
            return package_dirname("xoppylib") + "/data/"

    @classmethod
    def home_bin_run(cls):
        return os.getcwd()


# TODO: to be removed, only used in xcrystal
class XoppyPhysics:

    ######################################
    # FROM NIST
    codata_h  = codata.h # numpy.array(6.62606957e-34)
    codata_ec = codata.e # numpy.array(1.602176565e-19)
    codata_c  = codata.c # numpy.array(299792458.0)
    ######################################

    A2EV = (codata_h*codata_c/codata_ec)*1e+10
    K2EV = 2*numpy.pi/(codata_h*codata_c/codata_ec*1e+2)

    @classmethod
    def getWavelengthFromEnergy(cls, energy): #in eV
        return cls.A2EV/energy # in Angstrom

    @classmethod
    def getEnergyFromWavelength(cls, wavelength): # in Angstrom
        return cls.A2EV/wavelength # in eV

    @classmethod
    def getMaterialDensity(cls, material_formula):
        if material_formula is None: return 0.0
        if str(material_formula.strip()) == "": return 0.0

        try:    material_constants_library = xraylib
        except: material_constants_library = DabaxXraylib()

        try:
            compoundData = material_constants_library.CompoundParser(material_formula)

            if compoundData["nElements"] == 1:
                return material_constants_library.ElementDensity(compoundData["Elements"][0])
            else:
                return 0.0
        except:
            return 0.0
