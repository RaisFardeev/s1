import os
from flask import request, render_template, url_for, redirect, flash, session, make_response#, jsonify, HttpResponse, send_from_directory
from . import app, db, bcrypt
from .models import Ad, BoughtAd, LikedAd, User, Photo
from .forms import *
from werkzeug.utils import secure_filename


def is_login():
    return session.get('auth')


@app.route('/')
def rdrct_on_ads_view():
    return redirect(url_for('ads_view'))


@app.route("/logout", methods=['GET'])
def logout():
    session['auth'] = None
    return redirect("/")


@app.route("/editprofile", methods=['GET', 'POST'])
def edit_profile():
    if is_login():
        email = session['uemail']
        old_user = User.query.filter(User.email == email).first()
        form = EditProfileForm(name=old_user.name, email=old_user.email, old_password=old_user.password)
        if form.validate_on_submit():
            new_name = form.name.data
            new_email = form.email.data
            new_pass = form.new_password1.data
            res = make_response()
            res.set_cookie('mail', new_email, max_age=60 * 60 * 24 * 30)
            pw_hash = bcrypt.generate_password_hash(new_pass)
            User.update().where(User.email == email).values(name=new_name, email=new_email, password=pw_hash)
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
        res.set_cookie('mail', email, max_age=60*60*24*30)
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


@app.route('/ads')
def ads_view():
    ads = Ad.query.join(Photo, Ad.id == Photo.ad_id).\
        join(User, User.id == Ad.creator_id).\
        filter(not Ad.preordered, not Ad.bought).all()
    return render_template("ads.jinja2", ads=ads)


@app.route("/myads", methods=['GET', 'POST'])
def myads_view():
    if not is_login():
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(User.email == uemail).first()
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Ad.preordered, Ad.price, Photo.path).\
        join(Photo, Ad.id == Photo.ad_id).\
        where(Ad.creator_id == user.id).all()
    return render_template("myads.jinja2", ads=ads, user=user)


@app.route("/boughtads", methods=['GET', 'POST'])
def boughtads_view():
    if not is_login():
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(User.email == uemail).first()
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Photo.path).\
        join(BoughtAd, Ad.id == BoughtAd.ad_id).\
        join(Photo, Ad.id == Photo.ad_id).where(BoughtAd.user_id == user.id).all()
    return render_template("boughtads.jinja2", ads=ads)


@app.route("/likedads", methods=['GET', 'POST'])
def likedads_view():
    if not is_login():
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User(email=uemail)
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Ad.price, User.name, Photo.path).\
        join(LikedAd, Ad.id == LikedAd.ad_id).\
        join(Photo, Ad.id == Photo.ad_id).\
        join(User, Ad.creator_id == User.id).\
        where(LikedAd.user_id == user.id).all()
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
        if file:
            filename = secure_filename(file.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.data.save(filepath)
            image_path = f'{filepath}'
        else:
            image_path = 'static/imgs/1.jpg'
        photo = Photo(ad_id=ad.id, path=image_path)
        db.session.add(photo)
        db.sesion.commit()
        return redirect(url_for('myads_view'))
    return render_template('create.jinja2', form=form)


@app.route("/ad/<int:ad_id>/", methods=['GET', 'POST'])
def detail_view(ad_id):
    ad = db.session.query(Ad.id, Ad.name, Ad.price, Ad.category, Ad.preordered, Ad.description, Photo.path)\
        .join(Photo, Ad.id == Photo.ad_id).filter(Ad.id == ad_id).first()
    user = User.query.filter(User.email == session['uemail']).first()
    if ad is None:
        return render_template('404.jinja2')
    return render_template('detail.jinja2', ad=ad, user=user)


@app.route("/ad/<int:ad_id>/edit", methods=['GET', 'POST'])
def ad_edit(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = db.session.query(Ad.id, Ad.name, Ad.price, Ad.category, Ad.preordered, Ad.description, Photo.path)\
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
                Ad.update().where(Ad.id == ad_id). \
                    values(name=name, description=description, price=price, category=category)
                if file:
                    filename = secure_filename(file.data.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.data.save(filepath)
                    image_path = f'{filepath}'
                else:
                    image_path = 'static/imgs/1.jpg'
                Photo.update().where(Photo.ad_id == ad_id).values(path=image_path)
                db.session.commit()
                return redirect(url_for('ads_view'))
            return render_template('edit.jinja2', ad=ad, form=form)
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/ad/<int:ad_id>/delete", methods=['POST', 'GET'])
def ad_delete(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = Ad.query.filter(Ad.id == ad_id).first()
        if user.id == ad.creator_id:
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
    if form.validate_on_submit():
        number = int(form.number.data)
        new_b = user.balance + number
        User.update().where(User.id == user.id). \
            values(balance=new_b)
        db.session.commit()
        return render_template('addmoney.jinja2')
    return render_template('addmoney.jinja2', form=form)


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
            User.update().where(User.id == user.id).values(balance=new_b)
            Ad.update().where(User.id == ad_id).values(bought=1)
            db.session.add(bought_ad)
            db.session.commit()
            return redirect(url_for('boughtads_view'))
        return redirect(url_for('add_many'))
    return redirect(url_for('ads_view'))


@app.route("/ad/<int:ad_id>/preorder", methods=['POST', 'GET'])
def ad_preorder(ad_id):
    if is_login():
        user = User.query.filter(User.email == session['uemail']).first()
        ad = Ad.query.filter(Ad.id == ad_id).first()
        if user.id != ad.creator_id and not ad.preordered:
            Ad.update().where(Ad.id == ad_id).values(preordered=1)
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
            Ad.update().where(Ad.id == ad_id).values(preordered=0)
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))
