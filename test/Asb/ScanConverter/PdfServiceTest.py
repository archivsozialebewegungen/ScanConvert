'''
Created on 05.04.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Services import JobDefinition, GraphicFileInfo,\
    FormatConversionService
import os
from Asb.ScanConverter.Ocr.PdfService import PdfService
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.OCR import OcrRunner, OcrPreprocessor,\
    OcrPostprocessor
from Asb.ScanConverter.ImageStatistics import ImageStatistics
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
from Asb.ScanConverter.Ocr.Denoiser import DenoiseService


class PdfServiceTest(unittest.TestCase):


    def testPdfService(self):

        img_ops = ImageFileOperations()
        ocr_runner = OcrRunner(OcrPreprocessor(img_ops, ImageStatistics()), OcrPostprocessor())

        service = PdfService(FormatConversionService(Detectron2ImageDetectionService(), img_ops, DenoiseService()), img_ops, ocr_runner)
        job_definition = JobDefinition()
        job_definition.fileinfos = (GraphicFileInfo(os.path.join("Images", "Image1.png")),
                                    GraphicFileInfo(os.path.join("Images", "Image2.png")))
        job_definition.output_path = "test.pdf"
        
        service.create_pdf_file(job_definition)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()