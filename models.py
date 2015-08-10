# -*- coding: utf-8 -*-
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
#Config
####################################################
DB_INFO = {}
"""int: Module level variable documented inline.

The docstring may span multiple lines. The type may optionally be specified
on the first line, separated by a colon.
"""
DB_INFO['host'] = os.environ['MUCKAMUCK_DB_HOST']
DB_INFO['name'] = os.environ['MUCKAMUCK_DB_NAME']
DB_INFO['username'] = os.environ['MUCKAMUCK_DB_USER_NAME']
DB_INFO['password'] = os.environ['MUCKAMUCK_DB_USER_PASSWORD']

OUTPUT_PATHS = {}
OUTPUT_PATHS['root'] =  os.environ['MUCKAMUCK_OUTPUT_DIRECTORY']

OUTPUT_PATHS['audio']  = os.path.join(OUTPUT_PATHS['root'], "audio")
OUTPUT_PATHS['css']  = os.path.join(OUTPUT_PATHS['root'], "css")
OUTPUT_PATHS['hbs']  = os.path.join(OUTPUT_PATHS['root'], "hbs")
OUTPUT_PATHS['img']  = os.path.join(OUTPUT_PATHS['root'], "img")

OUTPUT_PATHS['js']  = os.path.join(OUTPUT_PATHS['root'], "js")

OUTPUT_PATHS['json']  = os.path.join(OUTPUT_PATHS['root'], "json")
OUTPUT_PATHS['json_site']  = os.path.join(OUTPUT_PATHS['json'], "site")
OUTPUT_PATHS['json_system']  = os.path.join(OUTPUT_PATHS['json'], "system")
OUTPUT_PATHS['json_user']  = os.path.join(OUTPUT_PATHS['json'], "user")

OUTPUT_PATHS['site']  = os.path.join(OUTPUT_PATHS['root'], "site")
OUTPUT_PATHS['site_domain']  = os.path.join(OUTPUT_PATHS['site'], "domain")
OUTPUT_PATHS['site_id']  = os.path.join(OUTPUT_PATHS['site'], "id")

####################################################
# Setup
####################################################
fake = faker.Factory.create()

####################################################
# Misc Helpers
####################################################
def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)



####################################################
# Database Connection
####################################################
db = MySQLDatabase(DB_INFO['name'], host=DB_INFO['host'], user=DB_INFO['username'], password=DB_INFO['password'])


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
    """The User Object.
    """
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
        """This function generates a shortish UUID.
        """
        self.uuid = shortuuid.ShortUUID().random()

    def encrypt_password(self, password):
        """This function encrypts password with bcrypt
        :param name: password
        :type name: str.
        """
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
json_site_subdirs = ["archive", "category", "page", "post", "tag"]

class Site(BaseModel):
    created_date = DateTimeField(default=datetime.datetime.now)
    description = CharField(null=True)
    domain = CharField(unique=True)
    language = CharField(default="en-us")
    owner = ForeignKeyField(User)
    subscription_level = CharField(default="free", index=True)
    title = CharField()
    uuid = CharField(index=True)

    def generate_UUID(self):
        self.uuid = shortuuid.ShortUUID().random()

    def to_dict(self):
            siteDict = {}
            siteDict["created_date"] = self.created_date.isoformat()
            siteDict["description"] = self.description
            siteDict["domain"] = self.domain
            siteDict["language"] = self.language
            siteDict["owner"] = self.owner.uuid
            siteDict["subscription_level"] = self.subscription_level
            siteDict["title"] = self.title
            siteDict["uuid"] = self.uuid
            return siteDict

    def get_site_dir_path(self):
        return os.path.join(OUTPUT_PATHS.get("json_site"), self.uuid)

    def get_site_dir_subdir_path(self, dir_name):
        return os.path.join(OUTPUT_PATHS.get("json_site"), self.uuid, dir_name)


    def make_dir(self):
        make_dir(self.get_site_dir_path())
        for subdir in json_site_subdirs:
            make_dir(self.get_site_dir_subdir_path(subdir))

    def get_json_path(self):
        return os.path.join(self.get_site_dir_path(), "about.json")

    def write_json(self):
        self.make_dir()
        user_dict = self.to_dict()
        file_object = open(self.get_json_path(), "wb")
        file_object.write(jsonifyer(user_dict))
        file_object.close()

def create_dummy_site():
    user = create_dummy_user()
    user.save()
    site = Site()
    site.description = fake.text(max_nb_chars=200)
    site.domain = fake.domain_name()
    site.owner = user
    site.title = fake.sentence(nb_words=6, variable_nb_words=True)
    site.generate_UUID()
    return site
