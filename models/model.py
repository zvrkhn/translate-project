import easyocr
import imutils as im
import translators as ts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

class ImageTranslator:
    def __init__(self, file_path, from_language, to_language):
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
        img = np.array(Image.open(self.file_path))
        dimensions = img.shape
        img = im.resize(img, width=dimensions[1], height=dimensions[0])
        return img

    def makeLinesCoordinates(self, coordinates_a, coordinates_b):
        """
    Connect two text boxes into one line box that contains both of them (horizontal box connection)

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
        Connect two text boxes into one paragraph box that contains both of them (vertical box connection)

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
        THE MAIN IDEA:
        if (difference between TOP RIGHT x of the right box and TOP LEFT x of the left box is less than 30) 
        AND 
        (difference between TOP LEFT y of the right box and TOP LEFT y of the left box is less than 30)
        then combine them into one line

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
        THE MAIN IDEA:
        if difference between TOP LEFT y of the bottom box and BOTTOM RIGHT y of the top box is less than 5
        then combine them into one paragraph

        """
        # result = self.lines
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
        Get the most frequent color in the box

        """
        colors = []
        for i in range(box[0][0], box[1][0]):
            for j in range(box[0][1], box[2][1]):
                colors.append(tuple(self.img[j][i]))
        return max(set(colors), key=colors.count)

    def draw_boxes(self, outline=None, color=None):
        """
        Draws boxes on the place of the text coordinates
        Can be used to show text outline or cover old text with box

        """
        for (coord, _) in self.lines:
            (topleft, topright, bottomright, bottomleft) = coord
            tx, ty = (int(topleft[0]), int(topleft[1]))
            bx, by = (int(bottomright[0]), int(bottomright[1]))
        #   if outline != None or color != None:
            color = self.most_frequent_color_in_box([topleft, topright, bottomleft, bottomright])
            self.drawer.rectangle([(tx, ty), (bx, by)], fill = color, outline = outline)

        return color

    def translator(self, text):
        """
        Translates the text and fit some letters to the Ukrainian alphabet

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

        """
        coordinates = [i[0] for i in text]
        return coordinates

    def isInParagraph(self, parCoords, lineCoords):
        """
        Checks if the paragraph is in the line

        """

        if parCoords[0][0] <= lineCoords[0][0] and parCoords[1][0] >= lineCoords[1][0] and parCoords[0][1] <= lineCoords[0][1]:
            return True
        else:
            return False

    def extrLineHeight(self):
        """
        Extracts the height of the first line of the paragraph

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
        self.lines = self.makeLines()
        color = self.draw_boxes(outline=None, color=None)
        self.paragraphs, parHeights, parWeights = self.makeParagraphs()
        firstLineHeight = self.extrLineHeight()
        self.textWrite(parWeights, firstLineHeight, parHeights, color)
        # plt.imshow(self.image)
        # plt.axis('off')
        # plt.show()

    def preview(self, type = None):
        if type == 'image':
            self.image.show()
        else:
            plt.imshow(self.image)
            plt.axis('off')
            plt.show()
    
    def save(self, out_dir, name):
        self.image.save(out_dir + '/' + str(name) + '.png')

# if __name__ == "__main__":
#     file_path = r'G:\My Drive\Own\image-to-text-translate\test-images\test_russian3.png'
#     translator = ImageTranslator(file_path, from_language='auto', to_language='en')
#     translator.run()