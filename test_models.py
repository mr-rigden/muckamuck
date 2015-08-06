import os
from peewee import *
import shutil
import unittest


from models import db, fake, logger, Site, User
from models import create_dummy_user, create_dummy_site




####################################################
# Utilities
####################################################


def prepDB():
  cleanDB()
  db.create_tables([Site, User])


def cleanDB():
  try:
    db.drop_tables([Site])
  except OperationalError:
    pass
    #logger.debug('Site table did non exists')
  try:
    db.drop_tables([User])
  except OperationalError:
    pass
    #logger.debug('User table did non exists')


####################################################
# Site Model
####################################################
class SiteTest(unittest.TestCase):

  def setUp(self):
    db.connect()
    prepDB()

  def tearDown(self):
    cleanDB()
    db.close()

  def test_Count_Sitess(self):
    for i in range(10):
      site = create_dummy_site()
      site.save()
      # print user.to_json()
    self.assertEqual(Site.select().count(), 10)

  def test_Create_Site(self):
    site = create_dummy_site()
    test_title = site.title
    site.save()
    site = Site.get(Site.title == test_title)
    self.assertEqual(site.uuid, site.uuid)

  def test_Site_Json_File(self):
    site = create_dummy_site()
    site.save()
    site.write_json()
    json_path = site.get_json_path()
    self.assertTrue(os.path.isfile(json_path))
    #shutil.rmtree(site.get_site_dir_path())


####################################################
# User Model
####################################################


class UserTest(unittest.TestCase):

  def setUp(self):
    db.connect()
    prepDB()

  def tearDown(self):
    cleanDB()
    db.close()

  def test_Count_Users(self):
    for i in range(10):
      user = create_dummy_user()
      user.save()
      # print user.to_json()
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

  def test_User_Json_File(self):
    user = create_dummy_user()
    user.save()
    user.write_json()
    json_path = user.get_json_path()
    user.write_json()
    self.assertTrue(os.path.isfile(json_path))
    shutil.rmtree(user.get_user_dir_path())


if __name__ == '__main__':
  unittest.main()
