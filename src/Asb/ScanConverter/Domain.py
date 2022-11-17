'''
Created on 04.07.2022

@author: michael
'''
from PIL import Image
import numpy
from numpy import ndarray, dtype

BW = "Schwarz-Weiß"
GRAYSCALE = "Graustufen"
COLOR = "Farbe"

class UnsupportedScanFileError(Exception):
    
    pass

class MissingResolutionInfoError(UnsupportedScanFileError):
    
    pass

class ResolutionMismatchError(UnsupportedScanFileError):
    
    pass

class UnsupportedModeError(UnsupportedScanFileError):
    
    pass

class IllegalPageRequest(Exception):
    
    pass

class Region(object):
    '''
    Describes a distinct region within a scan that may be treated
    differently.
    '''


    def __init__(self, x: int, y: int, width: int, height: int):
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
class AbstractImageObject(object):

    modes = {"1": BW, "L": GRAYSCALE, "RGB": COLOR}
    
    def __init__(self):
        
        self.width = 0
        self.height = 0
        self.resolution = 0
        self.mode = None

class Page(AbstractImageObject):

    def __init__(self, data: ndarray, resolution: int):

        super().__init__()
        self.data = data 
        self.resolution = resolution
        if self.data.ndim == 3:
            self.mode = COLOR
            self.width, self.height, rgb = self.data.shape
        else:
            #if self.data.dtype == dtype.
            self.width, self.height = self.data.shape
    
    
class Scan(AbstractImageObject):
    
    
    def __init__(self, filename: str):

        super().__init__()
        
        self.filename = filename
        self.page_nos = []
        self._init_scan_parameters()
 
    def get_page(self, page_no: int) -> Page:
        
        if not page_no in self.page_nos:
            raise IllegalPageRequest()
        
        nd_array = numpy.array(Image.open(self.filename)) 
        
    def _init_scan_parameters(self):
        
        pil_image = Image.open(self.filename)
        self.resolution = self._get_resolution(pil_image)
        self.mode = self._get_mode(pil_image)
        self.width, self.height = self._get_dimensions(pil_image)  
        
    def _get_resolution(self, img: Image) -> int:
        
        if not 'dpi' in img.info:
            raise MissingResolutionInfoError()
        
        xres, yres = img.info['dpi']
        if xres == 1 or yres == 1:
            raise MissingResolutionInfoError()
        
        if xres != yres:
            raise ResolutionMismatchError()
        
        return xres
    
    def _get_mode(self, img: Image):

        if img.mode in self.modes:
            return self.modes[img.mode]
        
        print(img.mode)
        raise UnsupportedModeError()
    
    def _get_dimensions(self, img: Image):
        
        return img.width, img.height