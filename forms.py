from flask_wtf import Form
from wtforms import PasswordField, StringField, TextField
from wtforms import validators

import helpers

def validate_domain_name(form, field):
    domain_name = helpers.reformat_domain_name(field.data)

class NewSiteForm(Form):
    site_title = StringField('site_title', validators=[validators.DataRequired()])
    site_subdomain = StringField('site_subdomain', validators=[validators.DataRequired()])
    site_email = StringField('site_email', validators=[validators.DataRequired(), validators.Email()])
    site_password = PasswordField('site_password', validators=[validators.DataRequired()])

class EmailWithPasswordForm(Form):
    email = StringField('email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired()])

class EmailForm(Form):
    email = TextField('Email', validators=[validators.DataRequired(), validators.Email()])

class SiteInfoForm(Form):
    site_title = StringField('site_title', validators=[validators.DataRequired()])

class PostForm(Form):
    post_body = StringField('post_body')
    post_description = StringField('post_description', validators=[validators.DataRequired()])
    post_featured_image = StringField('post_featured_image')
    post_tags = StringField('post_tags')
    post_title = StringField('post_title', validators=[validators.DataRequired()])

