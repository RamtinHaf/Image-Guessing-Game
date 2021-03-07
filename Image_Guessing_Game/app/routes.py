from flask import render_template, flash, redirect, url_for, request
from app import app, query_db, ai_player, socketio, get_userbyid, get_best_players, argon2
from app.forms import IndexForm, DashboardForm
from datetime import datetime
from app import socketio
from flask_socketio import leave_room, join_room, emit, send
import os
from app.models import User, Game, ImageGameController, Player, GameMode, GameState
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from app.imagelabelreader import ImageLabelReader
# Image game controller
IGC = ImageGameController()

# Ai Engine starts
ai = ai_player.AiEngine()


# home page/login/registration
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.get_id() is not None:
        return redirect(url_for('dashboard'))

    form = IndexForm()

    if form.login.is_submitted() and form.login.submit.data:
        user = query_db(
            'SELECT * FROM Users WHERE username="{}";'.format(form.login.username.data), one=True)
        if user is None:
            flash('Sorry, this user does not exist!')
        elif argon2.check_password_hash(user['password'], form.login.password.data):
            login_user(User(user['id']))
            return redirect(url_for('dashboard'))
        else:
            flash('Wrong username or password')

    elif form.register.is_submitted() and form.register.submit.data:    
        user = query_db(
            'SELECT * FROM Users WHERE username="{}";'.format(form.register.username.data), one=True)
        if user is None:
            query_db('INSERT INTO Users (username, password) VALUES("{}", "{}");'.format(form.register.username.data, argon2.generate_password_hash(form.register.password.data)))
            flash('User created, please login!')
            return redirect(url_for('index'))
        else:
            flash("Try a another username, this one is already taken.")
            return redirect(url_for('index'))
    return render_template('index.html', title='Welcome', form=form)

# content dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = DashboardForm()
    if form.is_submitted() and form.new_game_guesser_multiPlayer.data:
        game = Game()
        game.set_gamemode(GameMode.MULTIPLAYER)
        # Setting userid to the guesser
        # game.add_guesser(current_user.get_id())
        IGC.add_game(game)
        return redirect(url_for('guesser', game_id=game.get_id()))

    if form.is_submitted() and form.new_game_proposer_multiPlayer.data:
        game = Game()
        game.set_gamemode(GameMode.MULTIPLAYER)
        # Setting userid to the proposer
        # game.set_proposer(current_user.get_id())
        IGC.add_game(game)
        return redirect(url_for('proposer', game_id=game.get_id()))

    if form.is_submitted() and form.new_game_guesser_singlePlayer.data:
        game = Game()
        game.set_gamemode(GameMode.SINGLEPLAYER)
        # Setting userid to the guesser
        # game.add_guesser(current_user.get_id())
        IGC.add_game(game)
        return redirect(url_for('guesser', game_id=game.get_id()))

    if form.is_submitted() and form.new_game_proposer_singlePlayer.data:
        game = Game()
        game.set_gamemode(GameMode.SINGLEPLAYER)
        # Setting userid to the proposer
        # game.set_proposer(current_user.get_id())
        IGC.add_game(game)
        return redirect(url_for('proposer', game_id=game.get_id()))

    if form.is_submitted() and form.new_game_guesser_ai.data:
        game = Game()
        ilr = game.get_image_label_reader()
        ai.generate_playlist(ilr)
        filename, sequence = ai.get_random_image()
        game.set_imagePath(filename)
        game.set_ai_best_proposed(sequence)
        game.set_label(ilr.getLabel(filename))
        game.set_gamemode(GameMode.AI)

        IGC.add_game(game)
        return redirect(url_for('guesser', game_id=game.get_id()))

    user = get_userbyid(current_user.get_id())
    if len(request.args) > 0 and request.args['error']:
        return render_template('dashboard.html', title='Dashboard', form=form, games=IGC.get_games_to_join(),
                               err=request.args['error'], username=user['username'], points=user['points'])
    return render_template('dashboard.html', title='Dashboard', form=form, games=IGC.get_games_to_join(),
                           username=user['username'], points=user['points'])


@app.route('/proposer/<game_id>', methods=['GET', 'POST'])
@login_required
def proposer(game_id):
    game = IGC.get_game_by_id(game_id)
    user = get_userbyid(current_user.get_id())
    if game:
        return render_template('proposer.html', title="Proposer", game=game, user_id=current_user.get_id(),
                               username=user['username'], points=user['points'])
    return redirect(url_for('dashboard'))


@app.route('/guesser/<game_id>')
@login_required
def guesser(game_id):
    game = IGC.get_game_by_id(game_id)
    if game:
        user = get_userbyid(current_user.get_id())
        return render_template('guesser.html', title="Guesser", game=game, user_id=current_user.get_id(),
                               username=user['username'], points=user['points'])
    return redirect(url_for('dashboard'))


@app.route('/gametable', methods=["POST"])
@login_required
def game_table():
    req_data = request.values
   # mode = req_data['type']
    mode = req_data.get("mode")
    return render_template('gametable.html', games=IGC.get_games_to_join(), mode=mode)


@app.route('/leaderboard', methods=["GET"])
@login_required
def leaderboard():
    players = get_best_players()
    return render_template('leaderboard.html', games=IGC.get_games_to_join(), players=players)


@app.route('/join', methods=["POST"])
@login_required
def join():
    game_id = request.form['join']
    game = IGC.get_game_by_id(game_id)
    if game:
        if request.form['role'] == "proposer":
            return redirect(url_for('proposer', game_id=game.get_id()))
        else:
            return redirect(url_for('guesser', game_id=game.get_id()))
    return redirect(url_for('dashboard', error="Game not found!"))


@app.route('/logout')
@login_required
def logout():
    # Logingout the user and returning to index
    logout_user()
    return redirect(url_for('index'))


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@socketio.on('propose image')
def handlePropose(data):
    gameid = data['gameid']
    image = data['image']
    game = IGC.get_game_by_id(gameid)
    game.add_proposedImage(image)
    imagePath = "{}_scattered/{}.png".format(game.get_imagePath(), image)
    emit('new image section', imagePath, room=gameid, broadcast=True)


def propose(data):
    game = IGC.get_game_by_id(data['gameid'])
    if game:
        game.add_proposedImage(data['image'] + '.png')


def return_to_home(reason):
    sending = {
        "url": url_for('dashboard'),
        "reason": reason
    }
    emit("leave_game", sending)


@socketio.on('join_game')
@login_required
def handle_join_game(msg):
    game_id = msg['game_id']
    user_id = msg['user_id']
    proposer = msg['proposer']
    game = IGC.get_game_by_id(game_id)
    if game:
        ret = game.add_player(user_id,str(request.sid),proposer)
        if len(ret) > 0:
            return_to_home(ret)
        else:
            join_room(game.get_id())
            IGC.add_player_to_game(game,str(request.sid))
        return
    return_to_home("Game not found!")


@socketio.on('new_guess')
@login_required
def handle_new_guess(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
         if game.handle_new_guess(str(request.sid), msg["guess"]):
            game.remove_all_players(IGC)
            IGC.remove_game(game)


@socketio.on('propose_image')
@login_required
def handle_propesed_image(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
        game.handle_new_propose(str(request.sid), msg["image"])


@socketio.on('request_start')
@login_required
def handle_request_start(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
        game.start_game()


@socketio.on('request_propose')
@login_required
def handle_request_propose(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
        game.request_propose(str(request.sid))


@socketio.on('chat')
@login_required
def handle_chat(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
        user = game.find_guesser_by_sid(str(request.sid))
        if user:
            emit("chat", {"user": user.get_username(),"message": msg['message']}, room=game_id)


@socketio.on('disconnect')
@login_required
def handle_disconnect():
    game = IGC.get_game_from_player(str(request.sid))
    if game:
        handle_removing_player(game)


@socketio.on('leaving_game')
@login_required
def handle_player_leaving(msg):
    game_id = msg["game_id"]
    game = IGC.get_game_by_id(game_id)
    if game:
        handle_removing_player(game)

def handle_removing_player(game):
    leave_room(game.get_id())
    IGC.remove_player(str(request.sid))
    if game.remove_player(str(request.sid)):
        game.remove_all_players(IGC)
        IGC.remove_game(game)
    else:
        IGC.remove_player(str(request.sid))
