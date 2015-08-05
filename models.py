import datetime
import faker
import json
import logging
import logging.handlers
import os
from passlib.hash import bcrypt
from peewee import *
import shortuuid
import unittest

from helper import OUTPUT_PATHS
from helper import make_dir
####################################################
# Misc Setup
####################################################
fake = faker.Factory.create()

####################################################
# Logging Boilerplate
####################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)15s - %(levelname)s - %(message)s')
console_handle = logging.StreamHandler()
console_handle.setFormatter(formatter)
logger.addHandler(console_handle)
LOG_FILENAME = "muchamuck_models.log"
file_handle = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handle = logging.FileHandler('muchamuck_models.log')
file_handle.setFormatter(formatter)
logger.addHandler(file_handle)
#logger.info('log message')

####################################################
# Database Connection
####################################################
db = MySQLDatabase('database_name', host="localhost",
                   user='username', password="password")


####################################################
# Utilities
####################################################
def jsonifyer(someDict):
    return json.dumps(someDict, sort_keys=True, indent=4, separators=(',', ': '))

####################################################
# Base Model
####################################################
class BaseModel(Model):
  class Meta:
    database = db




####################################################
# User Model
####################################################
class User(BaseModel):
    created_date = DateTimeField(default=datetime.datetime.now)
    email = CharField(index=True, unique=True)
    password = CharField(null=True)
    public_email = CharField(default="")
    name = CharField(default="")
    bio = CharField(default="")
    twitter = CharField(default="")
    facebook = CharField(default="")
    google = CharField(default="")

    customer_id = CharField(default="")
    uuid = CharField(index=True)

    def generate_UUID(self):
        self.uuid = shortuuid.ShortUUID().random()

    def encrypt_password(self, password):
        self.password = bcrypt.encrypt(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def to_dict(self):
            userDict = {}
            userDict["created_date"] = self.created_date.isoformat()
            userDict["email"] = self.public_email
            userDict["name"] = self.name
            userDict["uuid"] = self.uuid
            userDict["bio"] = self.bio
            userDict["twitter"] = self.twitterID
            userDict["facebook"] = self.facebookID
            userDict["google"] = self.googleID
            return userDict

    def make_dir(self):
        make_dir(self.get_user_dir_path())

    def get_user_dir_path(self):
        return os.path.join(OUTPUT_PATHS.get("json_user"), self.uuid)

    def get_json_path(self):
        return os.path.join(self.get_user_dir_path(), "about.json")

    def write_json(self):
        self.make_dir()
        user_dict = self.to_dict()
        file_object = open(self.get_json_path(), "wb")
        file_object.write(jsonifyer(user_dict))
        file_object.close()


def create_dummy_user():
    user = User()
    user.generate_UUID()
    user.email = fake.free_email()
    user.encrypt_password(fake.password())
    user.name = fake.name()
    user.public_email = fake.free_email()
    user.bio = fake.text()
    user.twitterID = shortuuid.ShortUUID().random()
    user.facebookID = shortuuid.ShortUUID().random()
    user.googleID = shortuuid.ShortUUID().random()
    return user


####################################################
# Site Model
####################################################
class Site(BaseModel):
    description = CharField(null=True)
    domain = CharField(unique=True)
    language = CharField(default="en-us")
    owner = ForeignKeyField(User)
    title = CharField()
