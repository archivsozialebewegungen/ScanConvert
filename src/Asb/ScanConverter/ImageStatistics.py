'''
Created on 11.04.2021

@author: michael
'''
from PIL import Image
from numpy import uint32
import numpy
from Asb.ScanConverter.DeveloperTools import DeveloperTools
from injector import singleton

@singleton
class ImageStatistics:
    
    def __init__(self):
        
        self.dev_tools = DeveloperTools()
    
    def advice_sharpening(self, img: Image) -> bool:
        
        black_spreading = self._calculate_black_spreading(img)
        
        return black_spreading < 0.375
    
    def advice_more_contrast(self, img: Image) -> bool:
         
        black_spreading = self._calculate_black_spreading(img)
        return black_spreading > 1
    
    def _calculate_black_spreading(self, img: Image) -> float:
        
        histogram = img.histogram()
        
        dark_values = numpy.array(histogram[:50], dtype=uint32)
        
        #self.dev_tools.plot_values(dark_values)
        
        average = numpy.average(dark_values)
        standard_deviance = numpy.std(dark_values)
        
        normalized_deviance = standard_deviance / average
        print("Black spreading: %f" % (1 / normalized_deviance))
        return 1 / normalized_deviance