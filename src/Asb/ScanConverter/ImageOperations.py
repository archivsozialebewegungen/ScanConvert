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
from numpy import ndarray, median
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

class StringObject:
    
    dotted_characters = {'i': 2, 'ä': 3, 'ö': 3, 'ü': 3, 'Ä': 3, 'Ö': 3, 'Ü': 3, '.': 1, '!': 2, ':': 2, ';': 2}

    def __init__(self, stringElement: Element):
        
        self.stringElement = stringElement
    
    def is_string_with_dots(self):
        
        # Avoid strings with accented characters etc.
        empty_string = re.sub("[a-zA-ZäöüÄÖÜ.!:;]*", '', self.get_text())
        if len(empty_string) != 0:
            return False
        without_dotted = re.sub("[iäöüÄÖÜ.!:;]", '', self.get_text())
        if self.get_text() != without_dotted:
            return True
        return False
    
    def get_number_of_shapes(self):
        
        shapes = 0
        for character in self.get_text():
            if character in self.dotted_characters:
                shapes += self.dotted_characters[character]
            else:
                shapes += 1
        return shapes
        
    def get_text(self):
        
        return self.stringElement.getAttribute("CONTENT")
    
    def get_bounding_box(self):
        
        x1 = int(self.stringElement.getAttribute("HPOS"))
        y1 = int(self.stringElement.getAttribute("VPOS"))
        x2 = x1 + int(self.stringElement.getAttribute("WIDTH"))
        y2 = y1 + int(self.stringElement.getAttribute("HEIGHT"))
        return x1, y1, x2, y2

class AltoPageLayout:
    
    def __init__(self, img):

        self.dom = parseString(pytesseract.image_to_alto_xml(img).decode('utf-8'))
    
    def write_to_file(self, filename):

        file = open(filename, "w")
        self.dom.writexml(file, indent="   ")
        file.close()
    
    def getAllStrings(self) -> [StringObject]:

        strings = []
        for string in self.dom.getElementsByTagName("String"):
            strings.append(StringObject(string))
        return strings
        
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
    
    def get_median_text_height(self):
        
        heights = []
        for string in self.dom.getElementsByTagName("String"):
            heights.append(int(string.getAttribute("HEIGHT")))
        return numpy.median(heights)
        
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
    
    def __init__(self):
        
        self.dilation_kernel = numpy.ones((2, 2), 'uint8')
        self.erosion_kernel = numpy.ones((2, 2), 'uint8')
    
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
    
    def apply_dilation(self, img: Image):
        
        cv2_img = pil_to_cv2image(img)
        
        dilated = cv2.dilate(cv2_img, self.dilation_kernel, iterations=1)
        
        return cv2image_to_pil(dilated)
    
    def apply_erosion(self, img: Image):
        
        cv2_img = pil_to_cv2image(img)
        
        eroded = cv2.erode(cv2_img, self.erosion_kernel, iterations=1)
        
        return cv2image_to_pil(eroded)
        
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
            for key in img.info.keys():
                print(img.info[key])
            return img
            raise MissingResolutionInfo()
        
        current_xres, current_yres = img.info['dpi']
        if current_xres == 1 or current_yres == 1:
            for key in img.info.keys():
                print(img.info[key])
            return img
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

        return self.convert_to_gray(img).point(lambda v: 1 if v > threshold else 0, "1")

    def binarization_otsu(self, img):

        in_array = numpy.array(self.convert_to_gray(img))
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        return Image.fromarray(out_array)
    
    def binarization_sauvola(self, img, window_size=41):

        in_array = numpy.array(self.convert_to_gray(img))
        mask = threshold_sauvola(in_array, window_size=window_size)
        out_array = in_array > mask
        return Image.fromarray(out_array)
    
    def convert_to_gray(self, img: Image):
        
        if img.mode == "1" or img.mode == "L":
            return img
        
        return img.convert("L")

    def print_shape_information(self, img: Image):
        
        no_of_components, labels, sizes = self.connected_components_with_stats(img)
        print("Number of components: %d." % (no_of_components - 1))
        print("Average shape size: %d." % numpy.average(sizes[1:]))
        print("Standard deviation: %f." % numpy.std(sizes[1:]))
        print("Median shape size: %d." % numpy.median(sizes[1:]))
        print("Median / Average: %f." % (numpy.median(sizes[1:]) / numpy.average(sizes[1:])))
        num_bins = 256
        n, bins, patches = pyplot.hist(sizes[1:], num_bins, facecolor='blue', alpha=0.5)
        pyplot.show()
    
    def connected_components_with_stats(self, img: Image):

        if img.mode != "1":
            raise Exception("Please call the connected_components method only on binary images!")

        inverted = ImageOps.invert(img.convert("RGB"))
        ndarray = numpy.array(inverted.convert("1"), dtype=numpy.uint8)
        no_of_components, labels, stats, centroids = cv2.connectedComponentsWithStats(ndarray, connectivity=8)
        sizes = stats[:, cv2.CC_STAT_AREA];
        
        # Leave out background 
        return no_of_components, labels, sizes

    def denoise(self, img: Image):
        
        no_of_components, labels, sizes = self.connected_components_with_stats(img)

        small_shapes = 0
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] < 4:
                small_shapes += 1
        
        if small_shapes / (no_of_components - 1) < 0.1:
            #print("No need to denoise")
            return img
        
        textheight = AltoPageLayout(img).get_median_text_height()
        shape_diameter = textheight / 8
        threshold = int(shape_diameter * shape_diameter)

        bw_new = numpy.ones((labels.shape), dtype=numpy.bool)
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] > threshold:
                bw_new[labels == shape_identifier] = 0
        return Image.fromarray(bw_new)
    
    def determine_dot_size(self, img: Image):
        
        ndarray = pil_to_ndarray(img)
        
        bin_image = self.binarization_otsu(img)
        alto_layout = AltoPageLayout(bin_image)
        
        dotsizes = []
        for text_string in alto_layout.getAllStrings():
            if text_string.is_string_with_dots():
                x1, y1, x2, y2 = text_string.get_bounding_box()
                expected_no_of_shapes = text_string.get_number_of_shapes()
                no_of_components, labels, sizes = self.connectedComponentsWithStats(ndarray_to_pil(ndarray[y1:y2, x1:x2]))
                size_values = []
                for shape_identifier in range(1, no_of_components):
                    size_values.append(sizes[shape_identifier])
                size_values = numpy.sort(size_values)
                if len(size_values) < expected_no_of_shapes:
                    continue
                dotsizes.append(size_values[-1 * expected_no_of_shapes])
        print("Dotsize: %f" % numpy.median(dotsizes))
                
            
        return 13
        

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


