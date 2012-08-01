(function(){

	// Configuration for node.js include of file
	
	var server = false;

	if (typeof exports !== 'undefined') {	
		 _ = require('../../../../nodeJS/node_modules/underscore')._;
        Backbone = require('../../../../nodeJS/node_modules/backbone');
		$ = require('../../../../nodeJS/node_modules/jquery');

		airetyApp = exports;
		airetyApp.model = {};
		airetyApp.collection = {};
		server = true;
	}

	// Models
	
	airetyApp.model.baseModel = Backbone.Model.extend({
		initialize: function(options) {
			if (typeof this.init === 'function') {
				this.init(options)
			}
		}
	});

	airetyApp.model.user = airetyApp.model.baseModel.extend({
		urlRoot: '/users',
		initialize: function(options) {
			this.on('change:fb_id', this.refreshImages);
			if (options && options.fb_id) {
				this.refreshImages();
			}
		},
		refreshImages: function() {
			if (!this.get('picture_url')) {
				this.set('thumb_url',
						 'https://graph.facebook.com/'+this.get('fb_id')+'/picture',
						 { silent: true });
				this.set('picture_url',
						 'https://graph.facebook.com/'+this.get('fb_id')+'/picture?type=large',
						 { silent: true });
			}
		}
	});

	airetyApp.model.chat = airetyApp.model.baseModel.extend({
		urlRoot: '/chats'
	});

	airetyApp.model.nodeChatModel = airetyApp.model.baseModel.extend({
		init: function() {
			this.chats = new airetyApp.collection.textChats();
		}
	});

	airetyApp.model.textChat = airetyApp.model.baseModel.extend({
		urlRoot: '/textChats'
	});

	
	/* collections */

	airetyApp.collection.baseCollection = Backbone.Collection.extend({

		initialize: function(models,options) {
			this.pageSize = 100;
			this.data = {};
			if (typeof this.init === 'function') {
				this.init(models,options);
			}

		},

		fetchPrev: function() {
			var tempData = this.data;
			if (this.model.first()) {
				tempData = $.extend({ firstId: this.model.first().get('id') },tempData);
			}
			this.fetch({
				data: this.data
			});	
		},

		fetchNext: function() {
			var tempData = this.data;
			if (this.model.last()) {
				tempData = $.extend({ lastId: this.model.last().get('id') },tempData);
			}
			this.fetch({
				data: this.data
			});	
		}

	});

	airetyApp.collection.users = airetyApp.collection.baseCollection.extend({
		model: airetyApp.model.user
	});

	airetyApp.collection.chats = airetyApp.collection.baseCollection.extend({
		model: airetyApp.model.chat
	});

	airetyApp.collection.textChats = airetyApp.collection.baseCollection.extend({
		model: airetyApp.model.textChat
	});

	 //
    //Model exporting/importing for node.js / redis
    //
    
    Backbone.Model.prototype.xport = function (opt) {
        var result = {},
        settings = _({recurse: true}).extend(opt || {});

        function process(targetObj, source) {
            targetObj.id = source.id || null;
            targetObj.cid = source.cid || null;
            targetObj.attrs = source.toJSON();
            _.each(source, function (value, key) {
            // since models store a reference to their collection
            // we need to make sure we don't create a circular refrence
                if (settings.recurse) {
                  if (key !== 'collection' && source[key] instanceof Backbone.Collection) {
                    targetObj.collections = targetObj.collections || {};
                    targetObj.collections[key] = {};
                    targetObj.collections[key].models = [];
                    targetObj.collections[key].id = source[key].id || null;
                    _.each(source[key].models, function (value, index) {
                      process(targetObj.collections[key].models[index] = {}, value);
                    });
                  } else if (source[key] instanceof Backbone.Model) {
                    targetObj.models = targetObj.models || {};
                    process(targetObj.models[key] = {}, value);
                  }
               }
            });
        }

        process(result, this);

        return JSON.stringify(result);
    };


    Backbone.Model.prototype.mport = function (data, silent) {
        function process(targetObj, data) {
            targetObj.id = data.id || null;
            targetObj.set(data.attrs, {silent: true});
            // loop through each collection
            if (data.collections) {
              _.each(data.collections, function (collection, name) {
                targetObj[name].id = collection.id;
                _.each(collection.models, function (modelData, index) {
                  var newObj = targetObj[name].add({}, {silent: true}).last();
                  process(newObj, modelData);
                });
              });
            }

            if (data.models) {
                _.each(data.models, function (modelData, name) {
                    process(targetObj[name], modelData);
                });
            }
        }
        process(this, JSON.parse(data));
        return this;
    };

})()
