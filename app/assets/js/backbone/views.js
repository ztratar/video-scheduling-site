// Views

$(function() {

	airetyApp.view.baseView = Backbone.View.extend({

		initialize: function(options) {
			this.model = this.model || {};
			this.collection = this.collection || {};
			this.currentView = this.currentView || {};
			this.activeChildren = [];
			if (typeof this.init === 'function') {
				this.init(options);
			}
		},

		showView: function(selector, view, options) {
			if (this.currentView && this.currentView[selector] && view != this.currentView[selector]) {
				this.currentView[selector].close();
				this.currentView[selector] = false;
			}
			this.currentView[selector] = view;
			this.$(selector).html(this.currentView[selector].$el);
			if (options && options.render === true) {
				this.currentView[selector].render();
			}
			return this;
		},
		
		close: function() {
			if (typeof this.onClose === 'function' ) {
				this.onClose();
			}
			if (this.activeChildren != undefined && this.activeChildren.length > 0) {
				_.each(this.activeChildren,function(child){ child.close(); })
				this.activeChildren = [];
			}
			this.$el.remove();
		}

	});

	airetyApp.view.appView = airetyApp.view.baseView.extend({
	
		el: $('body'),

		events: {
			'click #dialog-container': 'closeDialog'
		},

		init: function() {
			this.model = new airetyApp.model.user();
			this.headerView = new airetyApp.view.headerView({
				model: this.model
			});
			if ( window.airety.currentUser ){
				// User is authed with Facebook and logged in
				this.model.set(window.airety.currentUser);
			} else {
				// User not logged
			}
		},

		showDialog: function(view, options) {
			$('html').addClass('theaterMode');
			this.showView('#dialog-container', view, options);
		},

		closeDialog: function(e) {
			if(e && e.target){
				if (e.target.id !== 'dialog-container'){
					return false;
				}
			}
			if (this.currentView['#dialog-container']) {
				this.currentView['#dialog-container'].close();
				this.currentView['#dialog-container'] = false;
			}
			$('html').removeClass('theaterMode');
		}

	});

	airetyApp.view.headerView = airetyApp.view.baseView.extend({
	
		el: $('#header'),

		dropdownTemplate: $("#headerDropdown-template").html(),
		hostButtonTemplate: $("#hostButton-template").html(),

		events: {
			'click #hostButton': 'openHostDialog',
			'click #editProfile': 'openEditProfileDialog'
		},

		init: function(options) {
			this.model.bind('change', this.renderDropdown, this);
			this.model.bind('change', this.renderHostButton, this);
		},

		renderDropdown: function() {
			this.$("#dropdown-container").html( Mustache.render(this.dropdownTemplate, this.model.toJSON()) );	
		},

		renderHostButton: function() {
			this.$("#hostButton-container").html( Mustache.render(this.hostButtonTemplate, this.model.toJSON()) );
		},

		openHostDialog: function() {
			var view = new airetyApp.view.hostChatsDialogView();
			window.airety.app.showDialog(view, { render: true });
			return false;
		},

		openEditProfileDialog: function() {
			var view = new airetyApp.view.editProfileDialogView();
			window.airety.app.showDialog(view, { render: true });
			return false;
		}
	
	});

	airetyApp.view.chatView = airetyApp.view.baseView.extend({
		
		template: $("#chatView-template").html(),

		initChat: function(options) {
			this.apiKey = 14712672;
			this.sessionId = window.chat.session || 'test';
			this.token = window.chat.token;
			this.publisher = {};

			TB.setLogLevel(TB.DEBUG);
		 
			this.session = TB.initSession(this.sessionId);
			var that = this;
			this.session.addEventListener('sessionConnected', function(e) {
		   		that.sessionConnectedHandler.call(that, e);
			});
			this.session.addEventListener('streamCreated', function(e) {
				that.streamCreatedHandler.call(that, e);
			});
			this.session.connect(this.apiKey, this.token);
		},

		render: function() {
			this.$el.html(this.template);
		},

		sessionConnectedHandler: function(event) {
			this.publisher = this.session.publish('myChat', { width: 214, height: 137 });
     		// Subscribe to streams that were in the session when we connected
     		this.subscribeToStreams(event.streams);
		},

		streamCreatedHandler: function(event) {
			// Subscribe to any new streams that are created
     		this.subscribeToStreams(event.streams);
		},

		subscribeToStreams: function(streams) {
			for (var i = 0; i < streams.length; i++) {
				// Make sure we don't subscribe to ourself
				if (streams[i].connection.connectionId == this.session.connection.connectionId) {
				  return;
				}
		 
				// Create the div to put the subscriber element in to
				var div = document.createElement('div');
				div.setAttribute('id', 'stream' + streams[i].streamId);
				this.$(".othersChat-container")[0].appendChild(div);
								   
				var subscriberProps = {
					width: 670, 
					height: 365
				};

				// Subscribe to the stream
				this.session.subscribe(streams[i], div.id, subscriberProps);
			  }
		}

	});

	airetyApp.view.chatColumnView = airetyApp.view.baseView.extend({
	
		template: $("#chatColumnView-template").html(),

		render: function() {
			this.$el.html(this.template);
		}
	
	});

	airetyApp.view.textChatView = airetyApp.view.baseView.extend({
	
		template: $("#textChatView-template").html(),

		events: {
			'submit form': 'sendMessage',
			'click a.submit-message': 'clickSend'
		},

		init: function(options) {
			this.model.chats.on('add', this.addOne, this);
       		this.socket = options.socket;
			this.lastMessageSent = (new Date()).getTime();
		},

		render: function() {
			this.$el.html(this.template);
		},

		addOne: function(chat) {
			var view = new airetyApp.view.textChatItemView({
				model: chat
			});
			this.$("ul.messages").append(view.$el);
			view.render();
			this.$("ul.messages").scrollTop(this.$("ul.messages")[0].scrollHeight);
			this.activeChildren.push(view);
		},

		msgReceived: function(message){
			var that = this;
			switch(message.event) {
				case 'initial':
					this.model.mport(message.data);
					var that = this;
					this.model.chats.each(function(chat){
						that.addOne(chat);
					});
					break;
				case 'chat':
					var newChatEntry = new airetyApp.model.textChat();
					newChatEntry.mport(message.data);
					this.model.chats.add(newChatEntry);
					break;
			}
		},

		clickSend: function() {
			this.sendMessage();
			return false;
		},

		sendMessage: function() {
			var currentTime = (new Date()).getTime();
			if ((currentTime-this.lastMessageSent) > 2000){ 
				var $input = this.$("input");
				var newMessage = new airetyApp.model.textChat({
					name: window.airety.app.model.get('first_name'),
					message: $input.val()
				});
				this.socket.send(newMessage.xport());
				$input.val('');
				this.lastMessageSent = (new Date()).getTime();
			} else {
				var that = this;
				this.$("a.submit-message").html('wait...');
				if(this.newTimeout)
					clearTimeout(this.newTimeout);
				this.newTimeout = setTimeout(this.changeBackToSend, 2000-(currentTime-this.lastMessageSent));
			}
			return false;
		},

		changeBackToSend: function() {
			this.$("a.submit-message").html('Send');
		}
	
	});


	airetyApp.view.textChatItemView = airetyApp.view.baseView.extend({
	
		tagName: 'li',

		template: $("#textChatItemView-template").html(),

		render: function() {
			this.$el.html(Mustache.render(this.template, this.model.toJSON()));
		}
	
	});


	airetyApp.view.homeView = airetyApp.view.baseView.extend({
	
		template: $("#homeView-template").html(),

		init: function() {
		},

		render: function() {
			this.$el.html(this.template);
		}
	
	});

	airetyApp.view.registrationView = airetyApp.view.baseView.extend({
	
		template: $("#registrationView-template").html(),

		events: {
			'click a.logInWithFacebook': 'signupLogin'
		},

		init: function() {
			$(window).on('scroll', this.scrolling);
		},

		render: function() {
			this.$el.html(this.template);
		},

		signupLogin: function() {
			var that = this,
				accessToken;
            FB.getLoginStatus(function(response) {
          		if (response.status === 'connected') {
           			var uid = response.authResponse.userID;
           			accessToken = response.authResponse.accessToken;
           			that.fbGetSignupData(accessToken);
         		} else {
					FB.login(function(response) {
						if (response.authResponse) {
							that.fbGetSignupData(response.authResponse.accessToken);
						}
					}, {scope: 'email,user_location,user_hometown,user_work_history,user_education_history,user_interests,publish_actions'});
         		}
       		});
        	return false;
		},

		fbGetSignupData: function(access_token) {
			FB.api('/me', function(data) { 
				data = $.extend(data, { access_token: access_token });
				$.ajax({
					url: '/login',
					type: 'POST',
					beforeSend: function(xhr) {
						xhr.setRequestHeader("X-CSRFToken", window.airety.csrf); 
					},
					data: data,
					success: function(data) {
						window.airety.app.model.set(data);
					}
				});
			});
		},

		scrolling: function() {
			if ($(window).scrollTop() < 1){
				this.$(".headerPop").css('z-index', '110');	
			} else {
				this.$(".headerPop").css('z-index', '90');
			}
		},

		onClose: function() {
			$(window).off('scroll', this.scrolling);
		}
	
	});

	airetyApp.view.chatsTodayView = airetyApp.view.baseView.extend({
	
		template: $("#chatsTodayView-template").html(),

		events: {
			'click li': 'showRoomOpts'
		},

		init: function() {
			$(window).on('scroll', this.scrolling);
			this.collection.on('reset', this.addAll, this);
			this.collection.on('add', this.addOne, this);
			this.render();
		},

		render: function() {
			this.$el.html(this.template);
			return this;
		},

		center: function() {
			var halfWidth = this.$(".chatHeaderPop").outerWidth() / 2;
			this.$(".chatHeaderPop").css('marginLeft','-'+halfWidth+'px');
			$("#primaryContainer").addClass('chatsToday');
		},

		addAll: function() {
			var that = this;
			this.activeChildren.each(function(child) { 
				child.close();   
			});
			this.activeChildren = [];
			this.collection.each(function(chat){
				that.addOne(chat)
			});		
		},

		addOne: function(chat) {
			var view = new airetyApp.view.chatsTodayItemView({
				model: chat
			});
			this.$("ul").append(view.$el);
			view.render();
			if(this.activeChildren.length >= 1){
				view.$el.addClass('rightItem');
			} else {
				view.$el.width('335').addClass('active');
			}
			this.activeChildren.push(view);
		},

		showRoomOpts: function(e) {
			var allElements = $(e.currentTarget).parent().children('li');
			var thisElement = $(e.currentTarget);
			if(!thisElement.hasClass('active')){
				allElements.not(thisElement).animate({ width: '56px'}, 100).removeClass('active');
				thisElement.animate({ width: '335px' }, 100).addClass('active');
			}
		},

		scrolling: function() {
			if ($(window).scrollTop() < 1){
				this.$(".chatHeaderPop").css('z-index', '110');	
			} else {
				this.$(".chatHeaderPop").css('z-index', '90');
			}
		},

		onClose: function() {
			$(window).off('scroll', this.scrolling);
		}

	});

	airetyApp.view.chatsTodayItemView = airetyApp.view.baseView.extend({
	
		tagName: 'li',
		
		template: $("#chatsTodayItemView-template").html(),

		init: function() {
			this.model.on('change', this.render, this);
		},

		render: function() {
			this.$el.html(Mustache.render(this.template, this.model.toJSON()));
		}

	});

	airetyApp.view.streamView = airetyApp.view.baseView.extend({
	
		className: "user-stream",

		init: function(options) {
			this.options = options || this.options || {};

			this.collection.on('reset', this.addAll, this);
			this.collection.on('add', this.addOne, this);

			this.itemWidth = options.itemWidth || 210;
			this.offset = options.offset || 20;
		},

		setUp: function() {
			this.columnWidth = this.itemWidth + this.offset;
			this.containerWidth = this.$el.width();
			this.numColumns = Math.floor((this.containerWidth + this.offset) / this.columnWidth);
			this.offsetRight = Math.round((this.containerWidth - (this.numColumns * this.columnWidth - this.offset)) / 2);
			this.bottom = 0;
			this.columns = [];

			while (this.columns.length < this.numColumns) {
				this.columns.push(0);
			}

			$(window).on('scroll', this, this.infScroll);
		},

		addAll: function() {
			var that = this;
			if (this.activeChildren) {
				_.each(this.activeChildren, function(child) { 
					child.close();   
				});
			}
			this.activeChildren = [];
			this.collection.each(function(user){
				that.addOne(user)
			});
			var scrollTop = $(window).scrollTop();
		},

		addOne: function(user) {
			var shortest = null,
			shortestIndex = 0,
			k;

			var view = new airetyApp.view.userCardView({ model: user });
			this.$el.append(view.render().el);

			this.activeChildren.push(view);

			for (k = 0; k < this.numColumns; k++) {
				if (shortest === null || this.columns[k] < shortest) {
					shortest = this.columns[k];
					shortestIndex = k;
				}
			}

			// Postion the item.
			view.$el.css({
				position: 'absolute',
				top: shortest + 'px',
				left: (shortestIndex * this.columnWidth) + 'px',
				width: this.itemWidth
			});

			// Update column height.
			this.columns[shortestIndex] = shortest + view.$el.outerHeight() + this.offset;
			if (this.columns[shortestIndex] > this.bottom) {
				this.bottom = this.columns[shortestIndex];
				this.$el.height(this.bottom);
			}

			view.$("img.lazy").lazyload({
				effect: 'fadeIn',
				threshold: 800
			});

		},

		infScroll: function() {

		}
	
	});

	airetyApp.view.userCardView = airetyApp.view.baseView.extend({

		className: "user-stream-card",

		template: $("#userCardView-template").html(),

		events: {
			'click a': 'openSchedule'
		},

		init: function(options) {
			this.extended = options.extended || false;
			this.model.on('change', this.render, this);
			this.model.on('destroy', this.remove, this);
		},

		render: function() {
			var templateVariables = {
				extended: this.extended,
				model: this.model.toJSON()
			};
			this.$el.html(Mustache.render(this.template, templateVariables));
			if (this.extended) {
				this.$("img.lazy").lazyload();
			}
			return this;
		},

		openSchedule: function() {
			var view = new 	airetyApp.view.scheduleChatDialogView({
				model: this.model
			});
			window.airety.app.showDialog(view, { render: true });
		}
	});

	airetyApp.view.scheduleChatDialogView = airetyApp.view.baseView.extend({
	
		template: $("#scheduleChatDialogView-template").html(),

		className: 'schedule-chat-dialog-view',

		events: {
			'click span.checkboxContainer': 'checkTheBox',
			'submit #schedule-slots-form': 'submitForm'
		},

		init: function() {
		},

		render: function() {
			this.$el.html(Mustache.render(this.template, this.model.toJSON()));
			this.cardView = new airetyApp.view.userCardView({
				model: this.model,
				extended: true
			});
			this.showView('.card-column', this.cardView, { render: true });
			return this;
		},

		checkTheBox: function(e) {
			var target = $(e.target);
			if(target.hasClass('active')){
				target.removeClass('active');
				target.children('input').attr('checked','');
			} else {
				target.addClass('active');
				target.children('input').attr('checked', 'checked');
			}
			return false;
		},

		submitForm: function() {
			
		}
	
	});

	airetyApp.view.hostChatsDialogView = airetyApp.view.baseView.extend({
		
		template: $("#hostChatsDialogView-template").html(),

		className: 'host-chats-dialog-view',

		events: {
			'click td.checkable': 'checkCalendarSlot',
			'click #host-chats-submit': 'formSubmit'
		},

		render: function() {
			this.$el.html(Mustache.render(this.template));
			var daysArray = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'];
			var timeSectionArray = [
				{
					name: 'Morning',
					time: '8AM-12PM'
				},{
					name: 'Afternoon',
					time: '12PM-4PM'
				},{
					name: 'Night',
					time: '4PM-8PM'
				},{
					name: 'Late Night',
					time: '8PM-11PM'
				},{
					name: 'Night Owl',
					time: '11PM-2AM'
				}],
				currentUserAvail = window.airety.app.model.get('availability');
			for (var i = 0; i < timeSectionArray.length; i++){
				var tableRow = '<tr><td><span class="big">'+timeSectionArray[i].name+'</span><span>'+timeSectionArray[i].time+'</span></td>';
				for(var y = 0; y < daysArray.length; y++){
					var checked = false;
					for (var z = 0; z < currentUserAvail.length; z++) {
						if (currentUserAvail[z].day === y
							&& currentUserAvail[z].start_time === 16 + (i * 8)) {
							checked = true;
						}
					}
					tableRow += '<td class="checkable';
					if (checked) {
						tableRow += ' checked';
					}
					tableRow += '"><input type="checkbox" name="'+y+'_'+timeSectionArray[i].name.replace(' ','-').toLowerCase()+'"';
					if (checked) {
						tableRow += ' checked="checked"';
					}
					tableRow += '></td>';
				}
				tableRow += '</tr>';
				this.$(".host-chats-table tbody").append(tableRow);
			}
			return this;
		},

		checkCalendarSlot: function(e) {
			var target = $(e.target);
			if(target.hasClass('checked')){
				target.removeClass('checked');
				target.children('input').attr('checked', false);
			} else {
				target.addClass('checked');
				target.children('input').attr('checked', true);
			}
			return false;
		},

		formSubmit: function() {
			var checkedArray = []
			this.$("input:checked").each(function(){
				checkedArray.push($(this).attr('name'));
			});

			$.ajax({
				type: 'POST',
				url: '/api/user_availability_create',
				beforeSend: function(xhr) {
					xhr.setRequestHeader("X-CSRFToken", window.airety.csrf); 
				},
				data: {
					'availability': checkedArray
				},
				success: function(data) {
					window.airety.app.model.set('availability', data);
				}
			});

			window.airety.app.closeDialog();

			return false;
		}

	});

	airetyApp.view.editProfileDialogView = airetyApp.view.baseView.extend({
	
		template: $("#editProfileDialogView-template").html(),

		className: 'edit-profile-dialog-view',

		render: function() {
			this.$el.html(Mustache.render(this.template));
			return this;
		}

	});

});
