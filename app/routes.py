import os
from flask import request, render_template, url_for, redirect, flash, session, make_response, jsonify, HttpResponse, send_from_directory
from . import app, db, bcrypt
from .models import *
from .forms import *
from sqlalchemy.exc import IntegrityError


def is_login():
    return session.get('auth')


@app.route('/')
def rdrct_on_ads_view():
    return redirect(url_for('ads_view'))


@app.route("/logout", methods=['GET'])
def logout():
    session['auth'] = None
    return redirect("/")


@app.route("/emailchange", methods=['GET', 'POST'])
def change_email():
    form = EditProfileForm()
    if form.validate_on_submit():
        users = User.query.conn.execute('select email from users').fetchall()
        email = session['uemail']
        new_email = foem.email.data
        if not (new_email in users):
            cur.execute("UPDATE users SET email = ?  WHERE email = ?", (new_email, email))
        return redirect(url_for('ads_view'))
    return render_template("changemail.jinja2")


@app.route("/login", methods=['GET', "POST"])
def login():
    mail = ''
    if request.cookies.get('mail'):
        mail = request.cookies.get('mail')
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter(email=email)
        if not user:
            flash('Ты не зарегистрирован')
        elif user and bcrypt.check_password_hash(user['password'], password):
            session['auth'] = True
            session['uemail'] = email
            return redirect(url_for('myads_view'))
    return render_template('login.jinja2', mail=mail)


@app.route("/registrate", methods=['GET', "POST"])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        password1 = form.password1.data
        password2 = form.password2.data
        user = User.query.filter(email=email)
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
    return render_template('registration.jinja2')


@app.route('/ads')
def ads_view():
    ads = #connection.execute('select ads.id as id,category,ads.price as price,ads.name as an,photo.path as p,users.name as un from ads '
          #                   'inner join photo on ads.id=photo.ad_id '
          #                   'inner join users on users.id=ads.creator_id '
          #                   'where ads.preordered=0 and ads.bought=0').fetchall()
    return render_template("ads.jinja2", ads=ads)


@app.route("/myads", methods=['GET', 'POST'])
def myads_view():
    if not session['auth']:
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(email=uemail)
    ads = connection.execute('select ads.id,category,name,preordered,price,category,path as p from ads '
                             'inner join photo on ads.id=photo.ad_id '
                             'where ads.creator_id = ?', (user['id'],)).fetchall()
    return render_template("myads.jinja2", ads=ads, user=user)


@app.route("/boughtads", methods=['GET', 'POST'])
def boughtads_view():
    if not session['auth']:
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User.query.filter(email=uemail)
    ads = connection.execute('select ads.id as id,category,ads.name as name,ads.category as c,photo.path as p from ads '
                             'inner join bought_ads on ads.id=bought_ads.ad_id '
                             'inner join photo on photo.ad_id=ads.id '
                             'where bought_ads.user_id=?', (user['id'],)).fetchall()
    return render_template("boughtads.jinja2", ads=ads)


@app.route("/likedads", methods=['GET', 'POST'])
def likedads_view():
    if not session['auth']:
        redirect(url_for('login'))
    uemail = session['uemail']
    user = User(email=uemail)
    ads = connection.execute('select ads.id as id,category,ads.name as an,price,users.name as un,path as p from ads '
                             'inner join liked_ads as l  on ads.id=l.ad_id '
                             'inner join photo on ads.id=photo.ad_id '
                             'inner join users on users.id=ads.creator_id '
                             'where l.user_id=?', (user['id'],)).fetchall()
    return render_template("likedads.jinja2", ads=ads)


@app.route("/ad/<int:ad_id>/like", methods=['POST', 'GET'])
def ad_like(ad_id):
    if session['auth']:
        ad = Ad.query.filter(id=ad_id)
        user = User.query.filter(email=session['uemail'])
        if user.id != ad.creator_id:
            if not LikedAd.query.filter(ad_id=ad_id, user_id=user.id):
                liked_ad = LikedAd(ad_id=ad_id, user_id=user.id)
                db.session.add(liked_ad)
                db.session.commit()
            return redirect(url_for('myads_view'))
        return redirect(url_for('detail_view', ad_id=ad_id))
    return redirect(url_for('login'))


@app.route("/ad/create", methods=['GET', 'POST'])
def ad_create():
    if not session['auth']:
        return redirect(url_for('login'))
    form = AdCreateForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = int(form.price.data)
        category = form.category.data #TODO: заменить на другие категории
        user = User.query.filter(email=session['uemail'])
        creator_id = user.id
        ad = Ad(name=name,creator_id=creator_id,description=description,price=price,category=category)
        db.session.add(ad)
        db.session.commit()
        file = form.file_upload.data
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            if filename.split('.')[-1] in ('jpg', 'png', 'gif', 'bmp'):
                image_path = f'{filepath}'
            else:
                image_path = 'uploads/1.jpg'
            photo=Photo(ad_id=ad.id,path=image_path)
            db.session.add(photo)
            db.sesion.commit()
        elif not file:
            image_path = 'uploads/1.jpg'
            photo = Photo(ad_id=ad.id, path=image_path)
            db.session.add(photo)
            db.sesion.commit()
        return redirect(url_for('myads_view'))
    return render_template('create.jinja2')


@app.route("/ad/<int:ad_id>/", methods=['GET', 'POST'])
def detail_view(ad_id):
    ad = connection.execute('SELECT * FROM ads '
                            'inner join photo on ads.id=photo.ad_id '
                            'where ads.id=?', (ad_id,)).fetchone()
    user = User.queru.filter(email=session['uemail'])
    if ad is None:
        return render_template('404.jinja2')
    return render_template('detail.jinja2', ad=ad, user=user)


@app.route("/ad/<int:ad_id>/edit", methods=['GET', 'POST'])
def ad_edit(ad_id):
    if session['auth']:
        user = User.query.filter(email=session['uemail'])
        ad = Ad.query.filter(id=ad_id)
        form = AdEditForm()
        if user.id == ad.creator_id:
            if form.validate_on_submit():
                name = form.name.data
                description = form.description.data
                price = int(form.price.data)
                category = form.category.data
                sql_command = 'UPDATE ads SET name = ?,description = ?,price = ?,category = ? WHERE id = ?'
                data = (name, description, price, category, ad_id)

                cur.execute(sql_command, data)
                return redirect(url_for('ads_view'))
            return render_template('edit.jinja2', ad=ad)
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/ad/<int:ad_id>/delete", methods=['POST', 'GET'])
def ad_delete(ad_id):
    if session['auth']:
        user = User.query.filter(email=session['uemail'])
        ad = Ad.query.filter(id=ad_id)
        if user.id == ad.creator_id:
            db.session.delete(ad)
            db.session.commit()
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/addmoney", methods=['POST', 'GET'])
def add_money():
    if not session['auth']:
        return redirect(url_for('login'))
    form = MoneyAddForm()
    user = User.query.filter(email=session['uemail'])
    if form.validate_on_submit():
        number = int(form.number.data)
        new_b = user.balance + number
        cur.execute('update users set balance=? where users.id=?', (new_b, user['id']))
        return render_template('addmoney.jinja2')
    return render_template('addmoney.jinja2')


@app.route("/ad/<int:ad_id>/buy", methods=['POST', 'GET'])
def ad_buy(ad_id):
    if not session['auth']:
        return redirect(url_for('login'))
    ad = Ad.query.filter(id=ad_id)
    user = User.query.filter(email=session['uemail'])
    if user['id'] != ad['creator_id']:
        if user['balance'] >= ad['price'] and not ad['bought']:
            new_b = user['balance'] - ad['price']
            insert('(ad_id,user_id)', (ad['id'], user['id']), 'bought_ads')
            connection = connect_to_db()
            cur = connection.cursor()
            cur.execute('update users set balance=? where id=?', (new_b, user['id']))
            cur.execute('update ads set bought=? WHERE id = ?', (1, ad_id,))
            connection.commit()
            connection.close()
            flash(f"{ad['name']} успешно куплен!")
            return redirect(url_for('boughtads_view'))
        flash('недостаточно денег')
        return redirect(url_for('add_many'))
    return redirect(url_for('ads_view'))


@app.route("/ad/<int:ad_id>/preorder", methods=['POST', 'GET'])
def ad_preorder(ad_id):
    if session['auth']:
        user = User.query.filter(email=session['uemail'])
        ad = Ad.query.filter(id=ad_id)
        if user.id != ad.creator_id and not ad.preordered:
            cur.execute('update ads set preordered=? WHERE id = ?', (1, ad_id,))
            flash(f"{ad.name} успешно предзаказан!")
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))


@app.route("/ad/<int:ad_id>/cancelpreorder", methods=['POST', 'GET'])
def cancel_preorder(ad_id):
    if session['auth']:
        user = User.query.filter(email=session['uemail'])
        ad = Ad.query.filter(id=ad_id)
        if user.id == ad.creator_id and ad.preordered:
            cur.execute('update ads set preordered=? WHERE id = ?', (0, ad_id,))
            flash(f"{ad.name} предзаказ отменен!")
            return redirect(url_for('myads_view'))
        return redirect(url_for('ads_view'))
    return redirect(url_for('login'))

#@app.route('/')
#def index():
#    objects = Something.query.all()
#    # order_by(Something.created_at.desc())
#    # paginate(page=???, per_page=???)
#    return render_template('index.html', objects=objects)
#
#
#@app.route('/<int:sid>/')
#def get_something(sid):
#    smth = Something.query.get_or_404(sid)
#    return render_template('something.html', object=smth)
#
#
#@app.route('/top/')
#def top():
#    rating = request.args.get('rating', 0, type=int)
#    print(rating)
#    somethings = Something.query.filter(Something.rating > rating)
#    return render_template('top.html', objects=somethings)
#
#
#@app.route('/create', methods=['GET', 'POST'])
#def create():
#    form = SomethingForm()
#
#    if form.validate_on_submit():
#        name = form.name.data
#        rating = form.rating.data
#        print(type(rating))
#
#        smth = Something(name=name, rating=rating)
#        db.session.add(smth)
#        db.session.commit()
#
#        return redirect(url_for('index'))
#    print(form._csrf)
#    return render_template('create.html', form=form)
#
#
#@app.route('/<int:sid>/edit/', methods=['GET', 'POST'])
#def edit(sid):
#    something = Something.query.get_or_404(sid)
#    form = UpdateSomething()
#
#    if form.validate_on_submit():
#        something.rating = int(form.rating.data)
#        try:
#            db.session.commit()
#            return redirect(url_for('index'))
#        except IntegrityError:
#            db.session.rollback()
#            flash('Произошла ошибка: такой объект уже есть в базе', 'error')
#            return render_template('edit.html', form=form)
#
#    elif request.method == 'GET':
#        form.rating.data = something.rating
#
#    return render_template('edit.html', form=form)