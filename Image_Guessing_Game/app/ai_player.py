import operator
import collections
from app import query_db
from app.imagelabelreader import ImageLabelReader
import random


class AiEngine:
    def __init__(self):
        self.__ai_play_sequence = {}
        self.__images_for_ai = {}
        self.__image_label_reader = None

    # Updates the playlist with new optimal plays.
    def generate_playlist(self, ilr):
        self.__image_label_reader = ilr
        list_of_files = query_db(
            'SELECT COUNT(points), imagepath FROM Games GROUP BY imagepath ORDER BY COUNT(points) DESC;')
        if list_of_files is None:
            print('No plays to generate')
        for file in list_of_files:
            previous_played = self.__get_previous_played(file['imagepath'])
            nr_pieces = len(self.__image_label_reader.getAllSections(file['imagepath']))
            sequence = self.__calculate_optimal_play(previous_played, nr_pieces)
            self.__ai_play_sequence[file['imagepath']] = sequence

    # Get image filename for image with enough statistics
    def get_random_image(self):
        if len(self.__ai_play_sequence.items()) > 0:
            filename, sequence = random.choice(
                list(self.__ai_play_sequence.items()))
            return filename, sequence
        return None, None

    # Get array with statistics for image
    def __get_previous_played(self, image_name):
        list_of_files = query_db('SELECT imagepath, proposedimages, successrate FROM Games WHERE imagepath = "{}";'.
                                 format(image_name))
        if list_of_files is None:
            print('No image_name matching played games')
        else:
            previous_plays = []
            for file in list_of_files:
                values = {
                    'filename': file['imagepath'],
                    'successrate': file['successrate'],
                    'proposed': file['proposedimages'].replace('[', '').replace(']', '').replace('\'', '').split(",")
                }
                previous_plays.append(values)
            return previous_plays

    # Calculates the optimal play for an image
    @staticmethod
    def __calculate_optimal_play(previous, nr_segments):
        main_list = [0]*nr_segments

        for attempt in previous:
            for i in range(len(attempt['proposed'])):
                if(len(attempt['proposed'][i].strip())) > 0:
                    p = (int(attempt['proposed'][i].strip()))
                    main_list[p] += (nr_segments-i+1)*attempt['successrate']

        statistics = {}
        for e in range(len(main_list)):
            statistics[e] = str(round(main_list[e], 3))

        sorted_return_statistics = sorted(
            statistics.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

        calculated_order = []
        for key, _ in sorted_return_statistics:
            calculated_order.append(key)
        return calculated_order
