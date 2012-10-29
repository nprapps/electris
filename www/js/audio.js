function play5Audio() {
	document.getElementById('livestreamer').play();
	$("#playcon5").empty();
	$("#playcon5").append("<img src='img/pauseButtonOver.png' onclick='pause5Audio();' />");
	if ($("#playerdisp .loading").length > 0) {
		$('#playerdisp .loading').remove();
	}
	if ($("#playerdisp .playing").length == 0) {
		$('#playerdisp').append('<div class="playing"><p>Live</p></div>');
		$('#eq_gfx').html('<img src="img/eq2.gif" />');
	}
}

function pause5Audio() {
	document.getElementById('livestreamer').pause();
	$("#playcon5").empty();
	$("#playcon5").append("<img src='img/playButtonOver.png' onclick='play5Audio();' />");
	
	$('#eq_gfx').html('<img src="img/eq-none.gif" />');
	$('#playerdisp .playing').remove();
	$('#playerdisp').append('<div class="loading loading-live"><p></p></div>');
}


$(function(){

	var jwPlayerAdUrl = 'http://ad.doubleclick.net/pfadx/n6735.NPR.MUSIC/music;theme=1039;storyid=157840374;testserver=true;embed=npr;mediatype=video;sz=400x300;dcmt=text/xml;ord=66802162';
	var jwPlayerAutoStart = 'false';
	if (true) {
		if (NPR.PageInfo.getUrlParameter('autoplay') == 'true') {
			jwPlayerAutoStart = 'true';
		}
	}
									
	if (navigator.userAgent.toLowerCase().match(/(iphone|ipod|ipad)/)) {
		$('#playercon').append("<div id='audioSrc' style='display: none'><audio id='livestreamer' src='http://pd.npr.org/anon.npr-mp3/npr/totn/2012/10/20121010_totn_01.mp3' controls='false'></audio></div>");
		$('#theplayer').append("<div id='playcon5'><img src='img/playButtonOver.png' onclick='play5Audio();' /></div>");
				
	} else {
		jwplayer('jwplayer').setup({
			modes: [{
				type: 'flash',
				src: 'http://www.npr.org/templates/javascript/jwplayer/player.swf',
				config: {
					skin: 'http://www.npr.org/design/stage/audioTest/live-convention-controls.zip',
					playlist: [{
                        // file: 'live3audio@52188',
                        // provider: 'rtmp',
                        // streamer: 'rtmp://cp150999.live.edgefcs.net/live/'
                        file: 'http://pd.npr.org/anon.npr-mp3/npr/totn/2012/10/20121010_totn_01.mp3',
                        provider: '',
                        streamer: ''
					}
				
					]
				}
			}, {
				type: 'html5',
				config: {
					playlist: [{
													
					}
				
					]
				}
			}],
			bufferlength: '5',
			controlbar: 'bottom',
			autostart: jwPlayerAutoStart,
			width: '41',
			height: '41',
			plugins: {
				'gapro-2': {
					'trackingobject': '_gaq',
					'trackstarts': 'true',
					'trackpercentage': 'true',
					'tracktime': 'true'
				}
			},
			events: {
				onBuffer: function () {
					if ($("#playerdisp .loading").length == 0) {
						$('#playerdisp .playing').remove();
						$('#playerdisp').append('<div class="loading loading-live"><p>Loading...</p></div>');
					}
				},
				onPlay: function () {
					if ($("#playerdisp .loading").length > 0) {
						$('#playerdisp .loading').remove();
					}
					if ($("#playerdisp .playing").length == 0) {
						$('#playerdisp').append('<div class="playing"><p>Live</p></div>');
						$('#eq_gfx').html('<img src="img/eq2.gif" />');
					}
				},
				onPause: function() {
					$('#eq_gfx').html('<img src="img/eq-none.gif" />');
					$('#playerdisp .playing').remove();
					$('#playerdisp').append('<div class="loading loading-live"><p></p></div>');
				}
			}
										   
									  
				
		});
	}
    
    // TODO: refactor so that it works based on a bit we flip or something, probably a nice function
    
	var _status = '';
    var isLive = 'TRUE';
    
	if (isLive == 'FALSE' && _status != 'FALSE') {
		$('body').addClass('comingSoon');
		if (!navigator.userAgent.toLowerCase().match(/(iphone|ipod|ipad)/)) {
			jwplayer().stop();
		}
		$('#comingsoon').show();
		$('#comingsoon').css("visibility", "visible");
		$('#playercon').hide();
		_status = 'FALSE';
	// if we're LIVE
	} else if (isLive == 'TRUE' && _status != 'TRUE') {
		$('body').removeClass('comingSoon');
		$('#comingsoon').hide();
		$('#playercon').show();
		$('#playercon').css("visibility", "visible");
		_status = 'TRUE';
	}
});