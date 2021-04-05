'''
Created on 05.04.2021

@author: michael
'''
from PIL import Image
import re
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
import numpy
from Asb.ScanConverter.ImageTypeConversion import pil_to_ndarray
import pytesseract

class OcrPreprocessor:
    
    def __init__(self, image_operations: ImageFileOperations):
        
        self.image_operations = image_operations
    
    def preprocess(self, img: Image) -> Image:
        
        if self.needs_more_contrast(img):
            img = self.image_operations.enhance_contrast(img)
            img = self.image_operations.apply_dilation(img)
        img = img.convert('L')
        img = self.image_operations.binarization_sauvola(img)
        img = self.image_operations.denoise(img)
        
        return img

    def needs_more_contrast(self, img: Image) -> bool:
        '''
        This is quite experimental. First we look for a text area
        in the image that has sufficient size.
        Then we calculate the mean and the standard deviation of the
        darkest pixel value (0-48) and put them into relation.
        If this value is smaller than 2 we assume that the values
        are spread out more and we need more contrast.
        
        Another possibility would be to normalize the histogram
        depending of the size of the text area and define a threshold
        for the standard deviation.
        '''
        
        page_layout = AltoPageLayout(img)
        coordinates = page_layout.get_big_text_block_coordinates()
        
        textblock = img.convert(mode='L').crop(coordinates)
        
        histogram = numpy.histogram(pil_to_ndarray(textblock), bins=256)
        mean = numpy.mean(histogram[0][:48])
        standard_deviation = numpy.std(histogram[0][:48])
        return standard_deviation / mean < 2
    
class OcrPostprocessor:
    
    def postprocess(self, text:str) -> str:

        text = self.remove_hyphenation(text)
        
        return text
        
    def remove_hyphenation(self, text: str) -> str:
        
        return re.sub("(?<=\w)-\s+", '', text, flags=re.DOTALL)

class OcrRunner:
    
    def __init__(self, preprocessor: OcrPreprocessor, postprocessor: OcrPostprocessor):
        
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        
    def get_text(self, img: Image, language: str='deu') -> str:
        
        bin_img = self.preprocessor.preprocess(img)
        text = pytesseract.image_to_string(bin_img, lang=language)
        return self.postprocessor.postprocess(text)
    
    def get_alto_layout(self, img: Image, language: str='deu'):
        
        return AltoPageLayout(self.preprocessor.preprocess(img), language=language)