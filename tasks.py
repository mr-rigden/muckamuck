from celery import Celery
import logging
import logging.handlers
import os
import unittest


import models
import render


#/home/jason/Desktop/muckamuck_shit

####################################################
# Logging Boilerplate
####################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)15s - %(levelname)s - %(message)s')
console_handle = logging.StreamHandler()
console_handle.setFormatter(formatter)
logger.addHandler(console_handle)
LOG_FILENAME = "muchamuck_task.log"
file_handle = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handle = logging.FileHandler('muchamuck_task.log')
file_handle.setFormatter(formatter)
logger.addHandler(file_handle)
#logger.info('tasks.log message')


BROKER_URL = 'redis://localhost:6379/0'
app = Celery('tasks', broker=BROKER_URL)

####################################################
# Events
####################################################
@app.task
def new_post(uuid):
    models.db.connect()
    post = models.Post.select().where(models.Post.uuid == uuid).get()
    render_post.delay(uuid)
    update_site.delay(post.site.uuid)
    models.db.close()

@app.task
def new_site(uuid):
    models.db.connect()
    site = models.Site.select().where( models.Site.uuid == uuid).get()
    initialize_site(site.uuid)
    change_domain.delay(uuid, site.domain)
    models.db.close()

@app.task
def change_domain(uuid, new_domain):
    models.db.connect()
    site = models.Site.select().where( models.Site.uuid == uuid).get()
    old_domain = site.domain
    render.remove_domain_symlink(uuid)
    site.domain = new_domain
    site.save()
    render.make_domain_symlink(uuid)
    models.db.close()

####################################################
# Tasks
####################################################
@app.task
def render_test_task():
    print "render_test_task"

@app.task
def initialize_site(uuid):
    logger.info('tasks.initialize_site('+ uuid +')')
    models.db.connect()
    render.initialize_site(uuid)
    update_site.delay(uuid)
    render.generate_robot_txt(uuid)
    models.db.close()

@app.task
def update_site(uuid):
    logger.info('tasks.update_site('+ uuid +')')
    render_archive.delay(uuid)
    render_index.delay(uuid)
    render_rss.delay(uuid)
    render_sitemap.delay(uuid)

@app.task
def full_rerender(uuid):
    logger.info('tasks.full_rerender('+ uuid +')')
    update_site.delay(uuid)
    render_all_tags.delay(uuid)
    render_all_posts.delay(uuid)

@app.task
def render_all_posts(uuid):
    logger.info('tasks.render_all_posts('+ uuid +')')
    models.db.connect()
    site = models.Site.select().where( models.Site.uuid == uuid).get()
    for post in  models.Post.select().where(models.Post.site == site).iterator():
        render_post.delay(post.uuid)
    models.db.close()

@app.task
def render_post(uuid):
    logger.info('tasks.render_post('+ uuid +')')
    models.db.connect()
    render.generate_post(uuid)
    models.db.close()



@app.task
def render_all_tags(uuid):
    logger.info('tasks.render_all_tags('+ uuid +')')
    models.db.connect()
    tags = models.get_site_tags(uuid)
    for tag in tags:
        render_tag.delay(uuid, tag)
    models.db.close()


@app.task
def render_tag(uuid, tag):
    logger.info('tasks.render_tag('+ uuid + ',' + tag + ')')
    models.db.connect()
    generate_tag_pages(uuid, tag)
    models.db.close()


@app.task
def render_archive(uuid):
    logger.info('tasks.render_archive('+ uuid +')')
    models.db.connect()
    render.generate_archives(uuid)
    models.db.close()


@app.task
def render_index(uuid):
    logger.info('tasks.render_index('+ uuid +')')
    models.db.connect()
    render.generate_index(uuid)
    models.db.close()


@app.task
def render_rss(uuid):
    logger.info('tasks.render_rss('+ uuid +')')
    models.db.connect()
    render.generate_site_rss_feed(uuid)
    models.db.close()

@app.task
def render_sitemap(uuid):
    logger.info('tasks.render_sitemap('+ uuid +')')
    models.db.connect()
    render.generate_site_sitemap(uuid)
    models.db.close()


####################################################
# Tests
####################################################

def create_dummy_data():
    for i in range(5):
        user = models.create_dummy_user()
        user.save()
        for j in range(5):
            site = models.create_dummy_site(user)
            site.save()
            theme = models.create_dummy_theme(site)
            theme.save()
            posts = []
            for k in range(5):
                post = models.Post()
                post.dummy(site, user)
                post.save()
                posts.append(post)


class TasksTest(unittest.TestCase):

    def setUp(self):
        render.clear_render_workspace()
        app.conf.CELERY_ALWAYS_EAGER = True
        models.reset_db()
        render.build_render_workspace()
        create_dummy_data()

    def tearDown(self):
        models.reset_db()
        #render.clear_render_workspace()

    ####################################################
    # Test Tests
    ####################################################
    def test_Test(self):
        #render_test_task()
        self.assertTrue(True)

    def test_Site_Initialization(self):
        site = models.get_random_site()
        initialize_site.delay(site.uuid)
        self.assertTrue(os.path.isfile( render.get_site_robots_txt_path(site.uuid) ))
        self.assertTrue(os.path.isfile( render.get_site_rss_path(site.uuid) ))
        self.assertTrue(os.path.isfile( render.get_site_sitemap_path(site.uuid) ))
        self.assertTrue(os.path.isfile( render.get_site_index_path(site.uuid) ))

    def test_Site_Update(self):
        site = models.get_random_site()
        update_site.delay(site.uuid)
        self.assertTrue(os.path.isfile( render.get_site_rss_path(site.uuid) ))
        self.assertTrue(os.path.isfile( render.get_site_index_path(site.uuid) ))

    def test_Site_Full_Rerender(self):
        site = models.get_random_site()
        initialize_site(site.uuid)
        full_rerender.delay(site.uuid)
        self.assertTrue(os.path.isfile( render.get_site_index_path(site.uuid) ))
        post = models.get_random_post_from_site(site.uuid)
        post_path = render.get_post_path(site.uuid, post.slug)
        self.assertTrue(os.path.isfile( post_path ))

    def test_Site_New_Post_Event(self):
        site = models.get_random_site()
        initialize_site(site.uuid)
        post = models.get_random_post_from_site(site.uuid)
        new_post.delay(post.uuid)
        post_path = render.get_post_path(site.uuid, post.slug)
        self.assertTrue(os.path.isfile( post_path ))

    def test_Site_Change_Domain(self):
        site = models.get_random_site()
        initialize_site(site.uuid)
        domain_symlink_path = render.get_site_domain_symlink_path(site.domain)
        self.assertFalse( os.path.exists(domain_symlink_path ) )
        change_domain.delay(site.uuid, "nothing.net")
        new_domain_symlink_path = render.get_site_domain_symlink_path("nothing.net")
        self.assertTrue( os.path.exists(new_domain_symlink_path ) )
        another_new_domain_symlink_path = render.get_site_domain_symlink_path("more_nothing.net")
        change_domain.delay(site.uuid, "more_nothing.net")
        self.assertFalse( os.path.exists(new_domain_symlink_path ) )
        self.assertTrue( os.path.exists(another_new_domain_symlink_path ) )


for i in range(5):
    user = models.create_dummy_user()
    user.save()
    for j in range(5):
        site = models.create_dummy_site(user)
        site.save()
        theme = models.create_dummy_theme(site)
        theme.save()
        new_site.delay(site.uuid)
        posts = []
        for k in range(5):
            post = models.Post()
            post.dummy(site, user)
            post.save()
            new_post.delay(post.uuid)
            posts.append(post)

#if __name__ == '__main__':
#    unittest.main()
