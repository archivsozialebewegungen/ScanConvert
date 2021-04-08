'''
Created on 05.04.2021

@author: michael
'''

from os.path import basename

from reportlab.pdfgen.canvas import Canvas

from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Services import JobDefinition, FormatConversionService
from Asb.ScanConverter.Ocr.OCR import OcrRunner
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
import re

from lxml import etree, html
from injector import singleton, inject
from reportlab.lib.utils import ImageReader
import io

INVISIBLE = 3

@singleton
class PdfService:
    
    @inject
    def __init__(self, format_conversion_service: FormatConversionService, image_operations: ImageFileOperations, ocr_runner: OcrRunner):
        
        self.format_conversion_service = format_conversion_service
        self.image_ops = image_operations
        self.ocr_runner = ocr_runner
    
    def create_pdf_file(self, job: JobDefinition):
        
        image_infos = job.fileinfos
   
        pdf = Canvas(job.output_path, pageCompression=1)
        pdf.setCreator('Scan-Convert')
        pdf.setTitle(basename(job.output_path))
        dpi = 300
        
        for image_info in image_infos:
            img = self.image_ops.load_image(image_info.filepath)
            img_width, img_height = img.size
            try:
                dpi = img.info['dpi'][0]
            except KeyError:
                pass
            page_width = img_width * 72 / dpi
            page_height = img_height * 72 / dpi
            pdf.setPageSize((page_width, page_height))
            
            foreground_img, image_info = self.format_conversion_service.perform_changes(img, image_info, job)
            foreground_img_stream = io.BytesIO()
            foreground_img.save(foreground_img_stream, format='png')
            foreground_img_stream.seek(0)
            foreground_img_reader = ImageReader(foreground_img_stream)
            pdf.drawImage(foreground_img_reader, 0, 0, width=page_width, height=page_height)
            
            #alto_layout = self.ocr_runner.get_alto_layout(img)
            hocr_layout = self.ocr_runner.get_hocr(img)
            self.add_text_layer_from_hocr(pdf, hocr_layout, page_height, dpi)

            pdf.showPage()
        
        pdf.save()
            
    def add_text_layer_from_alto(self, pdf: Canvas, alto_layout: AltoPageLayout, page_height: int, dpi: int):
        """Draw an invisible text layer for OCR data"""
        
        for line in alto_layout.get_all_lines():
            
            line_bbox = line.get_bounding_box()
            
            for string in line.get_strings():
                
                rawtext = string.get_text()
                if rawtext == '':
                    continue
                string_text_width = pdf.stringWidth(rawtext, 'Times-Roman', 8)
                if string_text_width <= 0:
                    continue
                
                string_bbox = string.get_bounding_box()
                
                text = pdf.beginText()
                text.setTextRenderMode(INVISIBLE)
                text.setFont('Times-Roman', 8)
                text.setTextOrigin(string_bbox[0] * 72 / dpi, page_height - (line_bbox[3] * 72 / dpi))
                string_bbox_width = string.get_width() * 72 / dpi
                text.setHorizScale(100.0 * string_bbox_width / string_text_width)
                text.textLine(rawtext)
                pdf.drawText(text)

    def add_text_layer_from_hocr(self, pdf, hocr_layout, height, dpi):
        '''
        This terrible code is lifted from https://github.com/ocropus/hocr-tools
        The result is better, because we have baseline information in hocr, which
        is missing in alto.
        '''

        p1 = re.compile(r'bbox((\s+\d+){4})')
        p2 = re.compile(r'baseline((\s+[\d\.\-]+){2})')
        hocr = etree.fromstring(hocr_layout, html.XHTMLParser())
        for line in hocr.xpath('//*[@class="ocr_line"]'):
            bbox_line = p1.search(line.attrib['title']).group(1).split()
            try:
                baseline = p2.search(line.attrib['title']).group(1).split()
            except AttributeError:
                baseline = [0, 0]
            bbox_line = [float(i) for i in bbox_line]
            baseline = [float(i) for i in baseline]
            xpath_elements = './/*[@class="ocrx_word"]'
            if (not (line.xpath('boolean(' + xpath_elements + ')'))):
                # if there are no words elements present,
                # we switch to lines as elements
                xpath_elements = '.'
            for word in line.xpath(xpath_elements):
                rawtext = word.text_content().strip()
                if rawtext == '':
                    continue
                text_width = pdf.stringWidth(rawtext, 'Times-Roman', 8)
                if text_width <= 0:
                    continue
                bbox_text = p1.search(word.attrib['title']).group(1).split()
                bbox_text = [float(i) for i in bbox_text]
                baseline_absolute = self.polyval(baseline,
                        (bbox_text[0] + bbox_text[2]) / 2 - bbox_line[0]) + bbox_line[3]
                text = pdf.beginText()
                text.setTextRenderMode(3)  # double invisible
                text.setFont('Times-Roman', 8)
                text.setTextOrigin(bbox_text[0] * 72 / dpi, height - baseline_absolute * 72 / dpi)
                bbox_text_width = (bbox_text[2] - bbox_text[0]) * 72 / dpi
                text.setHorizScale(100.0 * bbox_text_width / text_width)
                text.textLine(rawtext)
                pdf.drawText(text)


    def polyval(self, poly, x):
        '''
        WTF? Polyval? Really? "poly" is a tuple, decribed in the documentation
        this way: The two numbers for the baseline are the slope (1st number) and
        constant term (2nd number) of a linear equation describing the baseline
        relative to the bottom left corner of the bounding box
        '''
        return x * poly[0] + poly[1]
