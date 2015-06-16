from flask import Flask
from flask_mail import Mail
from hashids import Hashids


app = Flask(__name__, instance_relative_config=True)

###################################################
#Load Configuration Files
###################################################
app.config.from_object('config')
app.config.from_pyfile('secret_config.py.')

###################################################
#Activate Flask Extension
###################################################
mail = Mail(app)

###################################################
#Misc Initializations and fucntions
###################################################
hashid = Hashids(salt=app.config['HASHIDS_SALT'], min_length=app.config['HASHIDS_MIN_LENGTH']) 

custom_slugify = Slugify(to_lower=True)

def sluggy(name):
    name = custom_slugify(name)
    name = secure_filename(name)
    return name
