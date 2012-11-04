#!/usr/bin/env python

from webassets import Environment
from webassets import Bundle

environment = Environment('./www', '/')

header_js = Bundle(
    'js/lib/jquery-1.8.1.min.js',
    'js/lib/modernizr.js',
    'js/responsive-ad.js',
    #filters='uglifyjs',
    output='js/electris-header.min.js')

footer_js = Bundle(
    'js/lib/underscore-min.js',
    'js/lib/moment.min.js',
    'js/lib/jquery.timeago.js',
    'js/lib/jquery.touchclick.js',
    'bootstrap/js/bootstrap.min.js',
    'js/audio.js',
    'js/app.js',
    #filters='uglifyjs',
    output='js/electris-footer.min.js')

css = Bundle(
    'bootstrap/css/bootstrap.min.css',
    'bootstrap/css/bootstrap-responsive.min.css',
    'css/template.css',
    'css/app.css',
    'css/sponsorship.css',
    #filters='yui_css',
    output='css/electris.min.css')

environment.register('js_header', header_js)
environment.register('js_footer', footer_js)
environment.register('css', css)
