'''
Created on 05.04.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Services import JobDefinition, GraphicFileInfo
import os
from Asb.ScanConverter.Ocr.PdfService import PdfService
from Asb.ScanConverter.ImageOperations import ImageFileOperations


class PdfServiceTest(unittest.TestCase):


    def testPdfService(self):

        service = PdfService(ImageFileOperations())
        job_definition = JobDefinition()
        job_definition.fileinfos = (GraphicFileInfo(os.path.join("Images", "Image1.png")),
                                    GraphicFileInfo(os.path.join("Images", "Image1.png")))
        job_definition.output_path = "test.pdf"
        
        service.create_pdf_file(job_definition)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()