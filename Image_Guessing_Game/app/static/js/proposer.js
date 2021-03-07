const imagepath = document.querySelector('#imagePath').value
let readyPropose = true;
let isMultiplayer = false;
let stringifiedImages = document.querySelector('#all-images').value.split(",")
let canvases = []
let counter = 1

let images = []
stringifiedImages.forEach((image) => {
    images.push(image.replace("'", "").replace("'", "").replace(" ", "").replace("]", "").replace("[", ""))
})

images.forEach(image => {
    let c = document.createElement("canvas");
    c.classList = 'canvases'
    let ctx = c.getContext('2d');
    c.width = 400
    c.height = 400

    let img = new Image()
    img.setAttribute('crossorigin', 'anonymous');
    img.src = `https://dat240-group-8.firebaseapp.com/images/${imagepath}_scattered/${image}`
    img.onload = () => {
        ctx.drawImage(img, 0, 0, 400, 400)
    }

    document.querySelector('.canvases').appendChild(c)
    canvases.push([c, image])
    c.style.display = 'none'
})

document.querySelector('.images').addEventListener('click', (e) => {
    if (!readyPropose && !isMultiplayer) {
        return;
    }
    canvases.forEach(element => {
        let canvas = element[0]
        let imgData = canvas.getContext('2d').getImageData(e.pageX - 40, e.pageY - 250, 1, 1).data
        if (imgData[3] != 0) {
            let imgEl = document.getElementById(element[1])
            imgEl.classList.add('clicked')

            let dotEl = document.createElement('div')
            dotEl.style.position = 'absolute'
            dotEl.style.top = `${e.pageY - 10}px`
            dotEl.style.left = `${e.pageX - 10}px`
            dotEl.innerHTML = counter
            dotEl.classList.add('dot')

            document.querySelector('body').appendChild(dotEl)
            counter++

            let index = canvases.findIndex(list => {
                return list[1] == element[1]
            })

            canvases.splice(index, 1)
            socket.emit('propose_image', { 'image': element[1].replace(".png", ""), 'game_id': gameid })
            if (!isMultiplayer) {
                $('#game-log').append(
                    '<div class="alert alert-info game-event"><strong>Please wait for guesser to request new propose</strong></div>'
                );
                readyPropose = false;
                scrollToBottomOfLog()
            }
        }
    })
})

var startGame = function () {
    socket.emit("request_start", { "game_id": gameid });
    $('.images').show()
}

var startProposerWs = function (game_id, user_id) {
    game_id = game_id;
    socket = io();
    window.addEventListener('beforeunload', function (e) {
        socket.emit("leaving_game",{"game_id":game_id_str});
    });
    socket.on('connect', function () {
        socket.emit("join_game", { 'game_id': game_id, 'user_id': user_id, 'proposer': true });
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
        var finishStr = json.is_winner?`${json.winner} guessed correct. You got ${json.score} points`:"Game over!"
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
        $('#startBtn').hide();
        if (json.status == "notvalid") {
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Waiting for players!</strong></div>'
            );
            $('#startBtn').hide();
        }
        else if (json.status == "valid") {
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Ready to start game!</strong></div>'
            );
            $('#startBtn').show();
        }
        else if (json.status == "started") {
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Game has begun!</strong></div>'
            );
            $('#image-label').html(json.label);
            $('.images').show();
            $('#startBtn').hide();
        } else if (json.status == "ready_propose") {
            readyPropose = true;
            $('#game-log').append(
                '<div class="alert alert-info game-event"><strong>Ready to propose new segment</strong></div>'
            );
            scrollToBottomOfLog()
        }

    });
}

var scrollToBottomOfLog = function () {
    var el = $('#game-log')
    el.scrollTop(el.prop("scrollHeight"));
}