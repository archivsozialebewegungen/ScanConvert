'''
Created on 13.03.2021

@author: michael
'''
from PIL import Image
from os import path
import tempfile
import os
import numpy
from Asb.ScanConverter.Services import FormatConversionService
import time

class OcropuyImageDetectionService(object):
    '''
    classdocs
    '''

    def __init__(self, format_conversion_service: FormatConversionService):

        self.format_conversion_service = format_conversion_service

    def getImageMask(self, img: Image):
        
        with tempfile.TemporaryDirectory() as tmpdir:
            #bin_img = self.format_conversion_service._binarization_sauvola(img)
            bin_img = self.format_conversion_service._binarization_fixed(img, 200)
            bin_img_path = path.join(tmpdir, "input.bin.png") 
            bin_img.save(bin_img_path)
            bin_img_path = path.join(tmpdir, "input.bin.png") 
            bin_img.save("Image1.bin.png")
            #cmd = 'bash -c "PYTHONPATH=; source /home/michael/workspace/ocropy/ocropus_venv/bin/activate; ocropus-gpageseg -n --maxlines 2000 --minscale 3.0 %s"' % bin_img_path
            cmd = 'bash -c "PYTHONPATH=; source /home/michael/workspace/ocropy/ocropus_venv/bin/activate; ocropus-gpageseg -n %s"' % bin_img_path
            print(cmd)
            os.system(cmd)
            time.sleep(20)
            seg_info_path = path.join(tmpdir, "input.pseg.png")
            seg_info = Image.open(seg_info_path)
        
            green_channel = seg_info.getchannel("R")
            green_channel_array = numpy.array(green_channel, dtype=numpy.uint8)
            green_channel.save("/tmp/test.png")
            #red_channel = seg_info.getchannel("R")
            #red_channel_array = numpy.array(red_channel, dtype=numpy.uint8)
            mask_gray = numpy.ones((green_channel_array.shape), dtype=numpy.bool)
            mask_lineart = numpy.ones((green_channel_array.shape), dtype=numpy.bool)
            mask_gray[green_channel_array == 255] = 0
            mask_lineart[green_channel_array == 254] = 1
        
        return (mask_lineart, mask_gray)