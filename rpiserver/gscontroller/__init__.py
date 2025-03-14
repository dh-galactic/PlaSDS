from flask import Flask
from .GalacticSamplerController import GalacticSamplerController


def create_app():
    app = Flask(__name__)
    gsc = GalacticSamplerController(app)

    return app
