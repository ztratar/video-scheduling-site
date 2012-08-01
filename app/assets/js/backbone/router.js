$(function(){

	/********* ROUTER *********/

	airetyApp.router.primary = Backbone.Router.extend({
			
			routes: {
				'': 'index',
				'chats/:id': 'chats'
			},

			index: function() {
				this.homeView = new airetyApp.view.homeView();
				window.airety.app.showView('#primaryContainer', this.homeView, { render: true });
				
				if ( !window.airety.app.model.get('id') ) {
					this.registrationView = new airetyApp.view.registrationView();
					this.homeView.showView('.top-container', this.registrationView, { render: true });
				} else {
					$("#primaryContainer").addClass('authed');
					this.chatsToday = new airetyApp.collection.chats();
					this.chatsTodayView = new airetyApp.view.chatsTodayView({
						collection: this.chatsToday
					});
					this.chatsToday.add({
						id: 3
					}).add({
						id: 4
					}).add({
						id: 5
					});

					this.homeView.showView('.top-container', this.chatsTodayView);
					this.chatsTodayView.center();
				}

				this.userStream = new airetyApp.collection.users();
				this.userStreamView = new airetyApp.view.streamView({
					collection: this.userStream
				});
				this.homeView.showView('.stream-container', this.userStreamView);
				this.userStreamView.setUp();
				this.userStream.url = '/api/feed';
				this.userStream.fetch();
			},

			chats: function(id) {
				var that = this;
				this.socket = io.connect('http://192.168.1.148:8000/');
			
				this.chat = new airetyApp.model.chat({
					id: id
				});
       			this.nodeChatModel = new airetyApp.model.nodeChatModel({id: id});

				this.chatView = new airetyApp.view.chatView({
					model: this.chat
				});
				this.chatColumnView = new airetyApp.view.chatColumnView({
					model: this.chat
				});
				this.textChatView = new airetyApp.view.textChatView({
					model: this.nodeChatModel,
					socket: this.socket
				});
				this.cardView = new airetyApp.view.userCardView({
					model: window.airety.app.model,
					extended: true
				});
	
				$("#primaryContainer").addClass('authed');

				window.airety.app.showView('#primaryContainer', this.chatView, { render: true });
				this.chatView.showView('.chat-column', this.chatColumnView, { render: true });
				this.chatColumnView.showView('.textChat-container', this.textChatView, { render: true });
				this.chatView.showView('.card-container', this.cardView, { render: true });

				this.chatView.initChat();

        		this.socket.on('message', function(msg) { that.textChatView.msgReceived(msg); });
				var connectionObj = {
					__special: {
						chatRoomId: id
					}
				};
				this.socket.send(JSON.stringify(connectionObj));

			}

	});

});
