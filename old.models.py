# -*- coding: utf-8 -*-
#!/usr/bin/python
import datetime
from passlib.hash import bcrypt
from faker import Factory
import json
import logging
import logging.handlers
import os
from peewee import *
from playhouse.postgres_ext import *
import shortuuid
from slugify import slugify, Slugify
import unittest


SITES_DIR = "/home/jason/Desktop/muckamuck_shit/sites"
json_dir = "/home/jason/Desktop/muckamuck_shit"
user_json_dir = os.path.join(json_dir, "user")


fake = Factory.create()
sluggy = Slugify(to_lower=True)

def jsonifyer(someDict):
    return json.dumps(someDict, sort_keys=True, indent=4, separators=(',', ': '))


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

db = PostgresqlExtDatabase('directorium', user='jason', register_hstore=False)
####################################################
# Base Model
####################################################
class BaseModel(Model):
    created_date = DateTimeField(default=datetime.datetime.now)
    uuid = CharField(index=True)

    class Meta:
        database = db

    def to_json(self):
        return jsonifyer(self.to_dict())

    def generate_UUID(self):
        self.uuid = shortuuid.ShortUUID().random()
        #logger.debug("Generated UUID: " + self.uuid)

####################################################
# User Model
####################################################

class User(BaseModel):
    admin = BooleanField(default=False)
    email = CharField(index=True, unique=True)
    password = CharField(null=True)
    public_name = CharField(default="")
    public_email = CharField(default="")

    def json_location(self):
        return os.path.join(user_json_dir, self.uuid + ".json")

    def encrypt_password(self, password):
        self.password = bcrypt.encrypt(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def to_dict(self):
        userDict = {}
        userDict["created_date"] = self.created_date.isoformat()
        userDict["email"] = self.public_email
        userDict["name"] = self.public_name
        userDict["uuid"] = self.uuid
        return userDict

    def dummy(self):
        self.generate_UUID()
        self.email = fake.free_email()
        self.encrypt_password(fake.password())
        self.public_name = fake.name()
        self.public_email = fake.free_email()

def create_dummy_user():
    user = User()
    user.generate_UUID()
    user.email = fake.free_email()
    user.encrypt_password(fake.password())
    user.public_name = fake.name()
    user.public_email = fake.free_email()
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

    def site_dir(self):
        return os.path.join(SITES_DIR, self.uuid)

    def site_post_dir(self):
        return os.path.join(self.site_dir(), "post")

    def site_json_dir(self):
        return os.path.join(self.site_dir(), "json")

    def make_dir(self):
        if not os.path.exists(self.site_dir()):
            os.makedirs(self.site_dir())
        if not os.path.exists(self.site_post_dir()):
            os.makedirs(self.site_post_dir())
        if not os.path.exists(self.site_json_dir()):
            os.makedirs(self.site_json_dir())


    def to_dict(self):
        siteDict = {}
        siteDict["created_date"] = self.created_date.isoformat()
        siteDict['description'] = self.description
        siteDict['domain'] = self.domain
        siteDict['language'] = self.language
        siteDict['owner'] = self.owner.to_dict()
        siteDict['title'] = self.title
        siteDict['uuid'] = self.uuid
        return siteDict

    def dummy(self, owner):
        self.generate_UUID()
        self.description = fake.text(max_nb_chars=200)
        self.domain = fake.domain_name()
        self.language = fake.locale()
        self.owner = owner
        self.title = fake.company()


def create_dummy_site(owner):
    site = Site()
    site.generate_UUID()
    site.description = fake.text(max_nb_chars=200)
    site.domain = fake.word() + "_" + fake.word() + "_" + fake.word() + ".muckamuck.net"
    site.language = fake.locale()
    site.owner = owner
    site.title = fake.company()
    return site

def get_random_site():
    site = Site.select().order_by(fn.Random()).limit(1)[0]
    return site
####################################################
# Theme Model
####################################################
class Theme(BaseModel):
    site = ForeignKeyField(Site, unique=True)
    template = TextField()

def create_dummy_theme(site):
    theme = Theme()
    theme.generate_UUID()
    theme.site = site
    file_object = open("render_templates/dummy_theme.html", "r")
    theme.template = file_object.read()
    return theme

####################################################
# Membership Model
####################################################
class Membership(BaseModel):
    site = ForeignKeyField(Site, unique=True)
    user = ForeignKeyField(User)
    class Meta:
        indexes = (
            (('site', 'user'), True),
        )

def check_membership(site, user):
    try:
        membership = Membership.get( (Membership.site == site) & (Membership.user == user))
    except Membership.DoesNotExist:
        return False
    return True

def make_member(site, user):
    membership = Membership()
    membership.generate_UUID()
    membership.site = site
    membership.user = user
    return membership

####################################################
# Page Model
####################################################
class Page(BaseModel):
    author = ForeignKeyField(User)
    body = TextField()
    description = CharField()
    slug = CharField()
    site = ForeignKeyField(Site)
    title = CharField()
    class Meta:
        indexes = (
            (('site', 'slug'), True),
        )

    def to_dict(self):
        pageDict = {}
        pageDict["created_date"] = self.created_date.isoformat()
        pageDict['author'] = self.author.to_dict()
        pageDict['body'] = self.body
        pageDict['site'] = self.site.to_dict()
        pageDict['slug'] = self.slug
        pageDict['title'] = self.title
        pageDict['uuid'] = self.uuid
        return pageDict


def create_dummy_page(site, author):
    page = Page()
    page.generate_UUID()
    page.author = author
    page.body = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
    page.site = site
    page.title = fake.words(nb=3)
    page.slug = sluggy(page.title)
    return page

####################################################
# Post Model
####################################################
class Post(Page):
    #author = ForeignKeyField(User)
    #body = TextField()
    #description = CharField()
    #slug = CharField()
    #site = ForeignKeyField(Site)
    tags = ArrayField(CharField)
    #title = CharField()


    def to_dict(self):
        postDict = {}
        postDict["created_date"] = self.created_date.isoformat()
        postDict['author'] = self.author.to_dict()
        postDict['body'] = self.body
        postDict['description'] = self.description
        postDict['site'] = self.site.to_dict()
        postDict['slug'] = self.slug
        postDict['tags'] = self.tags
        postDict['title'] = self.title
        postDict['uuid'] = self.uuid
        return postDict

    def dummy(self, site, author):
        self.generate_UUID()
        self.author = author
        self.body = fake.paragraph(nb_sentences=15, variable_nb_sentences=True)
        self.description = fake.text(max_nb_chars=200)
        self.site = site
        self.title = fake.word() + "_" + fake.company() + " " + fake.word() + " " + fake.word()
        self.slug = sluggy(self.title)
        self.tags = fake.words(nb=3)
        self.tags.append("tag")

    def json_path(self):
        return os.path.join(self.site.site_json_dir(), self.slug + ".json")

    def write_json(self):
        file_object = open(self.post_json_path(), "wb")
        file_object.write(self.to_json())
        file_object.close()


def create_dummy_post(site, author):
    post = Post()
    post.generate_UUID()
    post.author = author
    post.body = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
    post.description = fake.text(max_nb_chars=200)
    post.site = site
    post.title = fake.word() + "_" + fake.company() + " " + fake.word() + " " + fake.word()
    post.slug = sluggy(post.title)
    post.tags = fake.words(nb=3)
    post.tags.append("tag")
    return post

def get_random_post_from_site(site_uuid):
    site = Site.select().where(Site.uuid == site_uuid).get()
    post = Post.select().where(Post.site == site).order_by(fn.Random()).limit(1)[0]
    return post

####################################################
# Tags
####################################################
def get_site_tags(uuid):
    site = Site.select().where(Site.uuid == uuid).get()
    tag_set = set()
    for post in Post.select().where(Post.site == site).iterator():
        for tag in post.tags:
            tag_set.add(tag)
    return tag_set


def reset_db():
    db.drop_tables([User, Site, Page, Post, Membership, Theme])
    db.create_tables([User, Site, Page, Post, Membership, Theme])

####################################################
# Tests
####################################################



#create_dummy_user().save()

class FooTest(unittest.TestCase):

    def setUp(self):
        db.connect()
        try:
            db.drop_tables([User, Site, Page, Post, Membership, Theme])
        except:
            pass
        db.create_tables([User, Site, Page, Post, Membership, Theme])

    # ending the test
    def tearDown(self):
        pass
    ####################################################
    # Membership Tests
    ####################################################
    def test_Check_Membership(self):
        user = create_dummy_user()
        user.save()
        site = create_dummy_site(user)
        site.save()
        membership = make_member(site, user)
        membership.save()
        self.assertTrue(check_membership(site, user))


    def test_Check_No_Membership(self):
        user = create_dummy_user()
        user.save()
        site = create_dummy_site(user)
        site.save()
        self.assertFalse(check_membership(site, user))

    def test_Duplicate_Membership(self):
        user = create_dummy_user()
        user.save()
        site = create_dummy_site(user)
        site.save()
        membership1 = make_member(site, user)
        membership1.save()
        with self.assertRaises(IntegrityError):
            membership2 = make_member(site, user)
            membership2.save()

    ####################################################
    # Page Tests
    ####################################################
    def test_Count_Page(self):
        user = create_dummy_user()
        user.save()
        site = create_dummy_site(user)
        site.save()
        for i in range(10):
            page = create_dummy_page(site, user)
            page.save()
            #print page.to_json()
        self.assertEqual(Page.select().count(), 10)

    ####################################################
    # Post Tests
    ####################################################
    def test_Count_Page(self):
        user = create_dummy_user()
        user.save()
        site = create_dummy_site(user)
        site.save()
        for i in range(10):
            post = Post()
            post.dummy(site, user)
            post.save()
            #print post.to_json()
        self.assertEqual(Post.select().count(), 10)

    ####################################################
    # Site Tests
    ####################################################
    def test_Count_Sites(self):
        user = create_dummy_user()
        user.save()
        for i in range(10):
            site = create_dummy_site(user)
            site.save()
            #print site.to_json()
        self.assertEqual(Site.select().count(), 10)



    ####################################################
    # User Tests
    ####################################################
    def test_Count_Users(self):
        for i in range(10):
            user = create_dummy_user()
            user.save()
            #print user.to_json()
        self.assertEqual(User.select().count(), 10)

    def test_Create_User(self):
        user_email = fake.free_email()
        user = User()
        user.generate_UUID()
        original_uuid = user.uuid
        user.email = user_email
        user.save()
        user2 = User.get(User.email == user_email)
        self.assertEqual(user2.uuid, user.uuid)

    def test_Create_Duplicate_User(self):
        user_email = fake.free_email()

        user1 = User()
        user1.generate_UUID()
        user1.email = user_email
        user1.save()

        user2 = User()
        user2.generate_UUID()
        user2.email = user_email
        with self.assertRaises(IntegrityError):
            user2.save()


    def test_User_Password(self):
        user_email = fake.free_email()
        user_password = fake.password()
        user = User()
        user.email = user_email
        user.encrypt_password(user_password)
        user.generate_UUID()
        user.save()
        self.assertTrue(user.verify_password(user_password))

    def test_User_BlankPassword(self):
        user_email = fake.free_email()
        user_password = fake.password()
        user = User()
        user.email = user_email
        user.generate_UUID()
        user.save()
        with self.assertRaises(TypeError):
            user.verify_password(user_password)


    def test_User_BadPassword(self):
        user_email = fake.free_email()
        user_password = fake.password()
        user_BADpassword = fake.password()
        user = User()
        user.email = user_email
        user.encrypt_password(user_password)
        user.generate_UUID()
        user.save()
        self.assertFalse(user.verify_password(user_BADpassword))


#if __name__ == '__main__':
#    unittest.main()
