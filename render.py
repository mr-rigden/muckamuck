# -*- coding: utf-8 -*-
import datetime
from email import utils
import jinja2
import logging
import logging.handlers
import math
import os
import shutil
import time
import unittest

import config
import models

from jinja2.sandbox import SandboxedEnvironment


render_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('render_templates'))

sandbox_env = SandboxedEnvironment()


###################################################
#
# Logging Boilerplate
####################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)15s - %(levelname)s - %(message)s')
console_handle = logging.StreamHandler()
console_handle.setFormatter(formatter)
logger.addHandler(console_handle)
LOG_FILENAME = "muchamuck_render.log"
file_handle = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handle = logging.FileHandler('muchamuck_render.log')
file_handle.setFormatter(formatter)
logger.addHandler(file_handle)
#logger.info('log message')

####################################################
# Render Setup
####################################################
MUCKAMUCK_SITES = os.path.join(config.MUCKAMUCK_DISK, "sites")
MUCKAMUCK_SITES_BY_UUID_PATH = os.path.join(MUCKAMUCK_SITES, "uuid")
MUCKAMUCK_SITES_BY_DOMAIN_PATH = os.path.join(MUCKAMUCK_SITES, "domain")

####################################################
# General Helpers
####################################################


def rss_datetime(time_stamp):
    time_stamp_tuple = time_stamp.timetuple()
    timestamp = time.mktime(time_stamp_tuple)
    time_string = utils.formatdate(timestamp)
    return time_string


def get_site_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid)


def get_site_domain_symlink_path(domain):
    return os.path.join(MUCKAMUCK_SITES_BY_DOMAIN_PATH, domain)

def get_site_post_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "post")


def get_site_pagination_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "paginate")


def get_site_podcast_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "podcast")


def get_site_img_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "img")


def get_site_rss_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "rss.xml")


def get_site_sitemap_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "sitemap.xml")


def get_site_index_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "index.html")


def get_site_users_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "user")


def get_site_user_path(site_uuid, user_uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, site_uuid, "user", user_uuid)


def get_site_tags_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "tag")


def get_site_tag_path(uuid, tag):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "tag", tag)


def get_site_archive_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "archive")


def get_post_path(site_uuid, post_slug):
    return os.path.join(get_site_post_path(site_uuid), post_slug + ".html")


def get_site_robots_txt_path(uuid):
    return os.path.join(MUCKAMUCK_SITES_BY_UUID_PATH, uuid, "robots.txt")


def politely_make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def build_render_workspace():
    politely_make_dir(MUCKAMUCK_SITES)
    politely_make_dir(MUCKAMUCK_SITES_BY_UUID_PATH)
    politely_make_dir(MUCKAMUCK_SITES_BY_DOMAIN_PATH)


def clear_render_workspace():
    shutil.rmtree(MUCKAMUCK_SITES)

####################################################
# Archive
####################################################


def generate_archives(uuid):
    delete_archives(uuid)
    dir_path = get_site_archive_path(uuid)
    politely_make_dir(dir_path)
    title = "Archive"
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    template = models.Theme.select().where(models.Theme.site == site).get().template
    post_count = models.Post.select().where(models.Post.site == site).count()
    page_count = int(math.ceil(float(post_count) / config.PAGE_ITEM_LIMIT))
    for i in range(page_count):
        current_page = i + 1
        posts = models.Post.select().where(models.Post.site == site).order_by(models.Post.created_date.desc()).paginate(current_page, config.PAGE_ITEM_LIMIT)
        make_pagination(dir_path, current_page, page_count, posts, site, template, title)


def delete_archives(uuid):
    dir_path = get_site_archive_path(uuid)
    politely_make_dir(dir_path)
    shutil.rmtree(dir_path)

####################################################
# Index
####################################################


def generate_index(uuid):
    index_path = get_site_index_path(uuid)
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    template = models.Theme.select().where(
        models.Theme.site == site).get().template
    post_count = models.Post.select().count()
    page_count = int(math.ceil(float(post_count) / config.PAGE_ITEM_LIMIT))
    posts = models.Post.select().where(models.Post.site == site).order_by(
        models.Post.created_date.desc()).paginate(1, config.PAGE_ITEM_LIMIT)
    post_dicts = []
    for post in posts:
        post_dicts.append(post.to_dict())
    index_content = sandbox_env.from_string(template).render(
        site=site.to_dict(), posts=post_dicts, current_page=1, total_pages=page_count)
    file_object = open(index_path, "wb")
    file_object.write(index_content)
    file_object.close()

####################################################
# Posts
####################################################


def generate_post(uuid):
    logger.info("render.generate_post(" + uuid + ")")
    post_from_db = models.Post.select().where(models.Post.uuid == uuid).get()
    theme = models.Theme.select().where(
        models.Theme.site == post_from_db.site).get()
    template = jinja2.Template(theme.template)
    post = post_from_db.to_dict()
    site = post_from_db.site.to_dict()
    file_object = open(get_post_path(site['uuid'], post['slug']), "wb")
    file_object.write(template.render(site=site, post=post))
    file_object.close()


def delete_post(uuid):
    post = models.Post.select().where(models.Post.uuid == uuid).get()
    os.remove(get_post_path(post.site.uuid, post.slug))

####################################################
# Robots.txt
####################################################


def generate_robot_txt(uuid):
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    file_object = open(get_site_robots_txt_path(site.uuid), "wb")
    file_object.write("# www.robotstxt.org/\n")
    file_object.write("Sitemap: http://")
    file_object.write(site.domain)
    file_object.write("/sitemap.xml\n")
    file_object.write("# Allow crawling of all content\n")
    file_object.write("User-agent: *\n")
    file_object.write("Disallow:\n")
    file_object.close()

####################################################
# RSS
####################################################


def generate_site_rss_feed(uuid):
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    posts = models.Post.select().where(models.Post.site == site).order_by(
        models.Post.created_date.desc()).limit(config.RSS_ITEM_LIMIT)
    template = render_env.get_template('rss.xml')
    rss_content = template.render(
        rss_datetime=rss_datetime, site=site, posts=posts)
    file_object = open(get_site_rss_path(uuid), "wb")
    file_object.write(rss_content)
    file_object.close()

####################################################
# Site
####################################################


def initialize_site(uuid):
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    initialize_site_dirs(site.uuid)


def initialize_site_dirs(uuid):
    politely_make_dir(get_site_path(uuid))
    politely_make_dir(get_site_post_path(uuid))
    politely_make_dir(get_site_podcast_path(uuid))
    politely_make_dir(get_site_img_path(uuid))
    politely_make_dir(get_site_pagination_path(uuid))
    politely_make_dir(get_site_users_path(uuid))
    politely_make_dir(get_site_tags_path(uuid))
    politely_make_dir(get_site_archive_path(uuid))


def make_domain_symlink(uuid):
    logger.info('render.make_domain_symlink('+ uuid +')')
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    uuid_path = get_site_path(uuid)
    domain_symlink_path = os.path.join(MUCKAMUCK_SITES_BY_DOMAIN_PATH, site.domain)
    try:
        os.symlink(uuid_path, domain_symlink_path)
        logger.info('Created Symlink: ' + domain_symlink_path)
    except:
        logger.info('Could Not Create Symlink: ' + domain_symlink_path)

def remove_domain_symlink(uuid):
    logger.info('render.remove_domain_symlink('+ uuid +')')
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    domain_symlink_path = os.path.join(MUCKAMUCK_SITES_BY_DOMAIN_PATH, site.domain)
    try:
        os.unlink(domain_symlink_path)
        logger.info('Removed Symlink:' + domain_symlink_path)
    except:
        logger.info('Could Not Remove Symlink:' + domain_symlink_path)



####################################################
# Sitemap
####################################################


def generate_site_sitemap(uuid):
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    file_object = open(get_site_sitemap_path(uuid), "wb")
    file_object.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    file_object.write(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for post in models.Post.select().where(models.Post.site == site).order_by(models.Post.created_date.desc()):
        file_object.write('<url>\n')
        file_object.write(
            " <loc>http://" + site.domain + "/post/" + post.slug + ".html</loc>\n")
        file_object.write(
            " <lastmod>" + post.created_date.strftime('%Y-%m-%d') + "</lastmod>\n")
        file_object.write('</url>\n')
    file_object.write('</urlset>\n')
    file_object.close()

####################################################
# Tags
####################################################


def generate_tag_pages(uuid, tag):
    delete_tag_pages(uuid, tag)
    dir_path = get_site_tag_path(uuid, tag)
    politely_make_dir(dir_path)
    title = "Posts Tagged With " + tag
    site = models.Site.select().where(models.Site.uuid == uuid).get()
    template = models.Theme.select().where(
        models.Theme.site == site).get().template
    post_count = models.Post.select().where(
        (models.Post.site == site) & (models.Post.tags.contains(tag))).count()
    page_count = int(math.ceil(float(post_count) / config.PAGE_ITEM_LIMIT))
    for i in range(page_count):
        current_page = i + 1
        posts = models.Post.select().where((models.Post.site == site) & (models.Post.tags.contains(tag))
                                           ).order_by(models.Post.created_date.desc()).paginate(current_page, config.PAGE_ITEM_LIMIT)
        make_pagination(
            dir_path, current_page, page_count, posts, site, template, title)


def delete_tag_pages(uuid, tag):
    dir_path = get_site_tag_path(uuid, tag)
    politely_make_dir(dir_path)
    shutil.rmtree(dir_path)

####################################################
# Users
####################################################


def generate_user_pages(site_uuid, user_uuid):
    dir_path = get_site_user_path(site_uuid, user_uuid)
    politely_make_dir(dir_path)
    user = models.User.select().where(models.User.uuid == user_uuid).get()
    site = models.Site.select().where(models.Site.uuid == site_uuid).get()
    post_count = models.Post.select().where(
        (models.Post.site == site) & (models.Post.author == user)).count()
    page_count = int(math.ceil(float(post_count) / config.PAGE_ITEM_LIMIT))
    title = "Posts By " + user.public_name
    template = models.Theme.select().where(
        models.Theme.site == site).get().template
    for i in range(page_count):
        current_page = i + 1
        posts = models.Post.select().where((models.Post.site == site) & (models.Post.author == user)
                                           ).order_by(models.Post.created_date.desc()).paginate(current_page, config.PAGE_ITEM_LIMIT)
        make_pagination(
            dir_path, current_page, page_count, posts, site, template, title)


####################################################
# Pagination
####################################################
def make_pagination(dir_path, current_page, page_count, posts, site, template, title):
    file_name = os.path.join(dir_path, str(current_page) + ".html")
    post_dicts = []
    for post in posts:
        post_dicts.append(post.to_dict())
    page_content = sandbox_env.from_string(template).render(site=site.to_dict(
    ), posts=post_dicts, current_page=current_page, title=title, total_pages=page_count)
    file_object = open(file_name, "wb")
    file_object.write(page_content)
    file_object.close()
    if current_page == 1:
        file_name = os.path.join(dir_path, "index.html")
        file_object = open(file_name, "wb")
        file_object.write(page_content)
        file_object.close()

####################################################
# Tests
####################################################


def create_dummy_data():
    user = models.create_dummy_user()
    user.save()
    site = models.create_dummy_site(user)
    site.save()
    theme = models.create_dummy_theme(site)
    theme.save()
    posts = []
    for k in range(50):
        post = models.Post()
        post.dummy(site, user)
        post.save()
        posts.append(post)
    return user, site, posts


class RenderTest(unittest.TestCase):

    def setUp(self):
        models.reset_db()
        build_render_workspace()

    def tearDown(self):
        clear_render_workspace()

    ####################################################
    # Test Tests
    ####################################################
    def test_Test(self):
        self.assertTrue(True)

    ####################################################
    # Site Tests
    ####################################################
    def test_Site_Initialization(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        self.assertTrue(os.path.exists(get_site_path(site.uuid)))
        self.assertTrue(os.path.exists(get_site_post_path(site.uuid)))
        self.assertTrue(os.path.exists(get_site_podcast_path(site.uuid)))
        self.assertTrue(os.path.exists(get_site_img_path(site.uuid)))

    def test_Site_RSS(self):
        import feedparser
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_site_rss_feed(site.uuid)
        self.assertTrue(os.path.isfile(get_site_rss_path(site.uuid)))
        parsed_feed = feedparser.parse(get_site_rss_path(site.uuid))
        self.assertEqual(parsed_feed.feed.title, site.title)

    def test_Site_Sitemap(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_site_sitemap(site.uuid)
        self.assertTrue(os.path.isfile(get_site_sitemap_path(site.uuid)))

    def test_Post(self):
        user, site, posts = create_dummy_data()
        post = posts[0]
        initialize_site(site.uuid)
        generate_post(post.uuid)
        self.assertTrue(os.path.isfile(get_post_path(site.uuid, post.slug)))

    def test_Delete_Post(self):
        user, site, posts = create_dummy_data()
        post = posts[0]
        initialize_site(site.uuid)
        generate_post(post.uuid)
        self.assertTrue(os.path.isfile(get_post_path(site.uuid, post.slug)))
        delete_post(post.uuid)
        self.assertFalse(os.path.isfile(get_post_path(site.uuid, post.slug)))

    def test_Index(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_index(site.uuid)
        self.assertTrue(os.path.isfile(get_site_index_path(site.uuid)))

    def test_Archive(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_archives(site.uuid)
        page_two_path = os.path.join(
            get_site_archive_path(site.uuid), "2.html")
        self.assertTrue(os.path.isfile(page_two_path))

    def test_Delete_Archive(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_archives(site.uuid)
        page_two_path = os.path.join(
            get_site_archive_path(site.uuid), "2.html")
        self.assertTrue(os.path.isfile(page_two_path))
        delete_archives(site.uuid)
        self.assertFalse(os.path.isfile(page_two_path))

    def test_Site_User(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_user_pages(site.uuid, user.uuid)
        page_two_path = os.path.join(
            get_site_user_path(site.uuid, user.uuid), "2.html")
        self.assertTrue(os.path.isfile(page_two_path))

    def test_Site_Tag(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_tag_pages(site.uuid, "tag")
        page_two_path = os.path.join(
            get_site_tag_path(site.uuid, "tag"), "2.html")
        self.assertTrue(os.path.isfile(page_two_path))

    def test_Site_Delete_Tag(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_tag_pages(site.uuid, "tag")
        page_two_path = os.path.join(
            get_site_tag_path(site.uuid, "tag"), "2.html")
        self.assertTrue(os.path.isfile(page_two_path))
        delete_tag_pages(site.uuid, "tag")
        self.assertFalse(os.path.isfile(page_two_path))

    def test_Site_Robots_Txt(self):
        user, site, posts = create_dummy_data()
        initialize_site(site.uuid)
        generate_robot_txt(site.uuid)
        self.assertTrue(os.path.isfile(get_site_robots_txt_path(site.uuid)))

if __name__ == '__main__':
    unittest.main()
