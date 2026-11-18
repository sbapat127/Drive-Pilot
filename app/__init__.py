import os
from flask import Flask
 
 
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="change-me-before-deploying",
        DATABASE=os.path.join(app.instance_path, "driving.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
 
    os.makedirs(app.instance_path, exist_ok=True)
 
    from . import db
    db.init_app(app)
 
    @app.route("/")
    def index():
        return "<h1>Blank Homepage</h1>"
 
    #Blueprints get registered here as you build them, e.g.
    from . import auth
    app.register_blueprint(auth.bp)
    return app