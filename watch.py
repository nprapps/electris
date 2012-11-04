from webassets import Environment
from webassets import Bundle

static = Environment('./www', '/')
static.cache = False

header_js = Bundle(
        'js/lib/jquery-1.8.1.min.js',
        'js/lib/modernizr.js',
        'js/responsive-ad.js',
        filters='uglifyjs',
        output='js/electris-header.min.js')

footer_js = Bundle(
    'js/lib/underscore-min.js',
    'js/lib/moment.min.js',
    'js/lib/jquery.timeago.js',
    'js/lib/jquery.touchclick.js',
    'bootstrap/js/bootstrap.min.js',
    'js/audio.js',
    'js/app.js',
    filters='uglifyjs',
    output='js/electris-footer.min.js')

css = Bundle(
    'bootstrap/css/bootstrap.min.css',
    'bootstrap/css/bootstrap-responsive.min.css',
    'css/template.css',
    'css/app.css',
    'css/sponsorship.css',
    filters='yui_css',
    output='css/electris.min.css')

static.register('js_header', header_js)
static.register('js_footer', footer_js)
static.register('css', css)

header_js.urls()
footer_js.urls()
css.urls()

import logging
from webassets.script import CommandLineEnvironment

# Setup a logger
log = logging.getLogger('webassets')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)

cmdenv = CommandLineEnvironment(static, log)
cmdenv.watch()