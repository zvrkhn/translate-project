import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import *
import sys
import easyocr
import cv2 as cv
import imutils as im
import translators as ts
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk
import easygui 
import matplotlib.pyplot as plt
import os

def load_resize(file_path): 
    """
    Reads and resizes the image to fit the screen

    """
    img = np.array(Image.open(file_path))
    dimensions = img.shape
    img = im.resize(img, width=dimensions[1], height=dimensions[0])
    return img

def makeLinesCoordinates(coordinates_a, coordinates_b): # make new horizontal coordinates for the text boxes
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
    
def makeParagraphsCoordinates(coordinates_a, coordinates_b): # make new vertical coordinates for the text boxes
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


def makeLines(result): # compares the coordinates of the text boxes and if they are close enough, it combines them into one line
    """ 
    THE MAIN IDEA:
    if (difference between TOP RIGHT x of the right box and TOP LEFT x of the left box is less than 30) 
    AND 
    (difference between TOP LEFT y of the right box and TOP LEFT y of the left box is less than 30)
    then combine them into one line

    """

    lines = [result[0][1]]
    coordinates = [result[0][0]]
    for i in range(1, len(result)):
      
      diff_x = result[i][0][0][0] - coordinates[-1][1][0]
      diff_y = result[i][0][0][1] - coordinates[-1][0][1]
      if np.abs(diff_x) < 30 and np.abs(diff_y) < 30:
        lines[-1] += " " + result[i][1]
        coordinates[-1] = makeLinesCoordinates(coordinates[-1], result[i][0])
        
      else: 
        lines.append(result[i][1])
        coordinates.append(result[i][0])

    return list(zip(coordinates, lines))

def makeParagraphs(result): # compares the coordinates of the text boxes and if they are close enough, it combines them into one paragraph
    """
    THE MAIN IDEA:
    if difference between TOP LEFT y of the bottom box and BOTTOM RIGHT y of the top box is less than 5
    then combine them into one paragraph

    """
    parHeight = []
    lines = [result[0][1]]
    coordinates = [result[0][0]]
    for i in range(1, len(result)):
        diff_x = result[i][0][0][0] - coordinates[-1][1][0]
        diff_y = result[i][0][0][1] - coordinates[-1][2][1]
        if diff_y < 5 and diff_x < 30:
            lines[-1] += " " + result[i][1]
            coordinates[-1] = makeParagraphsCoordinates(coordinates[-1], result[i][0])
        
        else:
            parHeight.append(np.abs(coordinates[-1][0][1] - coordinates[-1][2][1]))
            lines.append(result[i][1])
            coordinates.append(result[i][0])
    parHeight.append(np.abs(coordinates[-1][0][1] - coordinates[-1][2][1]))
    return list(zip(coordinates, lines)), parHeight

def most_frequent_color_in_box(img, box): # get the most frequent color in the box
    """
    Get the most frequent color in the box

    """
    colors = []
    for i in range(box[0][0], box[1][0]):
        for j in range(box[0][1], box[2][1]):
            colors.append(tuple(img[j][i]))
    return max(set(colors), key=colors.count)

def draw_boxes(drawer, result, outline = None, color = None, img = None):
    """
    Draws boxes on the place of the text coordinates
    Can be used to show text outline or cover old text with box
    
    """
    wight = []
    height = []
    if len(result[0]) == 3: # if the result contains probabilities
      for (coord, _, _) in result:
      
        (topleft, topright, bottomright, bottomleft) = coord
        tx, ty = (int(topleft[0]), int(topleft[1]))
        bx, by = (int(bottomright[0]), int(bottomright[1]))
        # cv.rectangle(img, (tx, ty), (bx, by), color, outline)
        if outline != None and color != None:
            color = most_frequent_color_in_box(img, [topleft, topright, bottomleft, bottomright])
            drawer.rectangle([(tx, ty), (bx, by)], fill = color, outline = outline)
        wight.append(np.abs(bx - tx))
        height.append(np.abs(by - ty))
    else: 
      for (coord, _) in result:
        (topleft, topright, bottomright, bottomleft) = coord
        tx, ty = (int(topleft[0]), int(topleft[1]))
        bx, by = (int(bottomright[0]), int(bottomright[1]))
        if outline != None or color != None:
            color = most_frequent_color_in_box(img, [topleft, bottomright, bottomleft, bottomright])
            drawer.rectangle([(tx, ty), (bx, by)], fill = color, outline = outline)

        wight.append(np.abs(bx - tx))
        height.append(np.abs(by - ty))

    return wight, height, color

def translator(text, from_language, to_language):
    """
    Translates the text and fit some letters to the Ukrainian alphabet
    
    """ 
    text_witho_comma = text.replace(',', '')
    try:
        value = int(text_witho_comma)
        return str(value)
    except ValueError:
        pass


    translate = ts.translate_text(text, from_language=from_language, to_language=to_language)
    return translate

def getCoordinates(result): # get the coordinates of the text boxes
  coordinates = [i[0] for i in result]
  return coordinates

def isInParagraph(parCoords, lineCoords): # check if the paragraph is in the line
  if parCoords[0][0] <= lineCoords[0][0] and parCoords[1][0] >= lineCoords[1][0] and parCoords[0][1] <= lineCoords[0][1]:
    return True
  else:
    return False

def extrLineHeight(paragraphs, lines):
  parCoords = getCoordinates(paragraphs)
  lineCoords = getCoordinates(lines)
  firstLineHeight = []
  for i in range(len(parCoords)):
    for j in range(len(lineCoords)):
      if isInParagraph(parCoords[i], lineCoords[j]):
        firstLineHeight.append(np.abs(lineCoords[i][0][1] - lineCoords[i][2][1]))
        break
  return firstLineHeight



def textWrap(text, firstLineHeight, boxesWight, parHeight, font, fontsize):
    textToWrite = text[1].split(' ')
    length = font.getlength(text[1])

    if length == boxesWight:
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
    
def textWrite(text_to_write, wight, firstLineHeight, parHeights, drawer, color, from_language='auto', to_language='en'):
  """
  Function that puts text into the image

  """

  for i in range(len(text_to_write)):
    translate = translator(text_to_write[i][1], from_language=from_language, to_language=to_language)

    translate = [text_to_write[i][0], translate]
    fontsize = int(parHeights[i] / (int(parHeights[i]/firstLineHeight[i])+1) * 0.9)
    font = ImageFont.truetype("arial.ttf", fontsize)
    lines, coords, new_font = textWrap(translate, firstLineHeight[i], wight[i], parHeights[i], font, fontsize)
    font = new_font
    for i in range(len(lines)):
        drawer.text(coords[i], lines[i], fill=(255 - color[0], 255 - color[1], 255 - color[2]), font=font)
       


root = tk.Tk()
root.title("Text from image translator")
root.geometry('400x200+300+200') 

label = tk.Label(root, text="File path")
label.grid(row=0, column=0)

filepath = ""

language = "English"

lang_list = ["English", "Ukrainian", "Russian", "Polish"]

value_inside = tk.StringVar(root)
  
# Set the default value of the variable
value_inside.set("Select an Option")
  
# Create the optionmenu widget and passing 
# the options_list and value_inside to it.
question_menu = tk.OptionMenu(root, value_inside, *lang_list)
question_menu.grid(row=1, column=0)


def print_answers():
    print("Selected Option: {}".format(value_inside.get()))
    global language
    language = value_inside.get()
    return None

submit_button = tk.Button(root, text='Submit', command=print_answers)



# открываем файл в текстовое поле
def open_file():
    global filepath
    filepath = filedialog.askopenfilename()

def save_file():
    global image
    filename = filedialog.asksaveasfile(initialfile = 'result.png',
defaultextension=".png",filetypes=[("All Files","*.*"),("PNG","*.png"), ("JPEG", "*.jpg")])
    image.save(filename)

def main(language, filepath, new_window):
    global image, drawer, result, text_to_translate, wight, height, color, parHeights, translated
    img = load_resize(filepath)
    image = Image.fromarray(img)
    drawer = ImageDraw.Draw(image)

    reader = easyocr.Reader(['ru', 'en', 'uk'])
    result = reader.readtext(img)
    
    text_to_translate = makeLines(result) # it makes a paragraph from text parts from easyocr output
    

    wight, height, color = draw_boxes(drawer, text_to_translate, outline = None, color = "white", img = img)

    text_to_translate_par, parHeights = makeParagraphs(text_to_translate) # it makes a paragraph from text parts from easyocr output

    hights = extrLineHeight(text_to_translate_par, text_to_translate)

    wight, height, _ = draw_boxes(drawer, text_to_translate_par, outline = None, color = None)

    textWrite(text_to_translate_par, wight, hights, parHeights, drawer, color, from_language='auto', to_language=language)

    new_window.destroy()

    final_window = tk.Tk()
    final_window.title("Translated text")
    final_window.attributes('-topmost', True)

    translated = ImageTk.PhotoImage(image)

    image_size = (f"{image.size[0]}x{image.size[1]+100}")
    final_window.geometry(f'{image_size}+300+200')
    label = tk.Label(
    final_window,
    image=translated,
    # compound='top'
    )
    label.grid(row=0, column=0)
    open_button = ttk.Button(text="Save file", command=save_file)
    open_button.grid(row=1, column=0)
    final_window.mainloop()
    
    

def translating():
    global root, filepath, language
    if language == "English":
            language = "en"
    if language == "Ukrainian":
        language = "uk"
    if language == "Russian":
        language = "ru"
    if language == "Polish":
        language = "pl"

    root.destroy()

    new_window = tk.Tk()
    new_window.geometry('400x200+300+200')
    new_window.title("Translating...")
    tk.Label(new_window, text="Translating...").place(x=0, y=0)
    new_window.after(1, lambda: main(language, filepath, new_window))
    new_window.mainloop()
    # main(language, filepath, new_window)



open_button = ttk.Button(text="Open file", command=open_file)

open_button.grid(row=0, column=1)

open_button = ttk.Button(text="Translate", command=translating)

open_button.grid(row=3, column=0)

root.mainloop()
