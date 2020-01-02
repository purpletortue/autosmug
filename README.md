Autosmug
========


These scripts are for automating some SmugMug operations one might perform on a regular basis, for example, daily/weekly uploading new files in a local folder to a gallery on smugmug.


Requirements
------------

To install autosmug:

  git clone https://github.com/tortue-B/autosmug.git  
	cd autosmug
	python3 -m venv env  
	source env/bin/activate  
  pip3 install -r requirements.txt

You may need to patch rauth due to a Python 3 Type requirement (without this patch POST methods to the API will fail):

  patch -p0 -i rauth.patch


The original Python API interface (smugmug.py) and registration scripts (smregister & smregtest) were written by Marek Rei as part of his smuploader Github repo. These files have been duplicated here since, over time, changes are expected to be made that will not be backward compatible with other existing scripts/modules.


Copyright and License
---------------------

This software is distributed under The MIT License (MIT)

Copyright (c) 2020 Marek Rei, Robert Baptista

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
