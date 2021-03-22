'''
Created on 21.03.2021

@author: michael
'''
from numpy import ndarray
from PIL import Image
import tempfile
from os import path
import numpy
import cv2

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
