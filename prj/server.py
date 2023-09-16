# Christopher O'Grady
# R00067022
# christopher.ogrady@mycit.ie

# TODO : bugs do exist, user input is not cleaned, must be lowercase
#   and accented letters in read file will make game impossible,
#   already guessed letters still report a hit to the user, game only runs properly once

from concurrent import futures
import random

import grpc
import game_pb2
import game_pb2_grpc


# decorator to turn letters lowercase and clean '\n'
def clean_string(func):
    def wrapper(*args, **kwargs):
        clean = func(*args, **kwargs)
        return [line.lower().rstrip("\n") for line in clean]
    return wrapper


# reads phrase from file, uses decorator
@clean_string
def phrase_lookup():
    temp_array = []
    with open("phrases.txt") as temp_file:
        for line in temp_file:
            temp_array.append(line)
    return temp_array


# populates a list the same size as phrase read and fills in '_' for letters and spaces
def populate_mystery_list(myst):
    mystery = myst
    counter = 0
    for x in myst:
        if x == "'" or x == "-" or x ==",":
            mystery[counter] = myst[counter]
        else:
            mystery[counter] = "_"
        counter += 1
    return mystery


# singleton implementation, only 1 can exist
class LookupCacheSingleton:
    __instance = None

    # returns a random phrase in the populated list
    def random_phrase(self):
        return random.choice(self.phrase_list)

    # creates an instance if there is none
    @staticmethod
    def get_instance():
        if LookupCacheSingleton.__instance is None:
            LookupCacheSingleton(phrase_lookup())
        return LookupCacheSingleton.__instance

    def __init__(self, phrase_list):
        if LookupCacheSingleton.__instance is not None:
            print("new phrase fetched")
        else:
            self.phrase_list = phrase_list
            LookupCacheSingleton.__instance = self


# our game round
class GameRound(game_pb2_grpc.GameRoundServicer):

    def __init__(self):
        self.game_on = True
        self.guess_status = "miss"
        self.answer_list = []
        self.mystery_list = []

        # answer and mystery list to be generated from singleton
        cache = LookupCacheSingleton.get_instance()
        answer = cache.random_phrase()
        self.answer_list = list(answer)
        self.mystery_list = populate_mystery_list(list(answer))
        # only display on server tab for testing purposes
        print(self.answer_list)

    # check if guess is in phrase
    def is_it_there(self, req):
        counter = 0
        for x in self.answer_list:
            if x == req:
                self.mystery_list[counter] = req
                self.guess_status = "hit!"
            counter += 1

    # if the input is greater than 1 letter, we interpret it as a full guess, if correct game over
    def guess_the_word(self, req):
        word = list(req)
        if word == self.answer_list:
            self.mystery_list = self.answer_list
            self.guess_status = "Correct guess of the phrase!"
            self.game_on = False
        else:
            self.guess_status = "Wrong guess of the phrase!"

    # if word is fully guessed, game is over
    def is_game_continuing(self):
        if self.mystery_list == self.answer_list:
            return False
        else:
            return True

    # returns output to client
    def guess_letter(self, request, context):
        self.guess_status = "miss!"
        if len(request.single_guess) > 1:
            self.guess_the_word(request.single_guess)
        else:
            self.is_it_there(request.single_guess)
        self.game_on = self.is_game_continuing()
        return game_pb2.ServerOutput(message='\n\n\n\n\nPlayer has guessed: \"{0}\" That\'s a {1}\n {2}\n\n'
                                     .format(request.single_guess, self.guess_status, self.mystery_list),
                                     game_continue=self.game_on)


# runs the server
def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    game_pb2_grpc.add_GameRoundServicer_to_server(GameRound(), server)
    server.add_insecure_port('[::]:50051')
    print("Game Server Opened,\n THIS TAB IS FOR ADMIN ONLY")
    server.start()
    server.wait_for_termination()


server()
