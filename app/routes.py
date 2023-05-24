import os
import requests
from flask import request, render_template, url_for, redirect, session, make_response
from . import app, db, bcrypt, \
    github_id, github_secret, vk_id, vk_secret, mail, gmail_address
from .models import Ad, BoughtAd, LikedAd, User, Photo
from .forms import *
from .utils import generate_link, get_token_by_code, get_user_info
from werkzeug.utils import secure_filename
from flask_mail import Message
from uuid import uuid4
from .api import api_users_get, api_ads_get

url_redirect_vk = "http://127.0.0.1:5000/vk_complete"
url_redirect_github = "http://127.0.0.1:5000/github_complete"


@app.route('/login_via_oauth/<string:app>')
def login_via_oauth(app):
    """
    Redirects the user to the OAuth provider for authentication.

    Args:
        app (str): The OAuth provider (either 'vk' or 'github').

    Returns:
        redirect: A redirect response to the OAuth provider's authentication page.
    """
    if app == 'vk':
        link = generate_link(url_redirect_vk, app, vk_id)
    else:
        link = generate_link(url_redirect_github, app, github_id)
    return redirect(link)


@app.route('/vk_complete')
def vk_auth():
    """
    Handles the completion of VK OAuth authentication.

    Retrieves the access token and user information from VK API, and saves it in the session.
    If the user is new, it creates a new User record in the database.

    Returns:
        redirect: A redirect response to the ads_view route.
    """
    code = request.args.get("code")
    token, email = get_token_by_code(code, url_redirect_vk, 'vk', vk_id, vk_secret)
    name, surname = get_user_info(token, 'vk')
    name = name + ' ' + surname
    if not User.query.filter(User.email == email).first():
        user = User(name=name, email=email, token=token)
        db.session.add(user)
        db.session.commit()
        res = make_response()
        res.set_cookie('mail', email, max_age=60 * 60 * 24 * 30)
    else:
        db.session.query(User).filter(User.email == email). \
            update(dict(token=token, name=name))
    session['uemail'] = email
    session['auth'] = True
    return redirect(url_for('ads_view'))


@app.route('/github_complete')  # TODO: поменять endpoint, email
def github_auth():
    """
    Handles the completion of GitHub OAuth authentication.

    Retrieves the access token and user information from GitHub API, and saves it in the session.
    If the user is new, it creates a new User record in the database.

    Returns:
        redirect: A redirect response to the ads_view route.
    """
    code = request.args.get("code")
    token = get_token_by_code(code, url_redirect_github, 'github', github_id, github_secret)
    name, email = get_user_info(token, 'github')
    if not User.query.filter(User.email == email).first():
        user = User(name=name, email=email, token=token)
        db.session.add(user)
        db.session.commit()
        res = make_response()
        res.set_cookie('mail', email, max_age=60 * 60 * 24 * 30)
    else:
        db.session.query(User).filter(User.email == email). \
            update(dict(token=token, name=name))
    session['uemail'] = email
    session['auth'] = True
    return redirect(url_for('ads_view'))


def is_login():
    return session.get('auth')


def safe_mode(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            pass

    return wrapper


@app.route("/logout", methods=['GET'])
def logout():
    """
       Logs out the user by clearing the session.

       Returns:
           redirect: A redirect response to the login route.
       """
    email = session['uemail']
    user = User.query.filter(User.email == email).first()
    token = user.token
    if token:
        url1 = f"https://api.github.com/authorizations/{token}"
        headers1 = {"Authorization": f"token {token}"}
        requests.delete(url1, headers=headers1)
        url2 = "https://oauth.vk.com/revoke_token"
        params2 = {"access_token": token}
        requests.get(url2, params=params2)
        db.session.query(User).filter(User.email == email). \
            update(dict(token=None))
    session['auth'] = None
    return redirect("/")


@app.route("/editprofile", methods=['GET', 'POST'])
def edit_profile():
    if is_login():
        email = session['uemail']
        old_user = User.query.filter(User.email == email).first()
        form = EditProfileForm(name=old_user.name, email=old_user.email)
        if form.validate_on_submit():
            new_name = form.name.data
            new_email = form.email.data
            new_pass = form.new_password1.data
            res = make_response()
            res.set_cookie('mail', new_email, max_age=60 * 60 * 24 * 30)
            pw_hash = bcrypt.generate_password_hash(new_pass)
            db.session.query(User).filter(User.email == email). \
                update(dict(name=new_name, email=new_email, password=pw_hash))
            session['uemail'] = new_email
            db.session.commit()
            return redirect(url_for('ads_view'))
        return render_template("editprofile.jinja2", form=form)
    return redirect(url_for('login'))


@app.route("/login", methods=['GET', "POST"])
def login():
    mail = ''
    form = LoginForm()
    if request.cookies.get('mail'):
        mail = request.cookies.get('mail')
    if form.validate_on_submit():
        email = form.email.data
        session['auth'] = True
        session['uemail'] = email
        return redirect(url_for('myads_view'))
    return render_template('login.jinja2', mail=mail, form=form)


@app.route("/registrate", methods=['GET', "POST"])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        password1 = form.password1.data
        res = make_response()
        res.set_cookie('mail', email, max_age=60 * 60 * 24 * 30)
        pw_hash = bcrypt.generate_password_hash(password1)
        user = User(email=email,
                    name=name,
                    password=pw_hash)
        db.session.add(user)
        db.session.commit()
        session['uemail'] = email
        session['auth'] = True
        return redirect(url_for('myads_view'))
    return render_template('registration.jinja2', form=form)


@app.route('/')
@app.route('/ads')
def ads_view():
    """
       Displays the list of ads.

       If the user is authenticated, it displays a list of ads from the API.
       Otherwise, it redirects the user to the login route.

       Returns:
           redirect or render_template: A redirect response to the login route if the user is not authenticated,
           or a template with the list of ads if the user is authenticated.
       """
    ads = db.session.query(Ad.id, Ad.category, Ad.name.label("an"), Ad.preordered, Ad.price, Photo.path,
                           User.name.label('un')). \
        join(Photo, Ad.id == Photo.ad_id). \
        join(User, User.id == Ad.creator_id). \
        filter(Ad.preordered == 0, Ad.bought == 0).all()
    return render_template("ads.jinja2", ads=ads)


@app.route("/myads", methods=['GET', 'POST'])
def myads_view():
    if not is_login():
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(User.email == uemail).first()
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Ad.preordered, Ad.price, Photo.path). \
        join(Photo, Ad.id == Photo.ad_id). \
        where(Ad.creator_id == user.id).all()
    return render_template("myads.jinja2", ads=ads, user=user)


@app.route("/boughtads", methods=['GET', 'POST'])
def boughtads_view():
    if not is_login():
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(User.email == uemail).first()
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Photo.path). \
        join(BoughtAd, Ad.id == BoughtAd.ad_id). \
        join(Photo, Ad.id == Photo.ad_id).where(BoughtAd.user_id == user.id).all()
    return render_template("boughtads.jinja2", ads=ads)


@app.route("/likedads", methods=['GET', 'POST'])
def likedads_view():
    if not is_login():
        redirect(url_for('login'))
    email = session['uemail']
    user = User.query.filter(User.email == email).first()
    ads = db.session.query(Ad.id, Ad.category, Ad.name.label('an'), Ad.price, User.name.label('un'), Photo.path). \
        join(LikedAd, Ad.id == LikedAd.ad_id). \
        join(Photo, Ad.id == Photo.ad_id). \
        join(User, LikedAd.user_id == User.id). \
        where(LikedAd.user_id == user.id).all()
    print(ads, LikedAd.query.all(), user.id)
    return render_template("likedads.jinja2", ads=ads)


@app.route("/ad/<int:ad_id>/like", methods=['POST', 'GET'])
def ad_like(ad_id):
    if is_login():
        ad = Ad.query.filter(Ad.id == ad_id).first()
        user = User.query.filter(User.email == session['uemail']).first()
        if user.id != ad.creator_id:
            liked_ad = LikedAd.query.filter(LikedAd.ad_id == ad_id, LikedAd.user_id == user.id).first()
            if not liked_ad:
                liked_ad = LikedAd(ad_id=ad_id, user_id=user.id)
                db.session.add(liked_ad)
            else:
                db.session.delete(liked_ad)
            db.session.commit()
        return redirect(url_for('detail_view', ad_id=ad_id))
    return redirect(url_for('login'))


@app.route("/ad/create", methods=['GET', 'POST'])
def ad_create():
    """
        Handles the creation of a new ad.

        If the request method is GET, renders the ad creation form.
        If the request method is POST, validates and saves the submitted form data as a new Ad record in the database.

        Returns:
            redirect or render_template: A redirect response to the ads_view route or a rendered template for the ad creation form.
        """
    if not is_login():
        return redirect(url_for('login'))
    form = AdCreateForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = int(form.price.data)
        category = form.category.data
        user = User.query.filter(User.email == session['uemail']).first()
        creator_id = user.id
        ad = Ad(name=name, creator_id=creator_id, description=description, price=price, category=category)
        db.session.add(ad)
        db.session.commit()
        file = form.file_upload
        try:
            filename = secure_filename(file.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.data.save(filepath)
            image_path = f'{filepath}'[3::]
        except:
            image_path = '/static/imgs/1.jpg'
        photo = Photo(ad_id=ad.id, path=image_path)
        db.session.add(photo)
        db.session.commit()
        return redirect(url_for('myads_view'))
    return render_template('create.jinja2', form=form)


@app.route("/ad/<int:ad_id>/", methods=['GET', 'POST'])
def detail_view(ad_id):
    ad = db.session.query(Ad.id, Ad.creator_id, Ad.name, Ad.uploaded, Ad.price, Ad.category, Ad.preordered,
                          Ad.description, Photo.path) \
        .join(Photo, Ad.id == Photo.ad_id).filter(Ad.id == ad_id).first()
    user = User.query.filter(User.email == session['uemail']).first()
    if ad is None:
        return render_template('404.jinja2')
    return render_template('detail.jinja2', ad=ad, user=user)


@app.route("/ad/<int:ad_id>/edit", methods=['GET', 'POST'])
def ad_edit(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = db.session.query(Ad.id, Ad.creator_id, Ad.name, Ad.price, Ad.category, Ad.preordered, Ad.description,
                              Photo.path) \
            .join(Photo, Ad.id == Photo.ad_id).filter(Ad.id == ad_id).first()
        if user.id == ad.creator_id:
            form = AdEditForm(
                name=ad.name, description=ad.description, category=ad.category, price=ad.price, upload_file=ad.path)
            if form.validate_on_submit():
                name = form.name.data
                description = form.description.data
                price = int(form.price.data)
                category = form.category.data
                file = form.file_upload
                db.session.query(Ad).filter(Ad.id == ad_id). \
                    update(dict(name=name, description=description, price=price, category=category))
                try:
                    filename = file.data.filename  # secure_filename(file.data.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.data.save(filepath)
                    image_path = f'{filepath}'[3::]
                except:
                    image_path = 'static/imgs/1.jpg'
                db.session.query(Photo).filter(Photo.ad_id == ad_id). \
                    update(dict(path=image_path))
                db.session.commit()
                return redirect(url_for('ads_view'))
            return render_template('edit.jinja2', ad=ad, form=form)
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/ad/<int:ad_id>/delete")
def ad_delete(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = Ad.query.filter(Ad.id == ad_id).first()
        photo = Photo.query.filter(Photo.ad_id == ad_id).first()
        if user.id == ad.creator_id:
            db.session.delete(photo)
            db.session.delete(ad)
            db.session.commit()
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/addmoney", methods=['POST', 'GET'])
def add_money():
    if not is_login():
        return redirect(url_for('login'))
    form = MoneyAddForm()
    user = User.query.filter(User.email == session['uemail']).first()
    return render_template('addmoney.jinja2', form=form, user=user)


@app.route("/ad/<int:ad_id>/buy", methods=['POST', 'GET'])
def ad_buy(ad_id):
    if not is_login():
        return redirect(url_for('login'))
    ad = Ad.query.filter(Ad.id == ad_id).first()
    user = User.query.filter(User.email == session['uemail']).first()
    if user.id != ad.creator_id:
        if user.balance >= ad.price and not ad.bought:
            new_b = user.balance - ad.price
            bought_ad = BoughtAd(ad_id=ad.id, user_id=user.id)
            db.session.query(User).filter(User.id == user.id). \
                update(dict(balance=new_b))
            db.session.query(Ad).filter(Ad.id == ad_id). \
                update(dict(bought=1))
            db.session.add(bought_ad)
            db.session.commit()
            return redirect(url_for('boughtads_view'))
        return redirect(url_for('add_money'))
    return redirect(url_for('ads_view'))


@app.route("/ad/<int:ad_id>/preorder", methods=['POST', 'GET'])
def ad_preorder(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = Ad.query.filter(Ad.id == ad_id).first()
        if user.id != ad.creator_id and not ad.preordered:
            db.session.query(Ad).filter(Ad.id == ad_id). \
                update(dict(preordered=1))
            db.session().commit()
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/ad/<int:ad_id>/cancelpreorder", methods=['POST', 'GET'])
def cancel_preorder(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = Ad.query.filter(Ad.id == ad_id).first()
        if user.id == ad.creator_id and ad.preordered:
            db.session.query(Ad).filter(Ad.id == ad_id). \
                update(dict(preordered=0))
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/reset_password", methods=['POST', 'GET'])
def reset_password_start():
    if is_login():
        return redirect(url_for('myads_view'))
    form = ResetPasswordForm1()
    if form.validate_on_submit():
        email = form.email.data
        token = str(uuid4())
        session['reset_token'] = token
        session['reset_email'] = email
        msg = Message('Сброс пароля', sender=gmail_address,recipients=[email])
        msg.html = render_template('email_for_reset.jinja2', token=token)
        mail.send(msg)
        return redirect(url_for('login'))
    return render_template('resetpassword.jinja2', form=form)


@app.route("/reset_password_complete", methods=['POST', 'GET'])
def reset_password_complete():
    if is_login():
        return redirect(url_for('myads_view'))
    if session['reset_token'] == request.args.get('token'):
        form = ResetPasswordForm2()
        if form.validate_on_submit():
            password = bcrypt.generate_password_hash(form.password1.data)
            email = session['reset_email']
            db.session.query(User).filter(User.email == email). \
                update(dict(password=password))
            db.session.commit()
    else:
        return redirect(url_for('signup'))
    return render_template('completereset.jinja2', form=form)
