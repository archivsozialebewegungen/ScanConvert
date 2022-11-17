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
from pytorch_pretrained_bert import BertTokenizer, BertForMaskedLM
from difflib import SequenceMatcher
import spacy
import contextualSpellCheck

@singleton
class OcrPreprocessor:
    
    @inject
    def __init__(self, image_operations: ImageFileOperations,
                 image_statistics: ImageStatistics):
        
        self.image_operations = image_operations
        self.image_statistics = image_statistics
    
    def preprocess(self, img: Image) -> Image:
        
        if self.needs_more_contrast(img):
            img = self.image_operations.enhance_contrast(img)
            img = self.image_operations.apply_dilation(img)
        if self.image_statistics.advice_sharpening(img):
            img = self.image_operations.sharpen(img)
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
        
        return text
        
    def remove_hyphenation(self, text: str) -> str:
        
        return re.sub("(?<=\w)-\s+", '', text, flags=re.DOTALL)

    def split_into_sentences(self, text: str) -> [str]:

        return [ sentence.strip() for sentence in re.split("(?<=\.\s)", text, flags=re.DOTALL) if sentence.strip() != '']

    def fix_word_via_spellchecker_and_bert(self, text: str) -> str:
        
        nlp = spacy.load("de_dep_news_trf")
        contextualSpellCheck.add_to_pipe(nlp)
        doc = nlp(text)

        if doc._.performed_spellCheck:
            return doc._.outcome_spellCheck 
        
        return text
    
    def fix_word_via_spellchecker_and_bert_old(self, text: str) -> str:
        
        suggested_corrections = self.get_suggested_corrections(text)
        # replace incorrect words with [MASK]
        for word in suggested_corrections.keys():
            text = text.replace(word, '[MASK]')

        tokenized_text = self.tokenizer.tokenize(text)
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)
        maskids = [i for i, e in enumerate(tokenized_text) if e == '[MASK]']

        # Create the segments tensors
        segs = [i for i, e in enumerate(tokenized_text) if e == "."]
        segments_ids=[]
        prev=-1
        for k, s in enumerate(segs):
            segments_ids = segments_ids + [k] * (s-prev)
            prev=s
        trailing = len(tokenized_text) - len(segments_ids)
        last_id = len(segs)
        segments_ids = segments_ids + [last_id] * trailing
         
        segments_tensors = torch.tensor([segments_ids])
        # prepare Torch inputs 
        tokens_tensor = torch.tensor([indexed_tokens])
        # Load pre-trained model
        model = BertForMaskedLM.from_pretrained('bert-base-multilingual-cased')
        # Predict all tokens
        with torch.no_grad():
            predictions = model(tokens_tensor, segments_tensors)
        
        return self.predict_words(text, predictions, suggested_corrections, maskids)
        
    def get_suggested_corrections(self, text: str):

        preprocessed = self.preprocess_text(text)

        spell_checker = SpellChecker("de_DE")
        words = preprocessed.split()
        
        suggestions = {}
        for word in words:
            if not spell_checker.check(word):
                suggestions[word] = spell_checker.suggest(word)
                
        return suggestions
    
    def predict_words(self, text_original, predictions, suggestedwords, maskids):
        
        for i in range(len(maskids)):
            preds = torch.topk(predictions[0, maskids[i]], k=50) 
            indices = preds.indices.tolist()
            list1 = self.tokenizer.convert_ids_to_tokens(indices)
            list2 = suggestedwords[i]
            simmax=0
            predicted_token=''
            for word1 in list1:
                for word2 in list2:
                    s = SequenceMatcher(None, word1, word2).ratio()
                    if s is not None and s > simmax:
                        simmax = s
                        predicted_token = word1
            text_original = text_original.replace('[MASK]', predicted_token, 1)
        return text_original

    def preprocess_text(self, text: str) -> str:

        whitespace_pattern = re.compile("\s+", re.DOTALL)
        text = whitespace_pattern.sub(" ", text)
        
        punctuation_pattern = re.compile("\s*([.,:!\-()*\"'])\s*")
        text = punctuation_pattern.sub(r" \1 ", text)
        
        return text

    def _get_tokenizer(self):
        
        if self._tokenizer is None:
            self._tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased', do_lower_case=False)
            
        return self._tokenizer


    tokenizer = property(_get_tokenizer)
    
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