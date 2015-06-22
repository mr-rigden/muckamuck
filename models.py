import datetime
from flask.ext.mongoengine import MongoEngine
from mongoengine import Q
import io
import jinja2
import json
import jwt
import math
from mongoengine.errors import NotUniqueError, DoesNotExist
import os
from passlib.hash import bcrypt
import shortuuid
from werkzeug import secure_filename

from helpers import logger
import helpers
from secret_config import FILE_SYSTEM_ABSOLUTE_PATH

db = MongoEngine()
template_env = jinja2.Environment(loader=jinja2.FileSystemLoader('site_templates'))


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
    description = db.StringField(default="")
    domain_name = db.StringField(max_length=255, unique=True)
    language = db.StringField(default="en-us")
    members = db.ListField(db.ReferenceField(User))
    owner = db.ReferenceField(User)
    site_css = db.StringField(default="")
    site_js = db.StringField(default="")
    site_template = db.StringField(default="")
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

    def get_json_directory(self):
        return os.path.join(self.get_site_directory(), "json")

    def get_json_post_directory(self):
        return os.path.join(self.get_json_directory(), "post")

    def get_json_tag_directory(self):
        return os.path.join(self.get_json_directory(), "tag")

    def get_json_pagination_directory(self):
        return os.path.join(self.get_json_directory(), "page")

    def get_index_path(self):
        site_root = self.get_site_directory()
        return os.path.join(site_root, "index.html")

    def make_site_directories(self):
        logger.info('Making Dirs for: ' + self.uuid)
        backup_directory = self.get_backup_directory()
        helpers.make_directory(backup_directory)

        main_directory = self.get_site_directory()
        helpers.make_directory(main_directory)

        helpers.make_directory(self.get_json_directory())
        helpers.make_directory(self.get_json_post_directory())
        helpers.make_directory(self.get_json_pagination_directory())
        helpers.make_directory(self.get_json_tag_directory())

        www_directory = self.get_www_directory()
        try:
            os.symlink(main_directory, www_directory)
        except OSError:
            logger.error('Symlink Already Exists For: ' + self.uuid)

    def write_robots_txt(self):
        robot_path = os.path.join(self.get_site_directory(), "robots.txt")
        template = template_env.get_template('robots.txt')
        robots_txt = template.render(site=self)
        f = open(robot_path, 'w')
        f.write(robots_txt.encode('utf8'))
        f.close()


    def generate_index(self):
        template = template_env.get_template('index.html')
        index_page = template.render()
        return unicode(index_page)

    def write_index_page(self):
        file_path = self.get_index_path()
        file_contents = self.generate_index()
        f = open(file_path, 'w')
        f.write(file_contents.encode('utf8'))
        f.close()

    def generate_sitemap(self):
        posts = Post.objects(site=self)
        template = template_env.get_template('sitemap.xml')
        xml_page = template.render(site=self, posts=posts)
        return unicode(xml_page)

    def write_sitemap(self):
        sitemape_path = os.path.join(self.get_www_directory(), "sitemap.xml")
        file_path = sitemape_path
        file_contents = self.generate_sitemap()
        f = open(file_path, 'w')
        f.write(file_contents.encode('utf8'))
        f.close()

    def generate_rss(self):
        posts = Post.objects(site=self).order_by('-published').limit(20)
        lastBuildDate = helpers.rss_datetime(datetime.datetime.now())
        for post in posts:
            post.rss_time = helpers.rss_datetime(post.published)
        template = template_env.get_template('rss.xml')
        xml_page = template.render(lastBuildDate=lastBuildDate, site=self, posts=posts)
        return unicode(xml_page)

    def write_rss(self):

        rss_path = os.path.join(self.get_www_directory(), "rss.xml")
        file_path = rss_path
        file_contents = self.generate_rss()
        f = open(file_path, 'w')
        f.write(file_contents.encode('utf8'))
        f.close()

    def generate_podcast_rss(self):
        template = template_env.get_template('podcast_rss.xml')
        xml_page = template.render()
        return unicode(xml_page)

    def write_podcst_rss(self):
        rss_path = os.path.join(self.get_www_directory(), "podcast_rss.xml")
        file_path = rss_path
        file_contents = self.generate_rss()
        f = open(file_path, 'w')
        f.write(file_contents.encode('utf8'))
        f.close()



    def write_css(self):
        css_path = os.path.join(self.get_www_directory(), "main.css")
        f = open(css_path, 'w')
        f.write(self.site_css.encode('utf8'))
        f.close()

    def write_js(self):
        js_path = os.path.join(self.get_www_directory(), "main.js")
        f = open(js_path, 'w')
        f.write(self.site_js.encode('utf8'))
        f.close()

    def write_template(self):
        template_path = os.path.join(self.get_www_directory(), "template.hbs")
        f = open(template_path, 'w')
        f.write(self.site_template.encode('utf8'))
        f.close()


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




    def write_paginations(self):
        fileList = os.listdir(self.get_json_pagination_directory())
        for eachFile in fileList:
            eachFile_path = os.path.join(self.get_json_pagination_directory(), eachFile)
            os.remove(eachFile_path)
        page_size = 15
        post_count = Post.objects(site=self).count()
        pages_needed = int(math.ceil(post_count/page_size))
        for page_number in range(pages_needed):
            page_file_name = str(page_number + 1) + ".json"
            page_dict = {}
            if page_number == 0:
                page_dict['previous'] = False
            else:
                page_dict['previous'] = True
            if (page_number + 1) < pages_needed:
                page_dict['next'] = True
            else:
                page_dict['next'] = False
            page_dict['page'] = page_number + 1
            page_dict['posts'] = []
            offset = page_number * page_size
            page = Post.objects(site=self).skip(offset).limit(page_size)
            for post in page:
                page_dict['posts'].append(post.get_summary_dict())
            page_json = unicode(json.dumps(page_dict, ensure_ascii=False, indent=4, sort_keys=True))
            page_json_path = os.path.join(self.get_json_pagination_directory(), page_file_name)
            file_path = page_json_path
            f = open(file_path, 'w')
            f.write(page_json.encode('utf8'))
            f.close()

    def write_tag_page(self, tag):
        if not tag:
            return
        tage_file_name = tag + ".json"
        tage_file_name = secure_filename(tage_file_name)
        tage_file_path = os.path.join(self.get_json_tag_directory(), tage_file_name)
        try:
            os.remove(tage_file_path)
        except OSError:
            logger.info('FAIL - write_tag_page delete": ' + tage_file_path)
        posts = Post.objects(Q(site=self) & Q(tags=tag))
        page_dict = {}
        page_dict['posts'] = []
        page_dict['tag'] =  tag
        for post in posts:
            page_dict['posts'].append(post.get_summary_dict())
        page_json = unicode(json.dumps(page_dict, ensure_ascii=False, indent=4, sort_keys=True))
        f = open(tage_file_path, 'w')
        f.write(page_json.encode('utf8'))
        f.close()



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
            return post
        except NotUniqueError:
            duplicate_title_count = len(Post.objects(title=post.title))
            post.slug = post.slug+ "_" + str(duplicate_title_count) + shortuuid.ShortUUID().random(length=3)
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

    def get_summary_dict(self):
        post_dict = {}
        post_dict['author'] = self.author.uuid
        post_dict['description'] = self.description
        post_dict['featured_image'] = self.featured_image
        post_dict['published'] = self.published.strftime('%s')
        post_dict['site'] = self.site.uuid
        post_dict['slug'] = self.slug
        post_dict['tags'] = self.tags
        post_dict['title'] = self.title
        post_dict['uuid'] = self.uuid
        return post_dict

    def get_json_location(self):
        file_name = self.slug + ".json"
        file_path = os.path.join(FILE_SYSTEM_ABSOLUTE_PATH, "site", self.site.uuid, "json", "post", file_name)
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


