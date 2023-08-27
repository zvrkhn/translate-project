
# Image to text translator

The project is a test of easyocr and PIL libraries combination for extracting text from image and putting translation back to the original image. GUI was made using Tkinker.

# Used libraries

For stable work of the model following libraries should be installed:

1. [EasyOCR](https://github.com/JaidedAI/EasyOCR)
2. [imutils](https://github.com/PyImageSearch/imutils)
3. [translators](https://github.com/UlionTse/translators)
4. [NumPy](https://numpy.org/)
5. [Pillow (PIL)](https://python-pillow.org/)
6. [matplotlib](https://matplotlib.org/)
7. [(Optional for basic GUI) Tkinter](https://tcl.tk/man/tcl8.6/TkCmd/contents.htm)
## Deployment

To run this project:

1. Install following libraries:
- pip install easyocr
- pip install imutils
- pip install translators
- pip install numpy
- pip install Pillow
- pip install matplotlib
- pip install (Optional for basic GUI) Tkinter

2. Create ImageTranslator(file_path, from_language, to_language) object and use run() method to start translation.

3. To preview image using matplotlib use preview() method, for image file preview use preview("image")

4. To save result use save(out_dir, name) method.


