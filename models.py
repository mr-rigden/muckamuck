import datetime
from flask.ext.mongoengine import MongoEngine
import jwt
from mongoengine.errors import NotUniqueError, DoesNotExist
from passlib.hash import bcrypt
import shortuuid

from helpers import logger

db = MongoEngine()


class User(db.Document):
    active = db.BooleanField(default=True)
    email = db.StringField(max_length=255, required=True, unique=True)
    email_confirmed = db.BooleanField(default=False)
    join_date = db.DateTimeField(default=datetime.datetime.now, required=True)
    password = db.StringField(max_length=255, required=True)
    stripe_customer_id = db.StringField(max_length=150)
    suspended = db.BooleanField(default=False)
    uuid = db.StringField(max_length=22, required=True, unique=True)


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
        site.domain_name = domain_name
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


    def check_membership(self, user):
        for member in self.members:
            if member.uuid == user.uuid:
                return True
        return False

    def add_member(self, user):
        self.update(add_to_set__members=[user,])


class Site(db.Document):
    create_date = db.DateTimeField(default=datetime.datetime.now, required=True)