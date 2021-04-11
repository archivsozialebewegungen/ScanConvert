'''
Created on 05.04.2021

@author: michael
'''
from matplotlib import pyplot
from PIL import Image
import cv2
from Asb.ScanConverter.ImageTypeConversion import pil_to_native_cv2image,\
    pil_to_ndarray
import numpy
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout

class DeveloperTools(object):
    '''
    Assorted tools to check image files
    '''
    
    def __init__(self):
        
        self.img_ops = ImageFileOperations()

    def show_image(self, img: Image, title: str='Image'):
        if img.mode == 'L':
            pyplot.imshow(img, cmap='gray', vmin=0, vmax=255)
        else:
            pyplot.imshow(img)
        pyplot.title(title)
        pyplot.xticks([])
        pyplot.yticks([])
        pyplot.show()
    
    def show_image2(self, img: Image):
        
        cv2.imshow("Image", pil_to_native_cv2image(img))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    def dump_alto_file(self, img: Image, filename: str):
        
        alto_layout = AltoPageLayout(img)
        alto_layout.write_to_file(filename)

    def plot_histogram(self, img: Image):
        
        if img.mode != "L":
            img = img.convert("L")
        histogram = img.histogram()
        self.plot_values(histogram)

    def plot_values(self, values):

        pyplot.figure(0)
        for index in range(0, len(values)):
            pyplot.bar(x=index, height=values[index], color="black")
        pyplot.show()
        
    def print_statistics(self, img: Image):
        '''
        Collect statistics on the image file.
        
        TODO: Add more statistics stuff and move
        the method to some helper module. This is nothing that
        will be used in production.
        '''
        if img.mode != "RGB" and img.mode != "L" and img.mode != "1":
            print("Unknown image mode: %s" % img.mode)
            color = img.convert("RGB")
            gray = self.img_ops.convert_to_gray(color)
            bw = self.img_ops.binarization_otsu(gray)
        elif img.mode == "RGB":
            print("RGB image")
            color = img
            gray = self.img_ops.convert_to_gray(color)
            bw = self.img_ops.binarization_otsu(gray)
        elif img.mode == "L":
            print("Grayscale image")
            color = None
            gray = img
            bw = self.img_ops.binarization_otsu(gray)
        else:
            print("Black and white image")
            color = None
            gray = None
            bw = img

        #self._print_shape_statics(bw)

        #self.plot_histogram(img)
        
    def _print_shape_statics(self, img: Image):
        no_of_components, labels, sizes = self.img_ops.connected_components_with_stats(img)
        print(numpy.sort(sizes[1:]))
        print("Number of components: %d." % (no_of_components - 1))
        print("Average shape size: %d." % numpy.average(sizes[1:]))
        print("Standard deviation: %f." % numpy.std(sizes[1:]))
        print("Deviation / Average: %f." % (numpy.std(sizes[1:]) / numpy.average(sizes[1:])))
        print("Median shape size: %d." % numpy.median(sizes[1:]))
        print("Median / Average: %f." % (numpy.median(sizes[1:]) / numpy.average(sizes[1:])))

    