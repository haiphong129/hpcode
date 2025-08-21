from flask import Flask, render_template, redirect, url_for, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_simplemde import SimpleMDE
app = Flask(__name__)
app.config['SIMPLEMDE_JS_IIFE'] = True
app.config['SIMPLEMDE_USE_CDN'] = True
SimpleMDE(app)

ckeditor = CKEditor(app)
app.config.from_object(Config)
db = SQLAlchemy(app,engine_options={'connect_args': { 'timeout': 10 }})
migrate = Migrate(app, db)
#db.init_app(app)
login = LoginManager(app) 
login.login_view = 'login'
from app import routes, models
with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)
# if __name__ == '__main__':  
#      app.run(port=80,debug=True, ssl_context=context)