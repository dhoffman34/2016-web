import os

from flask import Flask, g, abort

from flask_babel import Babel
import flask_assets as assets
from typogrify.templatetags import jinja_filters as typogrify_filters

from webassets.filter import get_filter

from web.views import *


def create_app(configfile=None):
    app = Flask(__name__)

    app.config.from_object('web.config.Config')

    # Typography Jinja2 Filter
    app.jinja_env.filters['typogrify'] = typogrify_filters.typogrify

    # Static Assets Config (Javascript and SCSS)
    env = assets.Environment(app)

    env.load_path = [
        os.path.join(app.config['STATIC_PATH'], 'bower'),
        os.path.join(app.config['STATIC_PATH'], 'scss'),
        os.path.join(app.config['STATIC_PATH'], 'javascript')
    ]

    env.register('js_all',
                 assets.Bundle('jquery/dist/jquery.min.js',
                               'leaflet/dist/leaflet.js',
                               assets.Bundle('app.js'),
                               output='app.js'))

    sass = get_filter('scss')
    sass.load_paths = env.load_path

    env.register('css_all',
                 assets.Bundle('app.scss',
                               filters=(sass,),
                               depends=(os.path.join(app.config['STATIC_PATH'],
                                        'scss/**/*.scss')),
                               output='app.css'))

    # i18n Config
    babel = Babel(app)

    @app.url_defaults
    def set_language_code(endpoint, values):
        if 'lang_code' in values or not g.get('lang_code', None):
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

    @app.url_value_preprocessor
    def get_lang_code(endpoint, values):
        if values is not None:
            g.lang_code = values.pop('lang_code', None)

    @app.before_request
    def ensure_lang_support():
        lang_code = g.get('lang_code', None)
        if lang_code and lang_code not in app.config['LANGUAGES'].keys():
            return abort(404)

    @babel.localeselector
    def get_locale():
        return g.get('lang_code', app.config['BABEL_DEFAULT_LOCALE'])

    @babel.timezoneselector
    def get_timezone():
        return app.config['BABEL_DEFAULT_TIMEZONE']

    # Register the Blueprints
    app.register_blueprint(view_pages, url_prefix='/<lang_code>')
    app.register_blueprint(view_schedule, url_prefix='/<lang_code>/schedule')

    return app
