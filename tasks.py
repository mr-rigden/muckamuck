from celery import Celery
import jinja2

import secret_config
import models

from helpers import logger



models.db.connect(secret_config.MONGODB_NAME)


app = Celery('tasks', broker='redis://localhost:6379/0')


@app.task
def initialize_site(site_uuid):
    logger.info('TASK - initialize_site:' + site_uuid)
    site = models.Site.get_by_uuid(site_uuid)
    site.make_site_directories()
    site.write_robots_txt()
    write_template_files.delay(site_uuid)
    update_site.delay(site_uuid)



@app.task
def write_template_files(site_uuid):
    logger.info('TASK - write_template_files:' + site_uuid)
    site = models.Site.get_by_uuid(site_uuid)
    site.write_index_page()
    site.write_css()
    site.write_js()
    site.write_template()

@app.task
def update_site(site_uuid):
    logger.info('TASK - update_site:' + site_uuid)
    site = models.Site.get_by_uuid(site_uuid)
    site.write_rss()
    site.write_podcst_rss()
    site.write_sitemap()
    site.write_paginations()
    site.write_robots_txt()

@app.task
def update_site_tag(site_uuid, tag):
    logger.info('TASK - update_site_tag:' + site_uuid + "-" + tag)
    site = models.Site.get_by_uuid(site_uuid)
    site = site.write_tag_page(tag)



@app.task
def render_post(post_uuid):
    post = models.Post.get_by_uuid(post_uuid)
    post.write_to_disk()




@app.task
def hello():
    return 'hello world!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'