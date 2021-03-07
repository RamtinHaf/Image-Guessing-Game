import os
import random
import math


class ImageLabelReader:

    def __init__(self):
        self.__images = {}
        with open("app/static/image_mapping.csv", 'r') as file:
            for line in file:
                splitted_line = line.split(' ')
                self.__images[splitted_line[0]
                              ] = splitted_line[1].replace("\n", '')

        self.__labels = {}
        with open("app/static/label_mapping.csv", 'r') as file:
            for line in file:
                splitted_line = line.split(' ', 1)
                self.__labels[splitted_line[0]
                              ] = splitted_line[1].replace("\n", '')

        self.__images_in_folder = {}
        with open("app/static/numImagesInFolder.txt", 'r') as file:
            for line in file:
                splitted_line = line.split(':')
                self.__images_in_folder[splitted_line[0]] = int(
                    splitted_line[1].replace("\n", ''))

    def getRandomImage(self):
        return random.choice(list(self.__images_in_folder.keys())).replace('_scattered', '')

    def getAllSections(self, image):
        numImages = self.__images_in_folder[image + '_scattered']
        images = []
        for i in range(0, numImages):
            images.append(str(i) + '.png')
        return images

    def getLabel(self, image):
        labelKey = self.__images.get(image + ".JPEG")
        label = self.__labels.get(labelKey)
        return label
