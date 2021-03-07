var socket = null;
let game_id_str = ''
var updateInterval;

window.onload = init;

function init() {
}


var initAjax = function(){
    $("#game-container-0" ).load("/gametable",{mode:"GameMode.MULTIPLAYER"});
    $("#game-container-1" ).load("/gametable",{mode:"GameMode.SINGLEPLAYER"});
    $("#leaderboard" ).load("/leaderboard");
};



var rowToHtml = function(row){
    var rowStr = "<tr id='"+ row.game_id +"'><td>" + row.game_id + "</td><td>"+ row.members +"</td>";
    rowStr += "<td><form id='"+ row.game_id + "' action='/join' method='POST'><button name='join' value='"+ row.game_id +"' class='btn btn-success'>Join</button></form></td>";
    rowStr += "<td><div class='btn-group btn-group-toggle' data-toggle='buttons'>"
    if(row.hasProposer){
        rowStr += "<label class='btn btn-secondary active'><input type='radio' name='role' value='proposer' autocomplete='off' checked>Proposer</label>";
        rowStr += "<label class='btn btn-secondary'><input type='radio' name='role' value='guesser' autocomplete='off'>Guesser</label>";
    }else{
        rowStr += "<label class='btn btn-secondary active'><input type='radio' name='role' value='guesser' autocomplete='off' checked>Guesser</label>";
    }
    rowStr += "</div></td></tr>";
    return rowStr;
};

var leaveGame = function(){
    socket.emit("leaving_game",{"game_id":game_id_str})
    window.location.href = "/dashboard?error=You%20left%20the%20game...";
}
