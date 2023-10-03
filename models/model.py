import easyocr
import imutils as im
import translators as ts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

class ImageTranslator:
    """
    A class for translating text from an image file.

    Args:
        file_path (str): The path to the image file.
        from_language (str, optional): The language to translate from. Defaults to 'auto'.
        to_language (str, optional): The language to translate to. Defaults to 'en'.
    """

    def __init__(self, file_path, from_language='auto', to_language='en'):
        self.file_path = file_path
        self.img = self.load_resize()
        self.image = Image.fromarray(self.img)
        self.drawer = ImageDraw.Draw(self.image)
        self.reader = easyocr.Reader(['ru', 'en', 'uk'])
        self.result = self.reader.readtext(self.img)
        self.lines = []
        self.parahraphs = []
        if from_language != None:
            self.from_language = from_language
        else:
            self.from_language = 'auto'

        if to_language != None:
            self.to_language = to_language
        else:
            self.to_language = 'en'


    def load_resize(self):
        """
        Loads an image from the file path specified in self.file_path, resizes it to its original dimensions, and returns the resized image.

        Returns:
            numpy.ndarray: The resized image.
        """
        img = np.array(Image.open(self.file_path))
        dimensions = img.shape
        img = im.resize(img, width=dimensions[1], height=dimensions[0])
        return img

    def makeLinesCoordinates(self, coordinates_a, coordinates_b):
        """
        Connect two text boxes into one line box that contains both of them (horizontal box connection)

        Args:
            coordinates_a (list of lists): list of coordinates for the first text box
            coordinates_b (list of lists): list of coordinates for the second text box

        Returns:
            list of lists: list of coordinates for the line box that contains both text boxes
        """
        new_coordinates = [
            [coordinates_a[0][0], min(coordinates_a[0][1], coordinates_b[0][1])],
            [coordinates_b[1][0], min(coordinates_a[1][1], coordinates_b[1][1])],
            [coordinates_b[2][0], max(coordinates_a[2][1], coordinates_b[2][1])],
            [coordinates_a[3][0], max(coordinates_a[3][1], coordinates_b[3][1])]
        ]
        return new_coordinates

    def makeParagraphsCoordinates(self, coordinates_a, coordinates_b):
            """
            Connects two text boxes into one paragraph box that contains both of them (vertical box connection).

            Args:
                coordinates_a (list of lists): A list of 4 coordinates representing the bounding box of the first text box.
                coordinates_b (list of lists): A list of 4 coordinates representing the bounding box of the second text box.

            Returns:
                list of lists: A list of 4 coordinates representing the bounding box of the new paragraph box.
            """
            new_coordinates = [
                [min(coordinates_a[0][0], coordinates_b[0][0]), coordinates_a[0][1]],
                [max(coordinates_a[1][0], coordinates_b[1][0]), coordinates_a[1][1]],
                [max(coordinates_a[2][0], coordinates_b[2][0]), coordinates_b[2][1]],
                [min(coordinates_a[3][0], coordinates_b[3][0]), coordinates_b[3][1]]
            ]
            return new_coordinates

    def makeLines(self):
        """
        Groups the OCR result into lines of text based on their proximity.

        Returns:
            list of tuples containing the coordinates and text of each line.
        """
        lines = [self.result[0][1]]
        coordinates = [self.result[0][0]]

        for i in range(1, len(self.result)):

            diff_x = self.result[i][0][0][0] - coordinates[-1][1][0]
            diff_y = self.result[i][0][0][1] - coordinates[-1][0][1]
            if np.abs(diff_x) < 30 and np.abs(diff_y) < 30:
                lines[-1] += " " + self.result[i][1]
                coordinates[-1] = self.makeLinesCoordinates(coordinates[-1], self.result[i][0])

            else: 
                lines.append(self.result[i][1])
                coordinates.append(self.result[i][0])

        self.lines = list(zip(coordinates, lines))
        return self.lines

    def makeParagraphs(self):
        """
        Groups lines into paragraphs based on their proximity to each other.

        Returns:
            tuple containing:
                list of tuples, where each tuple contains the coordinates and text of a paragraph.
                list of the heights of each paragraph.
                list of the widths of each paragraph.
        """
        parHeight = []
        parWeight = []
        lines = [self.lines[0][1]]
        coordinates = [self.lines[0][0]]
        for i in range(1, len(self.lines)):
            diff_x = self.lines[i][0][0][0] - coordinates[-1][1][0]
            diff_y = self.lines[i][0][0][1] - coordinates[-1][2][1]
            if diff_y < 5 and diff_x < 30:
                lines[-1] += " " + self.lines[i][1]
                coordinates[-1] = self.makeParagraphsCoordinates(coordinates[-1], self.lines[i][0])

            else:
                parHeight.append(np.abs(coordinates[-1][0][1] - coordinates[-1][2][1]))
                parWeight.append(np.abs(coordinates[-1][1][0] - coordinates[-1][0][0]))
                lines.append(self.lines[i][1])
                coordinates.append(self.lines[i][0])
        parHeight.append(np.abs(coordinates[-1][0][1] - coordinates[-1][2][1]))
        parWeight.append(np.abs(coordinates[-1][1][0] - coordinates[-1][0][0]))
        self.parahraphs = list(zip(coordinates, lines))
        return self.parahraphs, parHeight, parWeight

    def most_frequent_color_in_box(self, box):
        """
        Get the most frequent color in the given box.

        Args:
            box (tuple): A tuple containing the coordinates of the top-left and bottom-right corners of the box.

        Returns:
            tuple: A tuple representing the most frequent color in the box.
        """
        colors = []
        for i in range(box[0][0], box[1][0]):
            for j in range(box[0][1], box[2][1]):
                colors.append(tuple(self.img[j][i]))
        return max(set(colors), key=colors.count)

    def draw_boxes(self, outline=None, color=None):
        """
        Draws boxes on the place of the text coordinates.
        Can be used to show text outline or cover old text with box.

        Args:
            outline (tuple, optional): The outline color of the box. Default is None.
            color (tuple, optional): The fill color of the box. Default is None.

        Returns:
            tuple: The fill color of the box.
        """
        for (coord, _) in self.lines:
            (topleft, topright, bottomright, bottomleft) = coord
            tx, ty = (int(topleft[0]), int(topleft[1]))
            bx, by = (int(bottomright[0]), int(bottomright[1]))
            color = self.most_frequent_color_in_box([topleft, topright, bottomleft, bottomright])
            self.drawer.rectangle([(tx, ty), (bx, by)], fill = color, outline = outline)

        return color

    def translator(self, text):
        """
        Translates the text and fit some letters to the Ukrainian alphabet

        Args:
            text (str): The text to be translated

        Returns:
            str: The translated text
        """ 
        text_witho_comma = text.replace(',', '')
        try:
            value = int(text_witho_comma)
            return str(value)
        except ValueError:
            pass

        translate = ts.translate_text(text, from_language=self.from_language, to_language=self.to_language)
        return translate


    def getCoordinates(self, text):
        """
        Gets the coordinates of the text boxes

        Args:
            text (list): A list of tuples containing the text and its coordinates.

        Returns:
            list: A list of coordinates of the text boxes.
        """
        coordinates = [i[0] for i in text]
        return coordinates

    def isInParagraph(self, parCoords, lineCoords):
        """
        Checks if the paragraph is in the line

        Args:
            parCoords (tuple): The coordinates of the paragraph in the format ((x1, y1), (x2, y2))
            lineCoords (tuple): The coordinates of the line in the format ((x1, y1), (x2, y2))

        Returns:
            bool: True if the paragraph is in the line, False otherwise
        """

        if parCoords[0][0] <= lineCoords[0][0] and parCoords[1][0] >= lineCoords[1][0] and parCoords[0][1] <= lineCoords[0][1]:
            return True
        else:
            return False

    def extrLineHeight(self):
        """
        Extracts the height of the first line of the paragraph

        Returns:
            firstLineHeight (list): A list of the height of the first line of each paragraph in the document.
        """
        par = self.parahraphs
        parCoords = self.getCoordinates(par)
        line = self.lines
        lineCoords = self.getCoordinates(line)
        firstLineHeight = []
        for i in range(len(parCoords)):
            for j in range(len(lineCoords)):
                if self.isInParagraph(parCoords[i], lineCoords[j]):
                    firstLineHeight.append(np.abs(lineCoords[i][0][1] - lineCoords[i][2][1]))
                    break
        return firstLineHeight

    def textWrap(self, text, firstLineHeight, boxesWight, parHeight, font, fontsize):
        """
        Wraps the text to fit the box and changes the font size to fit the box

        Args:
            text (list): A list containing the text to be wrapped.
            firstLineHeight (int): The height of the first line of text.
            boxesWight (int): The width of the box.
            parHeight (int): The height of the paragraph.
            font (ImageFont): The font to be used for the text.
            fontsize (int): The size of the font.

        Returns:
            tuple: A tuple containing the wrapped text, the coordinates of each line, and the font to be used.
        """
        
        textToWrite = text[1].split(' ')
        length = font.getlength(text[1])

        if length == boxesWight: # if the text is exactly the same size as the box (width)
            lines_num = int(length / boxesWight)
        else:
            lines_num = int(length / boxesWight) + 1

        if lines_num*firstLineHeight > parHeight: # if the text is too big for the box (height)
            fontsize *= parHeight / (lines_num*firstLineHeight)
            font = ImageFont.truetype("arial.ttf", int(fontsize))

        lines = [textToWrite[0]]
        coords = []

        coords.append(tuple([text[0][0][0], int(text[0][0][1])]))
        for i in range(1, len(textToWrite)):

            if font.getlength(lines[-1] + " " + textToWrite[i]) <= boxesWight:
                lines[-1] += " " + textToWrite[i]
            else:
                lines.append(textToWrite[i])
                coords.append(tuple([coords[-1][0], int(coords[-1][1] + firstLineHeight * 0.8)]))

        if len(lines) == 1 and font.getlength(lines[0]) < boxesWight: # if the text is too small for the box (width)

            fontsize *= boxesWight / font.getlength(lines[0]) * 0.95

            font = ImageFont.truetype("arial.ttf", int(fontsize))
        return lines, coords, font
    
    def textWrite(self, wight, firstLineHeight, parHeights, color):
        """
        Function that puts translated text into the image

        Args:
            wight (list): A list of integers representing the width of each paragraph in pixels.
            firstLineHeight (list): A list of integers representing the height of the first line of each paragraph in pixels.
            parHeights (list): A list of integers representing the height of each paragraph in pixels.
            color (tuple): A tuple of integers representing the RGB color values of the text.

        Returns:
            None
        """

        for i in range(len(self.parahraphs)):
            translate = self.translator(self.parahraphs[i][1])

            translate = [self.parahraphs[i][0], translate]
            fontsize = int(parHeights[i] / (int(parHeights[i]/firstLineHeight[i])+1) * 0.9)
            font = ImageFont.truetype("arial.ttf", fontsize)
            lines, coords, new_font = self.textWrap(translate, firstLineHeight[i], wight[i], parHeights[i], font, fontsize)
            font = new_font
            for i in range(len(lines)):
                self.drawer.text(coords[i], lines[i], fill=(255 - color[0], 255 - color[1], 255 - color[2]), font=font)

    def run(self):
        """
        Runs the model and performs the following steps:
            - Makes lines
            - Draws boxes
            - Makes paragraphs
            - Calculates first line height
            - Writes text
        """
        self.lines = self.makeLines()
        color = self.draw_boxes(outline=None, color=None)
        self.paragraphs, parHeights, parWeights = self.makeParagraphs()
        firstLineHeight = self.extrLineHeight()
        self.textWrite(parWeights, firstLineHeight, parHeights, color)


    class Model:
        def __init__(self, image):
            self.image = image

        def preview(self, type=None):
            """
            Displays a preview of the image.

            Args:
                type (str, optional): The type of preview to display. Defaults to None (for matplotlib graph style).

            Returns:
                None
            """
            if type == 'image':
                self.image.show()
            else:
                plt.imshow(self.image)
                plt.axis('off')
                plt.show()
    
    def save(self, out_dir, name):
            """
            Saves the image of the model to the specified directory with the given name.

            Args:
                out_dir (str): The directory to save the image to.
                name (str): The name to give the saved image.

            Returns:
                None
            """
            self.image.save(out_dir + '/' + str(name) + '.png')
