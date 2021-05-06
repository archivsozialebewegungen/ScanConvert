'''
Created on 05.04.2021

@author: michael
'''

from PIL import Image
import cv2
from numpy import ndarray
import numpy


def pil_to_skimage(img: Image) -> ndarray:

    return pil_to_ndarray(img)

def skimage_to_pil(ndarray: ndarray, resolution: (int,)) -> Image:
    
    return ndarray_to_pil(ndarray, resolution)

def pil_to_ndarray(img: Image) -> ndarray:
    
    return numpy.array(img)

def ndarray_to_pil(ndarray: ndarray, resolution: (int,)) -> Image:
    
    img = Image.fromarray(ndarray)
    if resolution is not None:
        img.info['dpi'] = resolution
    return img

def pil_to_rgb_cv2image(img: Image):
    
    return pil_to_ndarray(img)
    
def rgb_cv2image_to_pil(cv2_image, resolution: (int,)):
    
    return ndarray_to_pil(cv2_image, resolution)

def pil_to_native_cv2image(img: Image):
    
    if img.mode == 'L' or img.mode == '1':
        return pil_to_ndarray(img)
    return cv2.cvtColor(pil_to_ndarray(img), cv2.COLOR_RGB2BGR)

def native_cv2image_to_pil(cv2_image, resolution: (int,)):
    
    if len(cv2_image.shape) < 3:
        return ndarray_to_pil(cv2_image, resolution)
    return ndarray_to_pil(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB), resolution)
