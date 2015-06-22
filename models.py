import datetime
from flask.ext.mongoengine import MongoEngine
import io
import json
import jwt
from mongoengine.errors import NotUniqueError, DoesNotExist
import os
from passlib.hash import bcrypt
import shortuuid
from werkzeug import secure_filename

from helpers import logger
import helpers

db = MongoEngine()

FILE_SYSTEM_ABSOLUTE_PATH = ""

class User(db.Document):
    active = db.BooleanField(default=True)
    email = db.StringField(max_length=255, required=True, unique=True)
    email_confirmed = db.BooleanField(default=False)
    join_date = db.DateTimeField(default=datetime.datetime.now, required=True)
    password = db.StringField(max_length=255, required=True)
    stripe_customer_id = db.StringField(max_length=150)
    suspended = db.BooleanField(default=False)
    uuid = db.StringField(max_length=22, required=True, unique=True)
    public_info = db.DictField()

    @staticmethod
    def create_user(email, password):
        user = User()
        user.email = email
        user.password = bcrypt.encrypt(password)
        user.uuid = shortuuid.ShortUUID().random()
        user.save()
        return user

    @staticmethod
    def authenticate(email, password):
        user = User.objects.get(email=email)
        if user.verify_password(password):
            return user
        else:
            return None

    @staticmethod
    def redeem_jwt(token, salt):
        try:
            payload = jwt.decode(token, salt)
        except jwt.ExpiredSignatureError:
            logger.error('jwt.ExpiredSignatureError :' + token)
            return None
        except jwt.exceptions.DecodeError:
            logger.error('jwt.DecodeError:' + token)
            return None
        try:
            user = User.objects.get(uuid=payload['uuid'])
            return user
        except DoesNotExist:
            return None

    def issue_jwt(self, salt, expire_time):
        expire_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expire_time)
        payload = {}
        payload['uuid'] = self.uuid
        payload['exp'] = expire_time
        token = jwt.encode(payload, salt, algorithm='HS512')
        return token

    def hash_password(self, password):
        self.password = bcrypt.encrypt(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def reauthenticate(self, email, password):
        if email == self.email and self.verify_password(password):
            return True
        else:
            return False


class Site(db.Document):
    create_date = db.DateTimeField(default=datetime.datetime.now, required=True)
    expired = db.BooleanField(default=False)
    domain_name = db.StringField(max_length=255, unique=True)
    members = db.ListField(db.ReferenceField(User))
    owner = db.ReferenceField(User)
    subdomain = db.StringField(max_length=255)
    suspended = db.BooleanField(default=False)
    title = db.StringField(max_length=255, required=True)
    uuid = db.StringField(max_length=22, required=True)

    @staticmethod
    def create_site(subdomain, domain_name, user, title):
        site = Site()
        site.subdomain = subdomain
        site.domain_name = secure_filename(domain_name)
        site.owner = user
        site.title = title
        site.uuid = shortuuid.ShortUUID().random()
        site.save()
        site.add_member(user)
        site.save()
        site.make_site_directories()
        return site

    @staticmethod
    def get_by_uuid(uuid):
        site = Site.objects.get(uuid=uuid)
        return site

    @staticmethod
    def get_sites_where_user_is_member(user):
        sites = Site.objects(members=user)
        return sites

    def get_site_directory(self):
        return os.path.join(FILE_SYSTEM_ABSOLUTE_PATH, "site", self.uuid)

    def get_backup_directory(self):
        return os.path.join(FILE_SYSTEM_ABSOLUTE_PATH, "backup", "sites", self.uuid)

    def get_www_directory(self):
        return os.path.join(FILE_SYSTEM_ABSOLUTE_PATH, "www", self.domain_name)

    def make_site_directories(self):
        backup_directory = self.get_backup_directory()
        helpers.make_directory(backup_directory)

        main_directory = self.get_site_directory()
        helpers.make_directory(main_directory)

        json_directory = os.path.join(main_directory, "json")
        helpers.make_directory(json_directory)

        image_directory = os.path.join(main_directory, "image")
        helpers.make_directory(image_directory)

        podcast_directory = os.path.join(main_directory, "podcast")
        helpers.make_directory(podcast_directory)

        www_directory = self.get_www_directory()
        os.symlink(main_directory, www_directory)


    def get_posts(self):
        posts = Post.objects(site=self).order_by('-published')
        return posts

    def check_membership(self, user):
        for member in self.members:
            if member.uuid == user.uuid:
                return True
        return False

    def add_member(self, user):
        self.update(add_to_set__members=[user])



class Post(db.Document):
    author = db.ReferenceField(User)
    body = db.StringField()
    description = db.StringField()
    draft = db.BooleanField(default=False)
    featured_image = db.StringField(max_length=255)
    published = db.DateTimeField(default=datetime.datetime.now, required=True)
    podcast_file = db.StringField(max_length=255)
    site = db.ReferenceField(Site)
    slug = db.StringField(max_length=255, unique=True, sparse=True)
    tags = db.ListField(db.StringField(max_length=255))
    title = db.StringField(max_length=255)
    uuid = db.StringField(max_length=22, required=True)

    @staticmethod
    def get_by_uuid(uuid):
        post = Post.objects.get(uuid=uuid)
        return post

    @staticmethod
    def create_post(site, user, body, description, tags, title):
        post = Post()
        post.author = user
        post.body = body
        post.description = description
        post.site = site
        post.slug = helpers.sluggy(title)
        post.tags = tags
        post.title = title
        post.uuid = shortuuid.ShortUUID().random()
        try:
            post.save()
            print post.get_json()
            post.write_to_disk()
            return post
        except NotUniqueError:
            duplicate_title_count = len(Post.objects(title=post.title))
            post.slug = post.slug+ "_" + str(duplicate_title_count) + shortuuid.ShortUUID().random(length=3)
            print post.slug
        post.save()
        return post

    def get_json(self):
        post_dict = {}
        post_dict['author'] = self.author.uuid
        post_dict['body'] = self.body
        post_dict['description'] = self.description
        post_dict['featured_image'] = self.featured_image
        post_dict['podcast_file'] = self.podcast_file
        post_dict['published'] = self.published.strftime('%s')
        post_dict['site'] = self.site.uuid
        post_dict['slug'] = self.slug
        post_dict['tags'] = self.tags
        post_dict['title'] = self.title
        post_dict['uuid'] = self.uuid
        return unicode(json.dumps(post_dict, ensure_ascii=False, indent=4, sort_keys=True))

    def get_json_location(self):
        file_name = self.slug + ".json"
        file_path = os.path.join(FILE_SYSTEM_ABSOLUTE_PATH, "site", self.site.uuid, "json", file_name)
        return file_path

    def write_to_disk(self):
        file_path = self.get_json_location()
        file_contents = self.get_json()
        f = open(file_path, 'w')
        f.write(file_contents.encode('utf8'))
        f.close()

    def delete_from_disk(self):
        file_path = self.get_json_location()
        try:
            os.remove(file_path)
        except OSError:
            logger.info('Post.delete_from_disk() failed for uuid: ' + self.uuid)


