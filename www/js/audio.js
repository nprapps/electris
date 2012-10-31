$(function(){
    
    var POLLING_INTERVAL = 60000;
    
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
    
    function fireItUp(){
        $.getJSON('status.json?t=' + (new Date()).getTime(), function(status) {
            if(status['audio'] == 'true') {
                if(status['streaming'] == 'true') {
                    playStream(status['flashStreamer'],status['flashFile'],status['htmlUrl'],status['title'],status['prompt'],status['feedback']); 
                } else {
                    playFile(status['url'],status['title'],status['prompt'],status['feedback']); 
                }
                $("body").removeClass("no-audio");
                $("body").addClass("audio");
            } else {
                $("body").removeClass("audio");
                $("body").addClass("no-audio");
            }
        });
    }
    
    fireItUp();
    setInterval(fireItUp, POLLING_INTERVAL);
});