'''
Created on 29.03.2021

@author: michael
'''
from os import path
import re
import tempfile
from xml.dom.minidom import parseString, Element

from PIL import Image, ImageOps
import cv2
from injector import singleton
from matplotlib import pyplot
from numpy import ndarray
import numpy
import pytesseract
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola


def pil_to_skimage(img: Image) -> ndarray:

    return pil_to_ndarray(img)

def skimage_to_pil(ndarray: ndarray) -> Image:
    
    return ndarray_to_pil(ndarray)

def pil_to_ndarray(img: Image) -> ndarray:
    
    return numpy.array(img)

def ndarray_to_pil(ndarray: ndarray) -> Image:
    
    return Image.fromarray(ndarray)

def pil_to_cv2image(img: Image):
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = path.join(tmpdir, "img.png") 
        img.save(tmpfile)
        cv2_image = cv2.imread(tmpfile)
        return cv2_image[..., ::-1]
    
def cv2image_to_pil(cv2_image):
    
    img = cv2_image[..., ::-1]
    return ndarray_to_pil(img[..., ::-1])

class MissingResolutionInfo(Exception):
    
    pass

class AltoPageLayout:
    
    def __init__(self, img):

        self.dom = parseString(pytesseract.image_to_alto_xml(img).decode('utf-8'))
    
    def write_to_file(self, filename):

        file = open(filename, "w")
        self.dom.writexml(file, indent="   ")
        file.close()
    
    def get_big_text_block_coordinates(self):
        
        block = self.get_big_text_block()
        hpos = block.getAttributeNode("HPOS")
        vpos = block.getAttributeNode("VPOS")
        width = block.getAttributeNode("WIDTH")
        height = block.getAttributeNode("HEIGHT")
        x1 = int(hpos.value)
        y1 = int(vpos.value)
        x2 = x1 + int(width.value)
        y2 = y1 + int(height.value)
        
        return x1, y1, x2, y2
        
    def get_layout(self):
        
        return self.dom.gmittelwertetElementsByTagName("Layout")[0]
    
    def get_first_page(self):
        
        return self.dom.getElementsByTagName("Page")[0]

    def get_big_text_block(self) -> Element:

        for i in range(0,10):
            for element in self.dom.getElementsByTagName("TextBlock"):
                width = int(element.getAttributeNode("WIDTH").value)
                height = int(element.getAttributeNode("HEIGHT").value)
                if width * height > 10000 * (10-i):
                    return element
        # Safety
        return self.dom.getElementsByTagName("TextBlock")[0]
    
@singleton
class ImageFileOperations:
    
    def enhance_contrast(self, img: Image) -> Image:
        
        #-----Reading the image-----------------------------------------------------
        cv2_img = pil_to_cv2image(img)
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
        return cv2image_to_pil(cv2.cvtColor(limg, cv2.COLOR_LAB2BGR))
    
    def detect_rotation_angle(self, img: Image):
        
        info = pytesseract.image_to_osd(img).replace("\n", " ")
        matcher = re.match('.*Orientation in degrees:\s*(\d+).*', info)
        if matcher is not None:
            return int(matcher.group(1))
        else:
            raise(Exception("RE is not working"))

    def rotate(self, img: Image, angle) -> Image:
            
        return img.rotate(angle, expand=True)

    def change_resolution(self, img: Image, new_resolution):
        
        if not 'dpi' in img.info:
            raise MissingResolutionInfo()
        
        current_xres, current_yres = img.info['dpi']
        if current_xres == 1 or current_yres == 1:
            raise MissingResolutionInfo()
        
        if current_xres == new_resolution and current_yres == new_resolution:
            return img
        
        current_width, current_height = img.size

        new_width = int(current_width * new_resolution / current_xres)
        new_height = int(current_height * new_resolution / current_yres)
        
        new_size = (new_width, new_height)
        
        return img.resize(new_size)

    def scale_up(self, img: Image, factor):
        
        cv2_img = pil_to_cv2image(img)
        original_height, original_width = cv2_img.shape[:2]
        resized_image = cv2.resize(cv2_img, (int(original_width*factor), int(original_height*factor)), interpolation=cv2.INTER_CUBIC )
        return cv2image_to_pil(resized_image)

    def binarization_floyd_steinberg(self, img):
        
        # Default for PIL images convert is Floyd/Steinberg
        return img.convert("1")

    def binarization_fixed(self, img, threshold=127):

        return img.point(lambda v: 1 if v > threshold else 0, "1")

    def binarization_otsu(self, img):

        in_array = numpy.array(img)
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        return Image.fromarray(out_array)
    
    def binarization_sauvola(self, img, window_size=41):

        in_array = numpy.array(img)
        mask = threshold_sauvola(in_array, window_size=window_size)
        out_array = in_array > mask
        return Image.fromarray(out_array)

    def denoise(self, img: Image, threshold, connectivity):
        
        if img.mode != "1":
            return img

        inverted = ImageOps.invert(img.convert("RGB"))
        
        ndarray = numpy.array(inverted.convert("1"), dtype=numpy.uint8)

        #print("Connectivity is %d" % connectivity)
        no_of_components, labels, stats, centroids = cv2.connectedComponentsWithStats(ndarray, connectivity=connectivity)
        sizes = stats[:, cv2.CC_STAT_AREA];
        #print("Found %d components" % no_of_components)

        bw_new = numpy.ones((ndarray.shape), dtype=numpy.bool)
        big_components = 0
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] > threshold:
                big_components += 1
                bw_new[labels == shape_identifier] = 0
        #print("Removed %d components" % (no_of_components - big_components))
        return Image.fromarray(bw_new)

    def show_image(self, img: Image):

        pyplot.imshow(img)
        pyplot.title('Image')
        pyplot.xticks([])
        pyplot.yticks([])
        pyplot.show()
    
    def show_image2(self, img: Image):
        
        cv2.imshow("Image", pil_to_cv2image(img))
        cv2.waitKey(0)
        cv2.destroyAllWindows()


