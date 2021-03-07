var blockGuessing = false;

var sendChat = function () {
    var text = document.getElementById("chat-field").value;
    if (text != "") {
        socket.emit("chat", { "message": text, "game_id": game_id_str });
        document.getElementById("chat-field").value = "";
    }
}

var isEnter = function (e) {
    var key = e.which || e.keyCode || 0;
    if (key === 13) {
        var guess = (document.activeElement === document.getElementById("guess-field"))
        var chat = (document.activeElement === document.getElementById("chat-field"))

        if (guess){
            newGuess();
        }
        if (chat) {
            sendChat();
        }
    }
}

var newGuess = function () {
    var text = document.getElementById("guess-field").value;
    if (text != "") {
        socket.emit("new_guess", { "guess": text, "game_id": game_id_str });
        document.getElementById("guess-field").value = "";
    }
}

var requestPropose = function () {
    socket.emit("request_propose", { "game_id": game_id_str });
}

var startGuesserWs = function (game_id, user_id) {
    game_id = game_id;
    document.addEventListener('keydown',isEnter);
    socket = io();
    window.addEventListener('beforeunload', function (e) {
        socket.emit("leaving_game",{"game_id":game_id_str});
    });
    socket.on('connect', function () {
        socket.emit("join_game", { 'game_id': game_id, 'user_id': user_id, 'proposer': false });
    });
    socket.on('new_image', function (msg) {
        $('#image-container').append('<img src="https://dat240-group-8.firebaseapp.com/images/' + msg.path + '_scattered/' + msg.image + '.png" width="400" class="image-section">');
    });
    socket.on('leave_game', function (json) {
        var url = json.url + "?error=" + json.reason;
        window.location.href = url;
    });
    socket.on('leaved_game', function (json) {
        $('#game-log').append(
            '<div class="alert alert-danger game-event"><strong>' + json.user + ' left the game</strong></div>'
        );
        scrollToBottomOfLog()
    });

    socket.on('game_finish', function (json) {
        var finishStr = json.is_winner?`${json.winner} guessed correctly. You got ${json.score} points`:"Game over!"
        $('#finishMessage').html(finishStr);
        $('#guesserModal').modal({ backdrop: 'static', keyboard: false })
        socket.close();
    });

    socket.on('chat', function (json) {
        $('#game-log').append(
            '<div class="alert alert-secondary game-event"><strong>' + json.user + ': </strong>' + json.message + '</div>'
        );
        scrollToBottomOfLog()
    });

    socket.on('new_player', function (json) {
        $('#game-log').append(
            '<div class="alert alert-success game-event"><strong>' + json.user + ' joined the game</strong></div>'
        );
        scrollToBottomOfLog()
    });

    socket.on('new_guess', function (json) {
        $('#game-log').append(
            '<div class="alert alert-primary game-event"><strong>' + json.user + ' guessed: ' + json.guess + '</strong></div>'
        );
        scrollToBottomOfLog()
    });

    socket.on('status_changed', function (json) {
        if (json.status == "notvalid" || json.status == "valid") {
            $('#game-status').html("Waiting to start");
        }
        else if (json.status == "started") {
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Game started!</strong></div>'
            );
            $('#guess-input').show();
        }
        else if (json.status == "last_proposed")
        {
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Last three guesses!</strong></div>'
            );
            $('#propose-btn').hide();
        }
        else if (json.status == "block_guessing") {
            if (json.open){
                $('#game-log').append(
                    '<div class="alert alert-info game-event"><strong>Try a new guess</strong></div>'
                );
                $("#guess-field").removeAttr('disabled', 'disabled');
                blockGuessing = false;
            }else{
                $('#game-log').append(
                    '<div class="alert alert-info game-event"><strong>Waiting for proposer to send new segment.</strong></div>'
                );
                $("#guess-field").val('');
                $("#guess-field").attr('disabled', 'disabled');
                blockGuessing = true;
            }
        }
    });
}

var scrollToBottomOfLog = function () {
    var el = $('#game-log')
    el.scrollTop(el.prop("scrollHeight"));
}