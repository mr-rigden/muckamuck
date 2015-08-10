import faker
import json
import logging
import logging.handlers
import os
import shortuuid



####################################################
# Logging
####################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)15s - %(levelname)s - %(message)s')
console_handle = logging.StreamHandler()
console_handle.setFormatter(formatter)
logger.addHandler(console_handle)
LOG_FILENAME = "muchamuck.log"
file_handle = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handle = logging.FileHandler('muchamuck.log')
file_handle.setFormatter(formatter)
logger.addHandler(file_handle)
#logger.info('log message')


####################################################
# System Paths
####################################################
def get_output_root_path():
    output_root_path = os.environ['MUCKAMUCK_OUTPUT_DIRECTORY']
    return output_root_path

def get_output_json_path():
    output_json_path = os.path.join(get_output_root_path(), "json")
    return output_json_path



####################################################
# Misc
####################################################
fake = faker.Factory.create()
"""Initialize a faker generator.

This provides all the fake data using in the create dummy functions
"""

def generate_UUID():
    """Generats Shortish UUID.

    Returns:
        uuid string

    """
    return shortuuid.ShortUUID().random()

def jsonifyer(someDict):
    """Provides standardization of pretty json

    Args:
        someDict (dict): Any JSON compatible dictionary

    Returns:
        JSON string

    """
    return json.dumps(someDict, sort_keys=True, indent=4, separators=(',', ': '))

def make_dir(directory):
  """Nicely make directories.

  Checks to see if directory exits before creating

  """
  if not os.path.exists(directory):
    os.makedirs(directory)
