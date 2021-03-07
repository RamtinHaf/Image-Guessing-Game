import unittest
from app.models import User, Game, ImageGameController, Player, GameState, GameMode
from app.imagelabelreader import ImageLabelReader
import app
from app.routes import IGC
from app.forms import LoginForm
from flask import Flask

ILR = ImageLabelReader()

class TestImageLabelReader(unittest.TestCase):
    def test_get_random_image(self):
        global ILR
        for num in range(0, 1000):
            self.assertIsNotNone(ILR.getRandomImage())

    def test_get_all_sections(self):
        global ILR
        testfile = "ILSVRC2012_val_00000532"
        response = ILR.getAllSections(testfile)
        self.assertEqual(len(response), 49)

        testfile = "ILSVRC2012_val_00002067"
        response = ILR.getAllSections(testfile)
        self.assertEqual(len(response), 49)

        testfile = "ILSVRC2012_val_00001671"
        response = ILR.getAllSections(testfile)
        self.assertEqual(len(response), 47)

        testfile = "ILSVRC2012_val_00001981"
        response = ILR.getAllSections(testfile)
        self.assertEqual(len(response), 43)

        testfile = "ILSVRC2012_val_00000872"
        response = ILR.getAllSections(testfile)
        self.assertEqual(len(response), 49)

    def test_get_label(self):
        global ILR

        label = ILR.getLabel("ILSVRC2012_val_00000090")
        self.assertEqual(label, "American alligator")

        label = ILR.getLabel("ILSVRC2012_val_00000343")
        self.assertEqual(label, "llama")

        label = ILR.getLabel("ksjdshsjdhsjdh")
        self.assertIsNone(label)


class TestSocketGame(unittest.TestCase):
    def setUp(self):
        with app.app.app_context():
            app.query_db('INSERT INTO Users (username, password) VALUES("Test123", "Test123");')
            user = tuple(app.query_db('SELECT * FROM Users WHERE username="Test123";', one=True))
        with app.app.test_client() as c:
            test_client = c
            with c.session_transaction() as sess:
                sess['user_id'] = str(user[0])
                sess['_fresh'] = True
        test_client.post('/', )
        test1 = app.socketio.test_client(app.app,flask_test_client=test_client)
        test2 = app.socketio.test_client(app.app,flask_test_client=test_client)
        test3 = app.socketio.test_client(app.app,flask_test_client=test_client)
        test4 = app.socketio.test_client(app.app,flask_test_client=test_client)
        self.test_ws_clients =[test1,test2,test3,test4]
    
    def tearDown(self):
        with app.app.app_context():
            app.query_db('DELETE FROM Users WHERE username="Test123";')

    def test_join_game_multiplayer(self):
        game = Game()
        IGC.add_game(game)   
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.assertEqual(game.get_numbers_of_players(),1)
        self.assertEqual(game.get_proposer(),None)
        self.test_ws_clients[1].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        self.test_ws_clients[2].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        recieved = self.test_ws_clients[2].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Game alredy have proposer!")
        self.assertEqual(game.get_numbers_of_players(),2)
        self.test_ws_clients[0].emit("request_start",{"game_id":game.get_id()})
        self.test_ws_clients[3].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        recieved = self.test_ws_clients[3].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Game already started!")
        

    def test_join_game_singleplayer(self):
        game = Game()
        game.set_gamemode(GameMode.SINGLEPLAYER)
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        recieved = self.test_ws_clients[0].get_received()
        for callback in recieved:
            self.assertFalse(callback["name"] == "leave_game")
        self.test_ws_clients[1].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        recieved = self.test_ws_clients[1].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Game alredy have proposer!")
        self.test_ws_clients[2].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        recieved = self.test_ws_clients[2].get_received()
        for callback in recieved:
            self.assertFalse(callback["name"] == "leave_game")
        self.assertTrue(game.get_state() == GameState.STARTED)
        self.test_ws_clients[3].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        recieved = self.test_ws_clients[3].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Game already started!")
        self.assertEqual(game.get_numbers_of_players(),2)
    
    def test_join_game_ai(self):
        game = Game()
        game.set_gamemode(GameMode.AI)
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        recieved = self.test_ws_clients[0].get_received()
        for callback in recieved:
            self.assertFalse(callback["name"] == "leave_game")
        self.assertTrue(game.get_state() == GameState.STARTED)
        self.test_ws_clients[1].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        recieved = self.test_ws_clients[1].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Game already started!")
        self.assertEqual(game.get_numbers_of_players(),1)
    
    def test_leave_game_multiplayer(self):
        game = Game()
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        for i in range(1,4):
            self.test_ws_clients[i].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].emit("request_start",{"game_id":game.get_id()},room=game.get_id())
        self.assertTrue(game.get_state() == GameState.STARTED)
        self.test_ws_clients[3].emit("leaving_game",{"game_id":game.get_id()},room=game.get_id())
        recieved = self.test_ws_clients[3].get_received()
        for callback in recieved:
            self.assertFalse(callback["name"] == "leave_game")
        self.test_ws_clients[0].get_received()
        self.test_ws_clients[1].get_received()
        self.test_ws_clients[2].get_received()
        self.test_ws_clients[0].emit("leaving_game",{"game_id":game.get_id()},room=game.get_id())
        for i in range(1,3):
            recieved = self.test_ws_clients[i].get_received()[0]
            self.assertEqual(recieved["name"],"leave_game")
            self.assertEqual(recieved["args"][0]["reason"],"Proposer left!")
        self.assertFalse(IGC.get_game_by_id(game.get_id()))

        
    def test_leave_game_singleplayer(self):
        game = Game()
        game.set_gamemode(GameMode.SINGLEPLAYER)
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        self.test_ws_clients[1].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].get_received()
        self.test_ws_clients[1].get_received()
        self.test_ws_clients[0].emit("leaving_game",{"game_id":game.get_id()},room=game.get_id())
        recieved = self.test_ws_clients[1].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Proposer left!")
        self.assertFalse(IGC.get_game_by_id(game.get_id()))
        game = Game()
        game.set_gamemode(GameMode.SINGLEPLAYER)
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        self.test_ws_clients[1].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].get_received()
        self.test_ws_clients[1].get_received()
        self.test_ws_clients[1].emit("leaving_game",{"game_id":game.get_id()},room=game.get_id())
        recieved = self.test_ws_clients[0].get_received()[0]
        self.assertEqual(recieved["name"],"leave_game")
        self.assertEqual(recieved["args"][0]["reason"],"Not enough players in the game!")
        self.assertFalse(IGC.get_game_by_id(game.get_id()))
    
    def test_leave_game_ai(self):
        game = Game()
        game.set_gamemode(GameMode.AI)
        IGC.add_game(game)
        self.assertTrue(IGC.get_game_by_id(game.get_id()))
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].emit("leaving_game",{"game_id":game.get_id()},room=game.get_id())
        self.assertFalse(IGC.get_game_by_id(game.get_id()))
    
    def test_handle_guess(self):
        game = Game()
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        for i in range(1,4):
            self.test_ws_clients[i].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].emit("request_start",{"game_id":game.get_id()},room=game.get_id())
        for i in range(4):
            self.test_ws_clients[i].get_received()
        self.test_ws_clients[1].emit("new_guess",{"guess":"test1","game_id":game.get_id()},room=game.get_id())
        for i in range(4):
            recieved = self.test_ws_clients[i].get_received()[0]
            self.assertEqual(recieved["name"],"new_guess")
            self.assertEqual(recieved["args"][0]["guess"],"test1")
        self.test_ws_clients[2].emit("new_guess",{"guess":game.get_label(),"game_id":game.get_id()},room=game.get_id())
        for i in range(4):
            recieved = self.test_ws_clients[i].get_received()[0]
            self.assertEqual(recieved["name"],"game_finish")
            self.assertEqual(recieved["args"][0]["score"],game.get_points())
        self.assertEqual(game.get_state(),GameState.FINISHED)
    
    def test_chat(self):
        game = Game()
        IGC.add_game(game)
        self.test_ws_clients[0].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":True},room=game.get_id())
        for i in range(1,3):
            self.test_ws_clients[i].emit("join_game",{"game_id":game.get_id(),"user_id":"1","proposer":False},room=game.get_id())
        self.test_ws_clients[0].emit("request_start",{"game_id":game.get_id()},room=game.get_id())
        for i in range(3):
            self.test_ws_clients[i].get_received()
        self.test_ws_clients[2].emit("chat",{"game_id":game.get_id(),"message":"hello"},room=game.get_id())
        for i in range(3):
            recieved = self.test_ws_clients[i].get_received()[0]
            self.assertEqual(recieved["name"],"chat")
            self.assertEqual(recieved["args"][0]["message"],"hello")
        recieved = self.test_ws_clients[3].get_received()
        for callback in recieved:
            self.assertFalse(callback["name"] == "chat")


class TestGame(unittest.TestCase):

    def test_get_image_path(self):
        game = Game()
        self.assertIsNotNone(game.get_imagePath())

        game = Game()
        self.assertIsNotNone(game.get_imagePath())

        game = Game()
        self.assertIsNotNone(game.get_imagePath())
    

    def test_get_proposed_images(self):
        game = Game()
        game.add_proposedImage('1.png')
        game.add_proposedImage('3.png')
        game.add_proposedImage('9.png')
        game.add_proposedImage('10.png')

        proposed_images = game.get_proposedImages()

        self.assertEqual(proposed_images[0], '1.png')
        self.assertEqual(proposed_images[1], '3.png')
        self.assertEqual(proposed_images[2], '9.png')
        self.assertEqual(proposed_images[3], '10.png')

    
    def test_get_points(self):

        for i in range(100):
            game = Game()
            
            num_images = len(game.get_allImages())
            for i in range(0,9):
                game.add_proposedImage(i)
            numProposedImages = len(game.get_proposedImages())
            self.assertEqual(game.get_points(), num_images - numProposedImages)

class TestImageGameController:
    pass
    
if __name__ == '__main__':
    unittest.main()
