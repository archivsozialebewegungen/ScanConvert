'''
Created on 05.05.2021

@author: michael
'''

from PIL import Image, ImageOps
import numpy
from Asb.ScanConverter.ImageTypeConversion import ndarray_to_pil, pil_to_ndarray
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
from injector import singleton
import cv2
from skimage.filters.thresholding import threshold_otsu

@singleton
class DenoiseService:
    
    removed_dots_words = ['fur', 'uber']
    
    def denoise(self, img: Image) -> Image:
        '''
        This is quite complicated. We want to remove small speckles, but we do
        not want to remove punktuation marks or dots on characters like i or ä.
        So first we need to determine, if denoising is relevant at all. This
        will be determined in _is_denoise_necessary. And if it is, we use
        _determine_denoise_threshold to determine the size of legitimate dots
        and stay well under this size.
        '''
        
        no_of_components, labels, sizes = self._connected_components_with_stats(img)

        if not self._is_denoise_necessary(no_of_components, sizes):
            return img
        
        threshold = self._determine_denoise_threshold(img)

        bw_new = numpy.ones((labels.shape), dtype=numpy.bool)
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] > threshold:
                bw_new[labels == shape_identifier] = 0
        return ndarray_to_pil(bw_new, img.info['dpi'])

    def _binarization_otsu(self, img) -> Image:
        '''
        Wrapper around the cv2 implementation
        '''

        if img.mode != "1" and img.mode != "L":
            img = img.convert("L")
        
        in_array = numpy.array(img)
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        return ndarray_to_pil(out_array, img.info['dpi'])

    def _connected_components_with_stats(self, img: Image):
        '''
        Just a wrapper around the cv2 method.
        '''

        if img.mode != "1":
            raise Exception("Please call the connected_components method only on binary images!")

        inverted = ImageOps.invert(img.convert("RGB"))
        ndarray = numpy.array(inverted.convert("1"), dtype=numpy.uint8)
        no_of_components, labels, stats, centroids = cv2.connectedComponentsWithStats(ndarray, connectivity=8)
        sizes = stats[:, cv2.CC_STAT_AREA]
        
        # Leave out background 
        return no_of_components, labels, sizes

    def _are_dots_missing(self, img: Image) -> bool:
        '''
        The usage of this method does not improve ocr. Some missing dots
        do less harm than leaving a lot of noise on the pages
        '''
        
        alto_layout = AltoPageLayout(img)
        
        for string_element in alto_layout.get_all_strings():
            
            word = string_element.get_text()
            if word in self.removed_dots_words:
                for bad_word in self.removed_dots_words:
                    if bad_word == word:
                        print("Found missing dot in %s" % bad_word)
                return True
            if 'ı' in word:
                print("Found missing dot in %s" % word)
                return True
            
        return False
     
    def _is_denoise_necessary(self, no_of_components, sizes):
        '''
        We look for very small speckles in the image (size < 4),
        and if they constitute 10% or more of all shapes,
        we should denoise.
        '''
        small_shapes = 0
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] < 4:
                small_shapes += 1
        return not small_shapes / (no_of_components - 1) < 0.1
    
    def _determine_denoise_threshold(self, img: Image) -> int:
        '''
        This one uses actual dot sizes from the document
        to calculate the threshold
        '''
        
        computed_dot_size = self._determine_dot_size(img)
        # Apply a safety margin
        threshold = int(computed_dot_size * 0.90)
        print("Using denoise threshold %d" % threshold)
        return threshold
    
    def _determine_denoise_threshold2(self, img: Image) -> int:
        '''
        This implementation uses the text height to determine
        the size of dots (for i or umlauts etc.) that we do not
        want do remove.
        '''
        
        textheight = AltoPageLayout(img).get_median_text_height()
        shape_radius = textheight / 18
        return int(shape_radius * shape_radius * 3.14)

    def _determine_dot_size(self, img: Image):
        '''
        This uses detected text snippets that contains dots.
        The reasoning: We know which characters to expect, so
        we also know to expect n shapes in corresponding the graphic
        snippet. Since the dot is the smallest shape that is
        legitimate, we sort the sizes and take the n-th shape
        size from the end of the list. And because this is not
        perfect, we do this for all text snippets with dots and
        take the median dot size.
        '''
        
        ndarray = pil_to_ndarray(img)
        
        bin_image = self._binarization_otsu(img)
        alto_layout = AltoPageLayout(bin_image)
        
        dotsizes = []
        for text_string in alto_layout.get_all_strings():
            if text_string.is_string_with_dots():
                x1, y1, x2, y2 = text_string.get_bounding_box()
                expected_no_of_shapes = text_string.get_number_of_shapes()
                no_of_components, labels, sizes = self._connected_components_with_stats(Image.fromarray(ndarray[y1:y2, x1:x2]))
                size_values = []
                for shape_identifier in range(1, no_of_components):
                    size_values.append(sizes[shape_identifier])
                size_values = numpy.sort(size_values)
                if len(size_values) < expected_no_of_shapes:
                    continue
                dotsizes.append(size_values[-1 * expected_no_of_shapes])
        if len(dotsizes) > 0:
            return numpy.median(dotsizes)
        else:        
            return 13
    
