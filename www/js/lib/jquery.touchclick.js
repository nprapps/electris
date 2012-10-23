/**
 * jQuery touch click - v1.0 - 4/22/2012
 * https://github.com/pesblog/jquery-touch-click
 *
 * Copyright (c) 2012 "pesblog" Noritak Baba
 * Licensed under the MIT licenses.
 */

// About: Examples
// https://github.com/pesblog/jquery-touch-click/blob/master/examples/index.html

;(function ( $, window, undefined ) {

    var pluginName = 'touchClick';
    var defaults = {
    	className: 'spinner',
        callback: function(){
            console.log('touchClick');
        }
    };

    var isTouch = ('ontouchend' in window);
    var touchstartEvent = isTouch ? 'touchstart.'+pluginName : 'mousedown.'+pluginName;
    var touchmoveEvent = isTouch ? 'touchmove.'+pluginName : 'mousemove.'+pluginName;
    var touchendEvent = isTouch ? 'touchend.'+pluginName : 'mouseup.'+pluginName;

    function Plugin( element, className, callback ) {
	    this.element = element;
        if (typeof className === 'function'){
            this.options = {};
            this.options.className = defaults.className;
            this.options.callback = className;
        } else {
            this.options = {
                className: className || defaults.className,
                callback: callback || defaults.callback
            };
        }
	    this._defaults = defaults;
	    this._name = pluginName;
	    this.init();
    }

    Plugin.prototype.init = function () {
        var self = this;
        var $element = $(self.element);
        var className = self.options.className;
        var callback = self.options.callback;
        $element
            .bind(touchstartEvent, function(e) {
                this.touchClickStart = true;
                $element.addClass( className );
            })
            .bind(touchmoveEvent, function(e) {
                if ( this.touchClickStart ) {
                    this.touchClickStart = undefined;
                    // $element.removeClass( className );
                }
            })
            .bind(touchendEvent, function(e) {
                var dom = this;
                if ( this.touchClickStart ) {
                    this.touchClickStart = undefined;
                    // $element.removeClass( className );
                    setTimeout(function(){
                        $.proxy(callback, dom)(e)
                    }, 0);
                }
            });
    };

    $.fn[pluginName] = function ( className, callback ) {
	    return this.each(function () {
	        if (!$.data(this, 'plugin_' + pluginName)) {
		        $.data(this, 'plugin_' + pluginName,
		               new Plugin( this, className, callback ));
	        }
	    });
    };

})( jQuery, window );
