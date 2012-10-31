// does the analytics plugin work?
// do we want to use the HTML5 version more frequently? why default to flash?
// is there supposed to be an ad?

$(function(){
    
    function playStream(flashStreamer,flashFile,htmlUrl,title,prompt,feedback){
        play(true,flashStreamer,flashFile,htmlUrl,title,prompt,feedback);
    }

    function playFile(url,title,prompt,feedback){
        play(false,'',url,url,title,prompt,feedback);
    }
    
    function play(streaming,flashStreamer,flashFile,htmlUrl,title,prompt,feedback) {
        //jwplayer uses the video tag, even for html5 audio, so we kick it to the curb for iOS
        //but we want to use the flash player when possible to get the analytics and stuff
        if (navigator.userAgent.toLowerCase().match(/(iphone|ipod|ipad)/)) {
            setupHtmlPlayer(htmlUrl);
        } else {
            setupFlashPlayer(streaming,flashStreamer,flashFile);
        }
        setupAudioInterface(title,prompt,feedback);
    }

    function setupFlashPlayer(streaming,streamer,file){
        var options = {
            file: file,
            modes: [
                {
                    type: 'flash',
                    src: 'http://www.npr.org/templates/javascript/jwplayer/player.swf'
                }
            ],
            skin: 'http://www.npr.org/design/stage/audioTest/live-convention-controls.zip',
            controlbar: 'bottom',
            width: '41',
            height: '41',
            bufferlength: '5',
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
                    $('#audio').addClass('buffering');
                    $('#audio').removeClass('playing');
				},
				onPlay: function () {
                    $('#audio').removeClass('buffering');
                    $('#audio').addClass('playing');
				},
				onPause: function() {
                    $('#audio').removeClass('buffering');
                    $('#audio').removeClass('playing');
				}
			}
        }
    
        if(streaming){
            options['provider'] = 'rtmp';
            options['streamer'] = streamer;
        }
        
        jwplayer('jwplayer').setup(options);
    }

    function setupHtmlPlayer(url){
        $('#audio-htmlcontrol').show();
        $('#audio-htmlstream')[0].src = url;
    }

    function setupAudioInterface(title,prompt,feedback){
        //just in case we're switching to a new stream
        $('#audio').removeClass('buffering');
        $('#audio').removeClass('playing');
    
        $("#audio-title").text(title);
        $("#audio-prompt").text(prompt);
        $("#audio-feedback #audio-feedback-message").text(feedback);
    }
    
    //interactivity for the html player
    $('#audio-htmlcontrol').click(function(){
        var player = $('#audio-htmlstream')[0];
        if(player.paused) {
            player.play();
            $('#audio').addClass('playing');
        } else {
            player.pause();
            $('#audio').removeClass('playing');
        }
    });
    
    $("#switch").click(function(){
        playFile('http://pd.npr.org/anon.npr-mp3/npr/totn/2012/10/20121010_totn_01.mp3', "NPR Pre-Election Special:", "Listen Now", "Previously recorded"); 
    })
    
    playStream('rtmp://cp42183.live.edgefcs.net/live/', 'Live1@1094', 'http://npr.ic.llnwd.net/stream/npr_live24', "NPR Special Coverage:", "Listen Now", "Live"); 
});