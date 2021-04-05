'''
Created on 05.04.2021

@author: michael
'''
from matplotlib import pyplot
from PIL import Image
import cv2
from Asb.ScanConverter.ImageTypeConversion import pil_to_native_cv2image
import numpy

class DeveloperTools(object):
    '''
    Assorted tools to check image files
    '''

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
        
    def print_shape_information(self, img: Image):
        '''
        Collect statistics on the image file.
        
        TODO: Add more statistics stuff and move
        the method to some helper module. This is nothing that
        will be used in production.
        '''
        
        no_of_components, labels, sizes = self.connected_components_with_stats(img)
        print("Number of components: %d." % (no_of_components - 1))
        print("Average shape size: %d." % numpy.average(sizes[1:]))
        print("Standard deviation: %f." % numpy.std(sizes[1:]))
        print("Median shape size: %d." % numpy.median(sizes[1:]))
        print("Median / Average: %f." % (numpy.median(sizes[1:]) / numpy.average(sizes[1:])))
        num_bins = 256
        n, bins, patches = pyplot.hist(sizes[1:], num_bins, facecolor='blue', alpha=0.5)
        pyplot.show()
    