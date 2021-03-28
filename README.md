# ScanConvert
Gui to bulk convert scans to pdf files and perform certain changes to the files

## Installation

### Non python dependencies

Make sure that the following dependencies are installed:

* tesseract, version 4.1
* libtiff-tools
* ocrmypdf

### Create and activate a virtual environment

   python3 -m venv --copies venv
   source venv/bin/activate
   
### Install the dependencies

Be aware that the following command lasts quite some time. Installing open cv is
a major compile task. Also it is not possible to put wheel and torch into the
requirements.txt file, so it is necessary to install them beforehand.

   pip3 install wheel
   pip3 install torch
   pip3 install -r requirements.txt
   
   
   


