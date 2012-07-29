var thisPage = $(this);

$(window).bind('scroll', function(){  
	thisPageTop = thisPage.scrollTop();

	console.log(thisPageTop);

/*
	if(thisPageTop > 14 && !panel.hasClass('fboxFloat')){
		panel.addClass('fboxFloat');
		panel.addClass('fboxPad');
		$("#crumbNav").addClass('fboxCrumbFloat');
		$("#padset").show();
	} else if(thisPageTop <= 14 && panel.hasClass('fboxFloat')){ 
		panel.removeClass('fboxFloat');
		panel.removeClass('fboxPad');
		$("#crumbNav").removeClass('fboxCrumbFloat');
		$("#padset").hide();
	}
*/
});