'''
Created on 05.04.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Services import JobDefinition, GraphicFileInfo
import os
from Asb.ScanConverter.Ocr.PdfService import PdfService
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.OCR import OcrRunner, OcrPreprocessor,\
    OcrPostprocessor
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout


class PdfServiceTest(unittest.TestCase):


    def testPdfService(self):

        img_ops = ImageFileOperations()
        ocr_runner = OcrRunner(OcrPreprocessor(img_ops), OcrPostprocessor())
        img = img_ops.load_image(os.path.join("Images", "Image1.png"))
        
        #hocr = ocr_runner.get_hocr(img)
        #hocr_file = open("Image1.hocr", "bw")
        #hocr_file.write(hocr)
        #hocr_file.close()
        
        #alto = AltoPageLayout(img)
        #alto.write_to_file("Image1.alto")

        service = PdfService(img_ops, ocr_runner)
        job_definition = JobDefinition()
        job_definition.fileinfos = (GraphicFileInfo(os.path.join("Images", "Image1.png")),
                                    GraphicFileInfo(os.path.join("Images", "Image2.png")))
        job_definition.output_path = "test.pdf"
        
        service.create_pdf_file(job_definition)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()