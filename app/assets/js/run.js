$(function() {
	airety.run = function() {
		airety.app = new airetyApp.view.appView();
		airety.route = new airetyApp.router.primary;	
		Backbone.history.start({ pushState: true });
	};
	
	/* initialize application */
	
	airety.run();
});
