'''
Created on 13.02.2021

@author: michael
'''

from PyQt5.QtWidgets import QApplication, QPushButton, QTableWidget,\
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTableWidgetItem, QAbstractItemView
import sys
from PIL import Image
from os.path import basename

BLACK_AND_WHITE = "Schwarz-Weiß"
GRAYSCALE = "Graustufen"
COLOR = "Farbe"
COLOR_WITH_ALPHA = "Farbe mit Transparenz"
INDEX = "Indexiert"

class GraphicFileInfo:
    
    modes = {"1": BLACK_AND_WHITE, "L": GRAYSCALE, "RGB": COLOR,
             "RGBA": COLOR_WITH_ALPHA, "P": INDEX}
    
    def __init__(self, filepath):
        
        self.filepath = filepath
        img = Image.open(filepath)
        self.format = type(img).__name__.replace('ImageFile', '')
        self.rawmode = img.mode
        self.width = img.width
        self.height = img.height
        self.info = img.info
        img.close()
        
    def _get_resolution(self):
        
        if "dpi" in self.info:
            dpi = self.info['dpi']
            if dpi[0] == 1:
                return "Unbekannt"
            if dpi[0] == dpi[1]:
                return "%s" % dpi[0]
            else:
                return "%sx%s" % dpi
        for key in self.info.keys():
            print(key)
        return "Unbekannt"
    
    def _get_filename(self):
        
        return basename(self.filepath)
    
    def _get_mode(self):
        
        if self.rawmode in self.modes:
            return self.modes[self.rawmode]
        
        return "Unbekannt (%s)" % self.rawmode
    
    resolution = property(_get_resolution)
    filename = property(_get_filename)
    mode = property(_get_mode)
    
    
        
class Window(QWidget):

    def __init__(self):
        super().__init__()
        self.createWidgets()
        self.setGeometry(400, 400, 300, 300)
        self.setWindowTitle("Scan-Kovertierer")
        self.fileinfos = []

    def createWidgets(self):
        
        file_selection_button = QPushButton("Laden")
        file_up_button = QPushButton("Hoch")
        file_down_button = QPushButton("Runter")
        file_remove_button = QPushButton("Entfernen")
        file_selection_button.clicked.connect(self.add_files)
        file_up_button.clicked.connect(self.files_up)
        file_down_button.clicked.connect(self.files_down)
        file_remove_button.clicked.connect(self.remove_files)
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["Datei", "Modus", "Auflösung", "Format"])
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(file_selection_button)
        button_layout.addWidget(file_up_button)
        button_layout.addWidget(file_down_button)
        button_layout.addWidget(file_remove_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.file_list)
        
        self.setLayout(layout)

    def append_fileinfo(self, fileinfo):
        
        self.fileinfos.append(fileinfo)
        self.file_list.setRowCount(len(self.fileinfos))
        self.display_line(len(self.fileinfos) - 1)
        
    def display_line(self, index):
        
        self.file_list.setItem(index, 0, QTableWidgetItem(self.fileinfos[index].filename))
        self.file_list.setItem(index, 1, QTableWidgetItem(self.fileinfos[index].mode))
        self.file_list.setItem(index, 2, QTableWidgetItem(self.fileinfos[index].resolution))
        self.file_list.setItem(index, 3, QTableWidgetItem(self.fileinfos[index].format))
        
    def files_up(self):
        
        selection_model = self.file_list.selectionModel()
        for index in self.file_list.selectionModel().selectedRows():
            if index.row() == 0:
                continue
            self.flip_lines(index.row(), index.row()-1)
        selection_model.clearSelection()
    
    def files_down(self):
        
        selection_model = self.file_list.selectionModel()
        for index in self.file_list.selectionModel().selectedRows():
            if index.row() == len(self.fileinfos) - 1:
                continue
            self.flip_lines(index.row(), index.row()+1)
        selection_model.clearSelection()

    def remove_files(self):
        
        indices = self.file_list.selectionModel().selectedRows()

        # Must delete in reverse order
        for each_row in reversed(sorted(indices)):
            self.file_list.removeRow(each_row.row())
            del self.fileinfos[each_row.row()]
        
    def flip_lines(self, line1, line2):
        
        fileinfo1 = self.fileinfos[line1]
        self.fileinfos[line1] = self.fileinfos[line2]
        self.fileinfos[line2] = fileinfo1
        self.display_line(line1)
        self.display_line(line2)
        

    def add_files(self):
        
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Graphikdateien (*.jpg *.tif *.gif)")
        
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            for filename in filenames:
                self.append_fileinfo(GraphicFileInfo(filename))
                 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
