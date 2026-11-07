#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# loads native/blind_check, build it with native/build.sh
# ctypes lets the other threads run while the c++ code works
import ctypes
import os

name = "blind_check.so"
if os.name == "nt":
    name = "blind_check.dll"
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "native", name)

lib = None
if os.path.exists(PATH):
    try:
        lib = ctypes.CDLL(PATH)
        lib.blind_numbers.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.blind_numbers.restype = ctypes.c_int
    except OSError:
        print("blind check library would not load, using opencv")
        lib = None


def available():
    return lib != None


# brightness and sharpness of a bgr image
def numbers(img):
    bright = ctypes.c_double()
    sharp = ctypes.c_double()
    bad = lib.blind_numbers(img.ctypes.data, img.shape[0], img.shape[1], img.strides[0],
                            ctypes.byref(bright), ctypes.byref(sharp))
    if bad != 0:
        return None
    return bright.value, sharp.value
