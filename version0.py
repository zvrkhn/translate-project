import easyocr
import cv2 as cv
import imutils as im
import translators as ts
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
    if abs(diff_x) < 30 and abs(diff_y) < 30:
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

  lines = [result[0][1]]
  coordinates = [result[0][0]]
  for i in range(1, len(result)):

    diff_y = result[i][0][0][1] - coordinates[-1][2][1]
    if diff_y < 5:
      lines[-1] += " " + result[i][1]
      coordinates[-1] = makeParagraphsCoordinates(coordinates[-1], result[i][0])
      
    else: 
      lines.append(result[i][1])
      coordinates.append(result[i][0])

  return list(zip(coordinates, lines))


def textSplit(text, text_scale, img_shape): # split the text into two lines if it is too long to fit in the image 
  """
  Check if the text fits in the image wight - 20 pixels from the right side to make it look better and 
  split it into two lines if it is too long

  """
  split = text.split(" ")
  first_line = split[0] + " "
  second_line = ""
  for i in range(1, len(split)):
    text_width, _ = cv.getTextSize(first_line + split[i], cv.FONT_HERSHEY_COMPLEX, text_scale, 1)

    if text_width + 20 < img_shape[1]:
      first_line += split[i] + " "
    else:
      second_line += split[i] + " "
      second_line += " ".join(split[i+1:])
      break
  return first_line, second_line
  # for i in range(1, len(split)):
  #   (text_width, _), _ = cv.getTextSize(split[i], cv.FONT_HERSHEY_COMPLEX, text_scale, 1)
  #   (fl_width, _), _ = cv.getTextSize(first_line, cv.FONT_HERSHEY_COMPLEX, text_scale, 1)
  #   if text_width + fl_width < img_shape[1] - 20:
  #     first_line = first_line + split[i] + " "
  #   elif text_width + fl_width > img_shape[1] - 20:
  #     second_line = second_line + split[i] + " "
  #     for j in range(i+1, len(split)):
  #       second_line = second_line + split[j] + " "
  #     break
  # return first_line, second_line

def draw_boxes(img, result, wight = [], height = [], outline = -1, color = (255, 255, 255)):
  """
  Draws boxes on the place of the text coordinates
  Can be used to show text outline or cover old text with box
  
  """
  if len(result[0]) == 3: # if the result contains probabilities
    for (coord, _, _) in result:
    
      (topleft, _, bottomright, bottomleft) = coord
      tx, ty = (int(topleft[0]), int(topleft[1]))
      bx, by = (int(bottomright[0]), int(bottomright[1]))
      cv.rectangle(img, (tx, ty), (bx, by), color, outline)
      wight.append(np.abs(bx - tx))
      height.append(np.abs(by - ty))
    return img, wight, height
  else: 
    for (coord, _) in result:
    
      (topleft, _, bottomright, _) = coord
      tx, ty = (int(topleft[0]), int(topleft[1]))
      bx, by = (int(bottomright[0]), int(bottomright[1]))
      cv.rectangle(img, (tx, ty), (bx, by), color, outline)
      wight.append(np.abs(bx - tx))
      height.append(np.abs(by - ty))
    return img, wight, height

def load_resize(name): 
  """
  Reads and resizes the image to fit the screen

  """
  img = cv.imread(name)
  dimensions = img.shape
  img = im.resize(img, width=dimensions[1], height=dimensions[0])
  return img

def translator(text, from_language, to_language):
  """
  Translates the text and fit some letters to the Ukrainian alphabet
  
  """ 
  translate = ts.translate_text(text, from_language=from_language, to_language=to_language)
  translate = translate.translate(str.maketrans("І", "I"))
  return translate

def text_write_v1(text_to_write, wight, height, scale, font = cv.FONT_HERSHEY_COMPLEX):
  """
  First version of the function that puts the text into the image
  """
  for i in range(len(text_to_write)):
    first_line = ""
    second_line = ""

    # calculate the scale of the text
    text_scale = min(wight[i], height[i]) / (25 / scale)

    # translate the text
    translate = translator(text_to_write[i][1], from_language='ru', to_language='en')
    # draw the text
    (_, text_height), _ = cv.getTextSize(translate, font, text_scale, 1)
    first_line, second_line = textSplit(translate, text_scale, img.shape) # split the text into two lines if it is too long
    (x, y) = tuple([text_to_write[i][0][0][0], text_to_write[i][0][0][1] + 20]) # coordinates of the text
    cv.putText(img, first_line, (x, y), font, text_scale, (0, 0, 0), 1)
    second_line_y = y + text_height * 2  # coordinates of the second line
    cv.putText(img, second_line, (x, second_line_y), font, text_scale, (0, 0, 0), 1)
  return img


def getCoordinates(result): # get the coordinates of the text boxes
  coordinates = [i[0] for i in result]
  return coordinates

def isInParagraph(parCoords, lineCoords): # check if the paragraph is in the line
  if parCoords[0][0] <= lineCoords[0][0] and parCoords[1][0] >= lineCoords[1][0] and parCoords[0][1] <= lineCoords[0][1]:
    return True
  else:
    return False

# result is a list of coordinates and text

def extrFirstLineHeight(paragraphs, lines):
  parCoords = getCoordinates(paragraphs)
  lineCoords = getCoordinates(lines)
  firstLineHeight = []
  for i in range(len(parCoords)):
    for j in range(len(lineCoords)):
      if isInParagraph(parCoords[i], lineCoords[j]):
        firstLineHeight.append(np.abs(lineCoords[i][0][1] - lineCoords[i][2][1]))
        break
  return firstLineHeight

def getParWight(paragraphs):
  parCoords = getCoordinates(paragraphs)
  wights = [abs(i[0][0] - i[1][0]) for i in parCoords]
  return wights


# TODO : rewrite font size calculation based on the size of the text box

def textWrap(text, firstLineHeight, wight, text_font, scale, text_thickness, parHeight): # wrap the text if it is too long to fit in the image
  """
  Wraps the text if it is too long to fit in the image

  """
  lines = []
  coords = []
  text_scale = min(wight, firstLineHeight) / (25 / scale)
  (text_width, text_height), _ = cv.getTextSize(text[1], text_font, text_scale, text_thickness)

  lines_num = int(text_width/wight) + 1
  if text_height * lines_num > parHeight:
    text_scale = text_scale - text_scale * 0.22

  (text_width, text_height), _ = cv.getTextSize(text[1], text_font, text_scale, text_thickness)
  textToWrite = text[1].split(" ")
  lines.append(textToWrite[0])
  coords.append(tuple([text[0][0][0], int(text[0][0][1] + firstLineHeight * 0.5)]))
  for j in range(1, len(textToWrite)):
      (line_wigth, _), _ = cv.getTextSize(str(lines[-1] + " " + textToWrite[j]), text_font, text_scale, text_thickness)
      if line_wigth <= wight: 
        lines[-1] += " " + textToWrite[j]
      else:
        lines.append(textToWrite[j])
        coords.append(tuple([coords[-1][0], int(coords[-1][1] + firstLineHeight)]))
  return lines, coords, text_scale
  



def textWrite_v2(text_to_write, wight, firstLineHeight, scale, font=cv.FONT_HERSHEY_COMPLEX):
  """
  Second version of the function that puts text into the image

  """
  for i in range(len(text_to_write)):
    translate = translator(text_to_write[i][1], from_language='en', to_language='uk')

    translate = [text_to_write[i][0], translate]
    (_, parHeight), _ = cv.getTextSize(translate[1], font, scale, 1)
    lines, coords, text_scale = textWrap(translate, firstLineHeight[i], wight[i], font, scale, 1, parHeight)
    for i in range(len(lines)):
      cv.putText(img, lines[i], coords[i], font, text_scale, (0, 0, 0), 1)

  return img


if __name__ == "__main__":

  img = load_resize(r'C:\Users\1\Desktop\work\Project\test_images\twi.jpg')

  reader = easyocr.Reader(['ru', 'en'])
  result = reader.readtext(img)


  scale = 0.5

  text_to_translate = makeLines(result) # it makes a paragraph from text parts from easyocr output

  img, wight, height = draw_boxes(img, text_to_translate, outline = -1, color = (255, 255, 255))

  text_to_translate_par = makeParagraphs(text_to_translate) # it makes a paragraph from text parts from easyocr output

  hights = extrFirstLineHeight(text_to_translate_par, text_to_translate)
  wights = getParWight(text_to_translate_par)

  # for i in text_to_translate:
  #   print(i)
  # img = text_write_v1(text_to_translate_par, wight, height, scale) # stock function that puts the text into the image
  
  img = textWrite_v2(text_to_translate_par, wights, hights, scale)
  
  cv.imshow('img', img) # show the image with text
  cv.waitKey(0)
  cv.imwrite('result.jpg', img) # save the image with text

