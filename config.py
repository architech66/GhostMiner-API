import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_this_for_prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'fSociety.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
