$(function(){
	console.log('ping');
	console.log(window.location.search);

    if(window.location.search.indexOf('studio') > 0) {
    	$('body').addClass('studio');
    }
});
