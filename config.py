import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_school_management_portal_2026')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///school_portal.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
