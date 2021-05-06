'''
Created on 05.04.2021

@author: michael
'''
from PIL import Image, ImageFilter
import re
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
import numpy
from Asb.ScanConverter.ImageTypeConversion import pil_to_ndarray
import pytesseract
from injector import singleton, inject
from Asb.ScanConverter.ImageStatistics import ImageStatistics
from enchant.checker import SpellChecker
import torch
from transformers import BertTokenizer, BertModel
import Levenshtein

@singleton
class OcrPreprocessor:
    
    @inject
    def __init__(self, image_operations: ImageFileOperations,
                 image_statistics: ImageStatistics):
        
        self.image_operations = image_operations
        self.image_statistics = image_statistics
    
    def preprocess(self, img: Image) -> Image:
        
        #if self.needs_more_contrast(img):
        #    img = self.image_operations.enhance_contrast(img)
        #    img = self.image_operations.apply_dilation(img)
        #if self.image_statistics.advice_sharpening(img):
        #    img = self.image_operations.sharpen(img)
        img = img.convert('L')
        img = self.image_operations.binarization_sauvola(img)
        # At the moment denoising produces more harm with vanishing dots
        # than that it helps OCR
        #img = self.image_operations.denoise(img)
        return img

    def try_normalization(self, img: Image):
        
        if self.image_operations.get_resolution(img) == (300, 300):
            return img
        old_ocr_confidence = AltoPageLayout(img).confidence
        new_img = self.image_operations.change_resolution(img, 300)
        new_ocr_confidence = AltoPageLayout(new_img).confidence
        if new_ocr_confidence > old_ocr_confidence:
            print("Changed image resolution to 300.")
            return new_img
        else:
            print("No resolution change.")
            return img
   
    def try_enhancement(self, img: Image, method):

        old_ocr_confidence = AltoPageLayout(img).confidence
        new_img = method(img)
        new_ocr_confidence = AltoPageLayout(new_img).confidence
        if new_ocr_confidence > old_ocr_confidence:
            print("Applied %s." % method.__name__)
            return new_img
        else:
            print("Did not apply %s.", method.__name__)
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

@singleton    
class OcrPostprocessor:
    
    @inject
    def __init__(self):
        
        self._tokenizer = None
        
    def postprocess(self, text:str) -> str:

        text = self.remove_hyphenation(text)
        text = self.normalize_spaces(text)
        
        return text
    
    def normalize_spaces(self, text: str) -> str:

        return re.sub("\s+", " ", text, flags=re.DOTALL)
        
    def remove_hyphenation(self, text: str) -> str:
        
        text = re.sub("(?<=\w)-\s*\n\s*(?=[a-z])", '', text, flags=re.DOTALL)
        text = re.sub("(?<=\w)-\s*\n\s*", '-', text, flags=re.DOTALL)
        return text
    
    
@singleton
class OcrRunner:
    
    @inject
    def __init__(self, preprocessor: OcrPreprocessor, postprocessor: OcrPostprocessor):
        
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        
    def get_text(self, img: Image, language: str='deu') -> str:
        
        bin_img = self.preprocessor.preprocess(img)
        text = pytesseract.image_to_string(bin_img, lang=language)
        return self.postprocessor.postprocess(text)
    
    def get_alto_layout(self, img: Image, language: str='deu'):
        
        return AltoPageLayout(self.preprocessor.preprocess(img), language=language)
    
    def get_hocr(self, img: Image, language: str='deu'):
        
        return pytesseract.image_to_pdf_or_hocr(self.preprocessor.preprocess(img), extension='hocr', lang=language)