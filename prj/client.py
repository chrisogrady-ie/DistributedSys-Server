# Christopher O'Grady
# R00067022
# christopher.ogrady@mycit.ie

import grpc

import game_pb2
import game_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = game_pb2_grpc.GameRoundStub(channel)
        response = stub.guess_letter(game_pb2.ClientInput(single_guess=" "))
        print(response.message)

        game_on = True
        while game_on:
            user_guess = input("What letter would you like?:")
            response = stub.guess_letter(game_pb2.ClientInput(single_guess=user_guess))
            print(response.message)
            # uses the server response to know if the word has been guessed
            game_on = response.game_continue
        print("Player wins!\n- - - - - -G A M E  O V E R - - - - - -")


run()
