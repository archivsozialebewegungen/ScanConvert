'''
Created on 04.07.2022

@author: michael
'''
import unittest
import os
from os.path import dirname
from Asb.ScanConverter.Domain import Scan, COLOR, GRAYSCALE, BW


class Test(unittest.TestCase):


    def setUp(self):
        
        self.img_dir = os.path.join(dirname(__file__), "TestImages")
        self.color_img = os.path.join(self.img_dir, "Color.jpg")
        self.gray_img = os.path.join(self.img_dir, "Gray.jpg")
        self.bw_img = os.path.join(self.img_dir, "BW.tif")


    def test_load_color(self):
        
        scan = Scan(self.color_img)
        self.assertEqual(72, scan.resolution)
        self.assertEqual(485, scan.width)
        self.assertEqual(540, scan.height)
        self.assertEqual(COLOR, scan.mode)

    def test_load_grayscale(self):
        
        scan = Scan(self.gray_img)
        self.assertEqual(72, scan.resolution)
        self.assertEqual(485, scan.width)
        self.assertEqual(540, scan.height)
        self.assertEqual(GRAYSCALE, scan.mode)

    def test_load_bw(self):
        
        scan = Scan(self.bw_img)
        self.assertEqual(72, scan.resolution)
        self.assertEqual(485, scan.width)
        self.assertEqual(540, scan.height)
        self.assertEqual(BW, scan.mode)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()