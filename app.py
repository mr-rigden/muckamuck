from flask import Flask
from flask import Flask, abort, flash, make_response, render_template, request, redirect, url_for
from flask.ext.mongoengine import MongoEngine
from flask_mail import Mail
from functools import wraps
from mongoengine.errors import NotUniqueError, DoesNotExist
from werkzeug import secure_filename


import forms
import helpers
from helpers import logger, sluggy, reformat_domain_name
import models
from tasks import hello
logger.info('log message')
app = Flask(__name__, instance_relative_config=True)

hello.delay()
###################################################
#Load Configuration Files
###################################################
app.config.from_object('config')
app.config.from_object('secret_config')
#app.config.from_pyfile('secret_config.py')
    
###################################################
#File System Setup
###################################################
models.FILE_SYSTEM_ABSOLUTE_PATH = app.config["FILE_SYSTEM_ABSOLUTE_PATH"]

###################################################
#Activate Flask Extension
###################################################
models.db.init_app(app) 
mail = Mail(app)


###################################################
#Jinja Helpers
###################################################
@app.template_filter()
def datetimefilter(value, format='%Y/%m/%d %H:%M'):
    """convert a datetime to a different format."""
    return value.strftime(format)

app.jinja_env.filters['datetimefilter'] = datetimefilter


#################################################
#Sign Up
#################################################
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up_page():
    form = forms.EmailWithPasswordForm(request.form)
    if form.validate_on_submit():
        try:
            user = models.User.create_user(form.email.data, form.password.data)
            logger.info('Created New User for: ' + form.email.data)
            return user.uuid
        except NotUniqueError:
            flash('Email address is already in use')
    return render_template('sign_up.html', form=form)


#################################################
#Sign In
#################################################
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in_page():
    form = forms.EmailWithPasswordForm(request.form)
    if form.validate_on_submit():
        try:
            user =  models.User.authenticate(form.email.data, form.password.data)
        except DoesNotExist:
            flash('Email not in use')
            return render_template('sign_in.html', form=form)
        if user is None:
            flash('Password Incorrect')
        else:
            token = user.issue_jwt(app.config["JWT_SALT"] , app.config["JWT_EXPIRE_TIME"] )
            response = make_response(redirect('/dashboard'))
            response.set_cookie("mowich_token", token, httponly=True)
            return response
    return render_template('sign_in.html', form=form)


#################################################
#Authorization Decorators
#################################################
def ownership_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            site = models.Site.get_by_uuid(kwargs['uuid'])
        except DoesNotExist:
            abort(404)
        kwargs['site'] = site
        if site.owner.uuid == kwargs['user'].uuid:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('membership_failure_page'))
            return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("mowich_token")
        if token is None:
            return redirect(url_for('sign_in_page'))
        user = models.User.redeem_jwt(token, app.config["JWT_SALT"])
        if user is None:
            return redirect(url_for('sign_in_page'))
        kwargs['user'] = user
        kwargs['sites'] = models.Site.get_sites_where_user_is_member(user)
        return f(*args, **kwargs)
    return decorated_function

def site_membership_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            site = models.Site.get_by_uuid(kwargs['uuid'])
        except DoesNotExist:
            abort(404)
        kwargs['site'] = site
        if site.check_membership(kwargs['user']):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('membership_failure_page'))
            return f(*args, **kwargs)
    return decorated_function

#################################################
#Dashboard
#################################################

@app.route('/dashboard')
@login_required
def dashboard_page(user=None, sites=None):
    print user.email
    return render_template('dashboard_base.html', user=user, sites=sites)


#################################################
#Add Site
#################################################
@app.route('/add_site', methods=["GET", "POST"])
@login_required
def add_site_page(user=None, sites=None):
    if not user.stripe_customer_id:
        flash('Billing Information Required')
        #return redirect(url_for('billing_page_page'))
    form = forms.NewSiteForm(request.form)

    if form.site_subdomain.data:
        form.site_subdomain.data = sluggy(form.site_subdomain.data)

    if form.validate_on_submit():
        if not user.reauthenticate(form.site_email.data, form.site_password.data):
            flash("Reauthentication Failed")
            return render_template('add_site.html', user=user, sites=sites, form=form)
        domain_name = form.site_subdomain.data + ".mowich.net"
        try:
            site = models.Site.create_site( form.site_subdomain.data, domain_name, user, form.site_title.data)
        except NotUniqueError:
            flash("That Subdomain Is Already In Use")
            return redirect(url_for('add_site_page'))
        return redirect(url_for('site_page', uuid=site.uuid))
    return render_template('add_site.html', user=user, sites=sites, form=form)
        

#################################################
#Site Page
##############################################
@app.route('/site/<uuid>', methods=["GET", "POST"])
@login_required
@site_membership_required
def site_page(uuid, user=None, site=None, sites=None):
    posts = site.get_posts()
    return render_template('site_page.html', user=user, sites=sites, active_site=site, posts=posts)


#################################################
#Site Settings
#################################################

@app.route('/site/<uuid>/settings', methods=["GET", "POST"])
@login_required
@ownership_required
def site_settings_page(uuid, user=None, site=None, sites=None):
    if site is None:
        abort(404)
    return render_template('site_settings.html', user=user, sites=sites, active_site=site)


#################################################
#Site Settings
#################################################

@app.route('/site/<uuid>/settings/info', methods=["GET", "POST"])
@login_required
@ownership_required
def site_info_page(uuid, user=None, site=None, sites=None):
    if site is None:
        abort(404)
    form = forms.SiteInfoForm()
    if form.validate_on_submit():
        site.title = form.site_title.data
        site.save()
        return redirect(url_for('site_info_page', uuid=uuid))
    else:
        form.site_title.data = site.title
    return render_template('site_info.html', user=user, sites=sites, active_site=site, form=form)


#################################################
#Create Post 
#################################################
@app.route('/site/<uuid>/post', methods=["GET", "POST"])
@login_required
@site_membership_required
def new_post_page(uuid, user=None, site=None, sites=None):
    hello.delay()
    form = forms.PostForm()
    if form.validate_on_submit():
        tags = helpers.parse_and_clean_tag(form.post_tags.data)
        post = models.Post.create_post(site, user, form.post_body.data, form.post_description.data, tags, form.post_title.data)
        return redirect(url_for('site_page', uuid=uuid))
    return render_template('post.html', user=user, sites=sites, active_site=site, form=form)

#################################################
#Edit Post 
#################################################
@app.route('/site/<uuid>/post/<post_uuid>', methods=["GET", "POST"])
@login_required
@site_membership_required
def edit_post_page(uuid, post_uuid, user=None, site=None, sites=None):
    form = forms.PostForm()
    try:
        post = models.Post.get_by_uuid(post_uuid)
    except DoesNotExist:
            abort(404)
    if request.method == 'POST':
        if request.form['btn'] ==  'delete_post':
            post.delete_from_disk()
            post.delete()
            return redirect(url_for('site_page', uuid=uuid))
    if form.validate_on_submit():
        post.body = form.post_body.data
        post.description = form.post_description.data
        post.tags = helpers.parse_and_clean_tag(form.post_tags.data)
        post.title = form.post_title.data
        post.save()
        post.write_to_disk()
        return redirect(url_for('site_page', uuid=uuid))
    else:
        form.post_body.data = post.body
        form.post_description.data = post.description
        form.post_tags.data = ", ".join(post.tags)
        form.post_title.data = post.title
    return render_template('post.html', user=user, sites=sites, active_site=site, post=post, form=form, author=post.author)




###################################################
###################################################
if __name__ == '__main__':
    app.run()
###################################################
###################################################

