var app = require('express').createServer()
  , io = require('socket.io').listen(app)
  , redis = require('redis')
  , rc = redis.createClient();

var airetyApp = require('../app/static/js/backbone/models');

app.listen(1337);

var clients = 0;
var nodeChatModels = [];


function getInitialChats(chatRoomId) {
	if(nodeChatModels[chatRoomId]){
		
	} else {
		
		nodeChatModels[chatRoomId] = new airetyApp.model.nodeChatModel();
		rc.lrange(chatRoomId+'_chatentries', -10, -1, function(err, data) {
			if (err)
			{
				console.log('Error: ' + err);
			}
			else if (data) {
				_.each(data, function(jsonChat) {
					var chat = new airetyApp.model.textChat();
					chat.mport(jsonChat);
					nodeChatModels[chatRoomId].chats.add(chat);
				});

				console.log('Revived ' + nodeChatModels[chatRoomId].chats.length + ' chats');
			}
			else {
				console.log('No data returned for key');
			}
		});
	}
}

io.sockets.on('connection', function (socket) {

	clients += 1;

	socket.on('message', function(msg){
		msg = JSON.parse(msg);
		if(msg.__special){
			socket.set('room', msg.__special.chatRoomId);
			socket.join(msg.__special.chatRoomId);
			getInitialChats(msg.__special.chatRoomId);
			socket.emit('message',{
				event: 'initial',
				data: nodeChatModels[msg.__special.chatRoomId].xport()
			});
	  	} else {
			chatMessage(socket, JSON.stringify(msg));
	  	}
	});

	socket.on('disconnect', function(){ clientDisconnect(socket) });

});

function chatMessage(socket, msg){
    var chat = new airetyApp.model.textChat();
    chat.mport(msg);

	var roomId = socket.store.data.room;

    rc.incr('next.textchat.id', function(err, newId) {
        chat.set({ id: newId });
        nodeChatModels[roomId].chats.add(chat);

        rc.rpush(roomId + '_chatentries', chat.xport(), redis.print);
        rc.bgsave();

        socket.broadcast.to(roomId).emit('message',{
            event: 'chat',
            data: chat.xport()
        }); 
        socket.emit('message',{
            event: 'chat',
            data: chat.xport()
        });
    }); 
}

function clientDisconnect(socket){
  clients -= 1;
  socket.leave(socket.store.data.room);
}

