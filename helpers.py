import logging
import logging.handlers
from slugify import slugify, Slugify
from urlparse import urlparse
from werkzeug import secure_filename


custom_slugify = Slugify(to_lower=True)

def sluggy(name):
    name = custom_slugify(name)
    name = secure_filename(name)
    return name

def parse_and_clean_tag(tags_string):
    tags = []
    temp_tags = tags_string.split(',')
    for tag in temp_tags:
        tag = tag.strip()
        tag = sluggy(tag)
        tags.append(tag)
    return tags



def reformat_domain_name(domain_name):
    if not domain_name.startswith("http"):
        logger.info('no http')
        domain_name = "http://" + domain_name
    parsed_domain_name = urlparse(domain_name)
    try:
        new_domain_name = secure_filename(parsed_domain_name.hostname)
    except AttributeError:
        new_domain_name = ""
    return new_domain_name


####################################################
#Logging Boilerplate
####################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handle = logging.StreamHandler()
console_handle.setFormatter(formatter)
logger.addHandler(console_handle)
LOG_FILENAME = "mowich.log"
file_handle = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5*1024*1024, backupCount=5)
file_handle = logging.FileHandler('mowich.log')
file_handle.setFormatter(formatter)
logger.addHandler(file_handle)
#logger.info('log message')