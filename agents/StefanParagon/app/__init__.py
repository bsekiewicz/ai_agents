import os

from dotenv import load_dotenv
from flask import Flask

from .models.database import init_db, get_db_connection

# Load environment variables from .env file
load_dotenv()


def create_app():
    app = Flask(__name__)

    with app.app_context():
        init_db()
        from . import routes

    # Access your OpenAI API key
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

    # Your Flask app initialization logic here
    return app
