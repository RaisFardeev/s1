from . import app, db
from flask import jsonify, request
from .models import User, Ad


@app.route("/api/v1/get_users")
def api_users_get():
    if email := request.args.get('email'):
        user = User.query.filter(User.email == email).first()
        if user:
            return jsonify(dict(email=user.email, name=user.name, balance=user.balance, status=200))
        return jsonify(dict(status=404))
    users = User.query.all()
    return jsonify(dict
                   (users=dict((f'user{u.name}', f'name:{u.name},email:{u.email},balance:{u.balance}') for u in users),
                    status=200))


@app.route("/api/v1/get_ads")
def api_ads_get():
    try:
        price_from = int(request.args.get('price_from'))
        price_to = int(request.args.get('price_to'))
    except TypeError:
        price_from, price_to = False, False
    if price_from and price_to:
        ads = db.session.query(Ad.id, Ad.category, Ad.name, Ad.price, User.email). \
            join(User, User.id == Ad.creator_id). \
            filter(Ad.preordered == 0, Ad.bought == 0, Ad.price >= price_from, Ad.price <= price_to).all()
        return jsonify(dict(
            ads=dict(
                (f'ad{a.name}', f'name:{a.name},creator_email:{a.email},category:{a.category}') for a in ads),
            status=200))
    ads = db.session.query(Ad.id, Ad.category, Ad.name, Ad.price, User.email). \
        join(User, User.id == Ad.creator_id). \
        filter(Ad.preordered == 0, Ad.bought == 0).all()
    return jsonify(dict(
        ads=dict(
            (f'ad{a.name}', f'name:{a.name},creator_email:{a.email},category:{a.category}') for a in ads),
        status=200))