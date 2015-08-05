import os
from peewee import *
import shutil
import unittest


from models import db, create_dummy_user, fake, Site, User

####################################################
# Site Model
####################################################

####################################################
# User Model
####################################################
class  UserTest(unittest.TestCase):
    def setUp(self):
        db.connect()
        try:
            db.drop_tables([User,])
        except:
            pass
        db.create_tables([User,])

    def tearDown(self):
        pass

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

    def test_User_Json_File(self):
        user = create_dummy_user()
        user.save()
        user.write_json()
        json_path =  user.get_json_path()
        user.write_json()
        self.assertTrue(os.path.isfile(json_path))
        try:
            shutil.rmtree(user.get_user_dir_path())
        except:
            pass


if __name__ == '__main__':
    unittest.main()
