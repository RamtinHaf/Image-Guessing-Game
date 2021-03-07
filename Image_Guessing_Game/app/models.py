from app import app, query_db, get_userbyid
from flask import url_for
from enum import Enum
from datetime import datetime
from threading import Lock
from flask_login import UserMixin
from app.imagelabelreader import ImageLabelReader
from flask_socketio import emit, send, close_room, join_room
import uuid
import re


class User(UserMixin):
    def __init__(self, id):
        self.id = id


class Game:
    IMAGE_LABEL_READER = ImageLabelReader()

    def __init__(self):
        self.__id = str(uuid.uuid4())
        self.__guessers = []
        self.__start_game = datetime.now()
        self.__proposer = None
        self.__imagePath = self.IMAGE_LABEL_READER.getRandomImage()
        self.__label = self.IMAGE_LABEL_READER.getLabel(self.__imagePath)
        self.__allImages = self.IMAGE_LABEL_READER.getAllSections(
            self.__imagePath)
        self.__finished = False
        self.__proposedImages = []
        self.__ai_best_proposed = []
        self.__successRate = 0
        self.__lastPropose = 0
        self.__state = GameState.NOTSTARTED
        self.__gameMode = GameMode.MULTIPLAYER
        self.__playerlist_lock = Lock()

    def get_image_label_reader(self):
        return self.IMAGE_LABEL_READER

    def get_imagePath(self):
        return self.__imagePath

    def set_imagePath(self, imagepath):
        self.__imagePath = imagepath

    def get_ai_best_proposed(self):
        return self.__ai_best_proposed

    def set_ai_best_proposed(self, proposed_images):
        self.__ai_best_proposed = proposed_images

    def set_proposer(self, proposer):
        self.__proposer = proposer
        if self.valid_game():
            emit("status_changed", {"status": "valid"}, room=self.__id)

    def add_guesser(self, guesser):
        self.__guessers.append(guesser)
        if self.__proposer and len(self.__guessers) == 1:
            emit("status_changed", {"status": "valid"}, room=self.__id)

    def get_label(self):
        return self.__label

    def set_label(self, label):
        self.__label = label

    def get_state(self):
        return self.__state

    def get_gamemode(self):
        return self.__gameMode

    def get_gamemode_string(self):
        return str(self.__gameMode)

    def set_gamemode(self, gamemode):
        self.__gameMode = gamemode

    def get_guessers(self):
        return self.__guessers

    def get_proposer(self):
        return self.__proposer

    def get_status(self):
        return self.__finished

    def get_allImages(self):
        return self.__allImages

    def get_proposedImages(self):
        return self.__proposedImages

    def add_proposedImage(self, imgName):
        if imgName not in self.__proposedImages:
            self.__proposedImages.append(imgName)

    def get_successRate(self):
        return 1 - (len(self.__proposedImages) / len(self.__allImages))
    
    def is_all_proposed(self):
        if self.__gameMode is GameMode.AI and len(self.get_ai_best_proposed()) == 0:
            return True
        if self.__gameMode is GameMode.SINGLEPLAYER and len(self.__allImages) == len(self.__proposedImages):
            return True
        return False

    def finish(self):
        self.__finished = True

    def saveGameInDatabase(self, winner):
        if self.get_gamemode() != GameMode.AI:
            query_db('INSERT INTO Games (id, guessers, proposer, imagepath, label, proposedimages, points, successrate ) VALUES("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}");'.format(
                self.__id, winner, self.get_proposer().get_uid(), self.__imagePath, self.__label, self.__proposedImages, self.get_points(), self.get_successRate()))

            guesser = query_db(
                'SELECT points FROM Users WHERE id="{}";'.format(winner), one=True)
            old_points = guesser['points']
            updated_points = self.get_points() + old_points
            query_db('UPDATE Users SET points = "{}" WHERE id="{}";'.format(
                updated_points, winner))

            proposer = query_db(
                'SELECT points FROM Users WHERE id="{}";'.format(self.get_proposer().get_uid()), one=True)
            old_points = proposer['points']
            updated_points = self.get_points() + old_points
            query_db('UPDATE Users SET points = "{}" WHERE id="{}";'.format(
                updated_points, self.get_proposer().get_uid()))

    def get_points(self):
        return len(self.__allImages) - len(self.__proposedImages)

    def get_numbers_of_players(self):
        result = len(self.__guessers)
        if self.__proposer:
            result = result + 1
        return result

    def get_id(self):
        return self.__id

    def is_multiplayer(self):
        return self.__gameMode == GameMode.MULTIPLAYER

    def handle_new_guess(self, sid, guess):
        with self.__playerlist_lock:
            if self.__state != GameState.STARTED:
                return False
            guesser = self.find_guesser_by_sid(sid)
            if guesser:
                guesser.new_guess()
                if re.sub(r'[^A-Za-z]', '', self.__label.lower()) == re.sub(r'[^A-Za-z]', '', guess.lower()):
                    self.__state = GameState.FINISHED
                    emit("game_finish", {"is_winner":True,"winner": guesser.get_username(), "score": self.get_points()}, room=self.__id)
                    self.saveGameInDatabase(guesser.get_uid())
                    return True
                else:
                    emit("new_guess", {
                        "user": guesser.get_username(), "guess": guess}, room=self.__id)
                if not self.__gameMode == GameMode.MULTIPLAYER:
                    if guesser.get_guesses() - self.__lastPropose > 2:
                        if self.is_all_proposed():
                            emit("game_finish", {"is_winner":False}, room=self.__id)
                        if self.__gameMode == GameMode.SINGLEPLAYER:
                            emit("status_changed", {
                                "status": "ready_propose"}, room=self.__id)
                            emit("status_changed", {
                                "status": "block_guessing", "open": False}, room=self.__id)
                        else:
                            self.__lastPropose = self.__guessers[0].get_guesses()
                            next_proposed_image = self.get_ai_best_proposed().pop(0)
                            self.__proposedImages.append(next_proposed_image)
                            emit("new_image", {"image": next_proposed_image, "path": self.get_imagePath()}, room=self.__id)
                            if len(self.get_ai_best_proposed()) < 1:
                                 emit("status_changed", {"status": "last_proposed"}, room=self.__id)
            return False

    def find_proposer_by_sid(self, sid):
        if self.__proposer.get_sid() == sid:
            return self.__proposer
        return None

    def find_guesser_by_sid(self, sid):
        for guesser in self.__guessers:
            if guesser.get_sid() == sid:
                return guesser
        return None
    
    def remove_guesser_by_sid(self,sid):
        for i in range(len(self.__guessers)):
            if self.__guessers[i].get_sid() == sid:
                del self.__guessers[i]

    def valid_game(self):
        return self.__proposer and len(self.__guessers) > 0

    def add_player(self, uid, sid, is_proposer):
        with self.__playerlist_lock:
            if self.get_state() == GameState.STARTED:
                return "Game already started!"
            if is_proposer:
                if self.__proposer:
                    return "Game alredy have proposer!"
                else:
                    newPlayer = Player(uid, sid)
                    self.set_proposer(newPlayer)
                    emit("new_player", {
                        "user": newPlayer.get_username()}, room=self.get_id())
                    join_room(self.__id)
                    if not self.is_multiplayer() and self.valid_game():
                        self.start_game()
                    return ""
            if not self.is_multiplayer() and len(self.get_guessers()) > 0:
                return "To many players!"
            newPlayer = Player(uid, sid)
            self.add_guesser(newPlayer)
            emit("new_player", {"user": newPlayer.get_username()}, room=self.__id)
            join_room(self.__id)
            if self.get_gamemode() == GameMode.SINGLEPLAYER and self.valid_game() or self.get_gamemode() == GameMode.AI:
                self.start_game()
            return ""

    def remove_player(self, sid):
        with self.__playerlist_lock:
            if self.__proposer and self.__proposer.get_sid() == sid:
                if self.__state == GameState.NOTSTARTED:
                    if self.get_numbers_of_players() < 2:
                        return True
                    self.__proposer = None
                else:
                    return_player_to_home("Proposer left!", self.__id)
                    return True
            else:
                player = self.find_guesser_by_sid(sid)
                if player:
                    if self.__state == GameState.NOTSTARTED:
                        if self.get_numbers_of_players() < 2:
                            self.remove_guesser_by_sid(sid)
                            return True
                        elif self.__proposer and len(self.__guessers) < 2:
                            self.remove_guesser_by_sid(sid)
                            emit("status_changed", {
                                "status": "notvalid"}, room=self.__id)
                        self.remove_guesser_by_sid(sid)
                        emit("leaved_game", {
                            "user": player.get_username()}, room=self.__id)
                    else:
                        if len(self.__guessers) < 2:
                            return_player_to_home("Not enough players in the game!", self.__id)
                            return True
                        else:
                            self.remove_guesser_by_sid(sid)
                            emit("leaved_game", {
                                "user": player.get_username()}, room=self.__id)
            return False

    def remove_all_players(self, igc):
        for guesser in self.__guessers:
            igc.remove_player(guesser.get_sid())
        if self.__proposer:
            igc.remove_player(self.__proposer.get_sid())

    def start_game(self):
        if self.valid_game() or self.__gameMode == GameMode.AI:
            self.__state = GameState.STARTED
            emit("status_changed", {"status": "started","label": self.__label}, room=self.__id)
        else:
            emit("status_changed", {"status": "notvalid"}, room=self.__id)

    def handle_new_propose(self, sid, image):
        if sid == self.__proposer.get_sid():
            self.__proposedImages.append(image)
            emit("new_image", {"image": image,
                               "path": self.get_imagePath()}, room=self.__id)
            if self.__gameMode == GameMode.SINGLEPLAYER:
                player = self.__guessers[0]
                if player:
                    self.__lastPropose = player.get_guesses()
                    if self.is_all_proposed():
                        emit("status_changed", {"status": "last_proposed"}, room=self.__id)
                    emit("status_changed", {"status": "block_guessing", "open": True}, room=self.__id)

    def request_propose(self, sid):
        player = self.find_guesser_by_sid(sid)
        if player:
            self.__lastPropose = player.get_guesses()
            if self.__gameMode == GameMode.SINGLEPLAYER:
                emit("status_changed", {
                     "status": "ready_propose"}, room=self.__id)
            else:
                self.__lastPropose = self.__guessers[0].get_guesses()
                next_proposed_image = self.get_ai_best_proposed().pop(0)
                self.__proposedImages.append(next_proposed_image)
                emit("new_image", {"image": next_proposed_image, "path": self.get_imagePath()}, room=self.__id)
                if self.is_all_proposed():
                    emit("status_changed", {"status": "last_proposed"}, room=self.__id)

    def is_uid_in_game(self, uid):
        if self.__proposer:
            if self.__proposer.get_uid() == uid:
                return True
        for guesser in self.__guessers:
            if guesser.get_uid() == uid:
                return True
        return False


class ImageGameController:
    def __init__(self):
        self.__activeGames = {}
        self.__playersInGame = {}

    def add_game(self, game):
        self.__activeGames[game.get_id()] = game
        return True

    def get_game_by_id(self, gameId):
        if gameId in self.__activeGames:
            return self.__activeGames[gameId]
        return None

    def remove_game(self, game):
        if game.get_id() in self.__activeGames:
            del self.__activeGames[game.get_id()]
            return True

    def remove_game_by_id(self, gameId):
        del self.__activeGames[gameId]
        return True

    def get_games_to_join(self):
        result = []
        for game_id in self.__activeGames:
            game = self.__activeGames[game_id]
            if game.get_state() == GameState.NOTSTARTED:
                result.append(game)
        return result

    def get_games(self):
        return self.__activeGames

    def add_player_to_game(self, game, sid):
        self.__playersInGame[sid] = game

    def get_game_from_player(self, sid):
        if sid in self.__playersInGame:
            return self.__playersInGame[sid]
        return None

    def remove_player(self, sid):
        if sid in self.__playersInGame:
            del self.__playersInGame[sid]


class Player:
    def __init__(self, user_id, sid):
        self.__user_id = user_id
        self.__sid = sid
        user = get_userbyid(user_id)
        self.__username = user['username']
        self.__score = user['points']
        self.__block_guessing = False
        self.__guesses = 0

    def get_sid(self):
        return self.__sid

    def get_uid(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_guess_blocking(self):
        return self.__block_guessing

    def set_guess_blocking(self, block):
        self.__block_guessing = block

    def set_score(self, score):
        self.__score = self.__score + score

    def get_score(self):
        return self.__score

    def get_guesses(self):
        return self.__guesses

    def new_guess(self):
        self.__guesses = self.__guesses + 1


class GameState(Enum):
    NOTSTARTED = 0
    STARTED = 1
    FINISHED = 2


class GameMode(Enum):
    MULTIPLAYER = 0
    SINGLEPLAYER = 1
    AI = 2


def return_player_to_home(reason, id):
    sending = {
        "url": url_for('dashboard'),
        "reason": reason
    }
    emit("leave_game", sending, room=id)
    close_room(room=id)
