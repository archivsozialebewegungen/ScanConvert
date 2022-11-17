# ScanConvert
Gui to bulk convert scans to pdf files and perform certain changes to the files

## Installation

### Non python dependencies

Make sure that the following dependency is installed:

* tesseract, version 4.1

### Create and activate a virtual environment

    python3 -m venv --copies venv
    source venv/bin/activate
   
### Install the dependencies

Be aware that the following command lasts quite some time. Installing open cv is
a major compile task. Also it is not possible to put wheel and torch into the
requirements.txt (I really don't understand why, but that's how it is) file,
so it is necessary to install them beforehand.

    pip3 install wheel
    pip3 install torch==1.8.1
    pip3 install -r requirements.txt
    
### Download the spacy model

    python -m spacy download de_dep_news_trf
 