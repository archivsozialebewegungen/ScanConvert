'''
Created on 10.08.2021

@author: michael
'''
from Asb.ScanConverter.Services import GraphicFileInfo, COLOR, COLOR_WITH_ALPHA,\
    GRAYSCALE
from PIL import Image, ImageOps
import numpy
from skimage.filters.thresholding import threshold_sauvola
from injector import singleton

@singleton
class FilterChainGenerator(object):
    '''
    The idea is, that we radically separate the
    conversions of the images from the conversion
    for OCR. This filter chain mechanism is intended
    to preprocess the images in various ways to optimize
    the input for OCR.
    
    In the first implementation we just binarize the
    images, but more enhancement techniques like
    denoising, sharpening, contrast etc. will follow.
    
    Which filters will be applied will be determined
    in this generator that may perform different analytical
    tasks on the graphics file. We do not strive for
    performance, but for quality.
    '''

    def generate_filter_chain(self, img: Image):
        
        filter_chain = FilterChain()
        if img.mode == "RGB" or img.mode == "RGBA":  # COLOR
            filter_chain.append(ColorToGrayFilter())
            filter_chain.append(GrayToBWFilter())
        elif img.mode == "L":                       # GRAYSCALE
            filter_chain.append(GrayToBWFilter())
        elif img.mode == "1":                        # BW  
            pass
        else:
            raise Exception("Don't know how to handle image mode $s!" % img.mode)
        
        return filter_chain

class FilterChain:
    
    def __init__(self):
        
        self.filters = []
        
    def append(self, img_filter):
        
        self.filters.append(img_filter)
        
    def apply(self, img):
        
        for img_filter in self.filters:
            img = img_filter.apply(img)
            
        return img

class ColorToGrayFilter:
    
    def apply(self, img: Image):
        
        return ImageOps.grayscale(img)
    
class GrayToBWFilter:
    
    def apply(self, img: Image):
        
        in_array = numpy.array(img)
        mask = threshold_sauvola(in_array)
        out_array = in_array > mask
        return Image.fromarray(out_array)
