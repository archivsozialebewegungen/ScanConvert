'''
Created on 29.03.2021

@author: michael
'''
from Asb.ScanConverter.ImageTypeConversion import ndarray_to_pil, \
    pil_to_native_cv2image, native_cv2image_to_pil, pil_to_rgb_cv2image, \
    rgb_cv2image_to_pil, pil_to_ndarray
from PIL import Image, ImageOps, ImageFilter
from injector import singleton
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola
import cv2
import numpy
import pytesseract
import re
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout

class MissingResolutionInfo(Exception):
    
    pass

    
@singleton
class ImageFileOperations:
    '''
    This class is a collection of common image manipulation
    methods, mostly wrappers around different implementation
    from PIL, ski, open CV, numpy to have a common interface that
    works with PIL images.
    TODO: Keep resolution information when using numpy / cv2.
    '''
    
    def __init__(self):
        
        self.dilation_kernel = numpy.ones((2, 2), 'uint8')
        self.erosion_kernel = numpy.ones((2, 2), 'uint8')
        
    def load_image(self, filename: str) -> Image:
        
        return Image.open(filename)
    
    def save_image(self, img: Image, filename: str):
        
        if filename[-4:] == '.tif':
            img.save(filename, compression="tiff_deflate", dpi=self.get_resolution(img))
        else:
            img.save(filename, dpi=self.get_resolution(img))
            
    def get_resolution(self, img: Image) -> (int,):
        
        if not 'dpi' in img.info:
            raise MissingResolutionInfo()
        
        xres, yres = img.info['dpi']
        if xres == 1 or yres == 1:
            raise MissingResolutionInfo()
        
        return xres, yres
     
    def sharpen(self, img: Image) -> Image:
        
        return img.filter(ImageFilter.SHARPEN)   
    
    def enhance_contrast(self, img: Image) -> Image:
        '''
        A wrapper around the cv2 implementation. This is just
        code lifted from stackoverflow. I have not the slightest
        idea how it works, but it works.
        '''
        if img.mode == '1' or img.mode == "L":
            cv2_img = pil_to_native_cv2image(img.convert("RGB"))
        else:
            cv2_img = pil_to_native_cv2image(img)

        #-----Converting image to LAB Color model----------------------------------- 
        lab= cv2.cvtColor(cv2_img, cv2.COLOR_BGR2LAB)
        #-----Splitting the LAB image to different channels-------------------------
        l, a, b = cv2.split(lab)
        #-----Applying CLAHE to L-channel-------------------------------------------
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        #-----Merge the CLAHE enhanced L-channel with the a and b channel-----------
        limg = cv2.merge((cl,a,b))
        #-----Converting image from LAB Color model to RGB model--------------------
        return native_cv2image_to_pil(cv2.cvtColor(limg, cv2.COLOR_LAB2BGR), self.get_resolution(img))
    
    def apply_dilation(self, img: Image):
        '''
        A wrapper around the cv2 implementation
        '''
        
        cv2_img = pil_to_rgb_cv2image(img)
        
        dilated = cv2.dilate(cv2_img, self.dilation_kernel, iterations=1)
        
        return rgb_cv2image_to_pil(dilated, self.get_resolution(img))
    
    def apply_erosion(self, img: Image):
        '''
        A wrapper around the cv2 implementation
        '''
        
        cv2_img = pil_to_rgb_cv2image(img)
        
        eroded = cv2.erode(cv2_img, self.erosion_kernel, iterations=1)
        
        return rgb_cv2image_to_pil(eroded, self.get_resolution(img))
        
    def detect_rotation_angle(self, img: Image):
        '''
        This uses tesseract to determine if the image
        needs rotation. Don't confuse this with deskewing.
        This is about, 90, 180 and 240 degree rotation.
        '''
        
        info = pytesseract.image_to_osd(img).replace("\n", " ")
        matcher = re.match('.*Orientation in degrees:\s*(\d+).*', info)
        if matcher is not None:
            return int(matcher.group(1))
        else:
            raise(Exception("RE is not working"))

    def rotate(self, img: Image, angle) -> Image:
        '''
        Just a wrapper around the PIL implementation
        '''
            
        return img.rotate(angle, expand=True)

    def change_resolution(self, img: Image, new_resolution) -> Image:
        '''
        TODO: This need a complete rewrite. Especially we need
        to keep the image resolution, which currently is lost on
        upscaling. Also the handling of missing dpi information
        is not very useful. Perhaps it would be better to make
        the actual resolution change dependend on a factor and
        make this signature just a wrapper around it.
        '''
        
        current_xres, current_yres = self.get_resolution(img)
        
        if current_xres == new_resolution and current_yres == new_resolution:
            return img
        
        current_width, current_height = img.size
        new_width = int(current_width * new_resolution / current_xres)
        new_height = int(current_height * new_resolution / current_yres)

        if new_width > current_width:
            scaled_img = self._scale_up(img, new_width / current_width)
        else:
            new_size = (new_width, new_height)
            scaled_img = self._scale_down(img, new_size)
            
        scaled_img.info['dpi'] = (new_resolution, new_resolution)
        return scaled_img
     
    def _scale_down(self, img: Image, new_size) -> Image:   
        '''
        Wrapper around the downscale implementation of PIL
        '''
        
        return img.resize(new_size)

    def _scale_up(self, img: Image, factor) -> Image:
        '''
        Wrapper around the cv2 implementation
        '''
        (orig_xres, orig_yres) = self.get_resolution(img)
        cv2_img = pil_to_rgb_cv2image(img)
        original_height, original_width = cv2_img.shape[:2]
        resized_image = cv2.resize(cv2_img, (int(original_width*factor), int(original_height*factor)), interpolation=cv2.INTER_CUBIC )
        return rgb_cv2image_to_pil(resized_image, (int(orig_xres * factor), int(orig_yres * factor)))

    def binarization_floyd_steinberg(self, img) -> Image:
        '''
        Wrapper around the PIL implementation
        '''
        
        # Default for PIL images convert is Floyd/Steinberg
        return img.convert("1")

    def binarization_fixed(self, img, threshold=127) -> Image:
        '''
        Wrapper around the PIL implementation
        '''

        return self.convert_to_gray(img).point(lambda v: 1 if v > threshold else 0, "1")

    def binarization_sauvola(self, img, window_size=41) -> Image:
        '''
        Wrapper around the cv2 implementation
        '''

        in_array = numpy.array(self.convert_to_gray(img))
        mask = threshold_sauvola(in_array, window_size=window_size)
        out_array = in_array > mask
        try:
            resolution = self.get_resolution(img)
        except:
            resolution = None
        return ndarray_to_pil(out_array, resolution)
    
    def binarization_otsu(self, img) -> Image:
        '''
        Wrapper around the cv2 implementation
        '''

        in_array = numpy.array(self.convert_to_gray(img))
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        try:
            resolution = self.get_resolution(img)
        except:
            resolution = None
        return ndarray_to_pil(out_array, resolution)
    
    def convert_to_gray(self, img: Image) -> Image:
        '''
        Simple wrapper around the PIL conversion routine.
        
        TODO: Look for more sophisticated methods
        to turn color images into gray ones.
        '''

        if img.mode == "1" or img.mode == "L":
            return img
        
        return img.convert("L")

    def invert(self, img: Image):
        
        ndarray = pil_to_ndarray(img)
        inverted = numpy.invert(ndarray)
        return ndarray_to_pil(inverted, self.get_resolution(img))

    def isolate_text(self, img: Image) -> Image:
        
        layout = AltoPageLayout(img)
        mask = layout.get_text_mask()
        masked_img = img.copy()
        masked_img.paste(255, (0,0,img.width, img.height), mask=mask)
        return masked_img


    def split_image(self, img: Image):
        
        width, height = img.size
        img1 = img.crop((0,0,int(width/2), height))
        img2 = img.crop((int(width/2)+1,0,width, height))
        return (img1, img2)


        



