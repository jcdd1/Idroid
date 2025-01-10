import os
class Config:
    SECRET_KEY = os.urandom(24)
    DEBUG=True
    SQLALCHEMY_DATABASE_URI = 'postgresql://inventario_Idroid_owner:2pQNire8VEhz@ep-royal-pond-a5x382p0.us-east-2.aws.neon.tech/inventario_Idroid?sslmode=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

