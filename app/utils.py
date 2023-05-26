import requests
from flask import Flask, redirect, request
from flask_sqlalchemy import SQLAlchemy
from .models import Ad, User, Photo
from . import bcrypt


def fill_database(app: Flask, db: SQLAlchemy):
    with app.app_context():
        try:
            password = bcrypt.generate_password_hash('password')
            u = User(name='User1', email='user31@mail.ru', password=password)
            db.session.add(u)
            db.session.commit()
            u_id = db.session.query(User.id).where(User.name == 'User1').first().id
            for i in range(1, 10):
                ad = Ad(creator_id=u_id, name=f'Ad{i}', description=f'description{i}', price=i)
                db.session.add(ad)
                db.session.commit()
                ad_id = db.session.query(Ad.id).where(Ad.name == ad.name).first().id
                photo = Photo(ad_id=ad.id, path='static/imgs/1.jpg')
                db.session.add(photo)
                db.session.commit()
            db.session.commit()
        except Exception as e:
            print(e)


def generate_link(url_redirect, app, id):
    if app == 'github':
        params = dict(client_id=id,  # the client ID you received from GitHub when you registered
                      redirect_uri=url_redirect,  # the URL in your application where users will be sent after authorization
                      scope="user",  # type of access
                      response_type="code")  # request the code
        endpoint = "https://github.com/login/oauth/authorize"
        response = requests.get(endpoint, params=params)
        return response.url
    elif app == 'vk':
        params = dict(client_id=id,  # the client ID you received from GitHub when you registered
                      redirect_uri=url_redirect,
                      # the URL in your application where users will be sent after authorization
                      scope="email",  # type of access
                      response_type="code")  # request the code
        endpoint = "https://oauth.vk.com/authorize"
        response = requests.get(endpoint, params=params)
        return response.url


def get_token_by_code(code, url_redirect, app, id, secret):
    if app == 'github':
        params = dict(client_id=id,
                      client_secret=secret,
                      redirect_uri=url_redirect,
                      code=code)
        headers = {"Accept": "application/json"}
        endpoint = "https://github.com/login/oauth/access_token"
        response = requests.post(endpoint, params=params, headers=headers)
        data = response.json()
        token = data.get("access_token")
        return token
    elif app == 'vk':
        params = dict(client_id=id,
                      client_secret=secret,
                      redirect_uri=url_redirect,
                      code=code)
        headers = {"Accept": "application/json"}
        endpoint = "https://oauth.vk.com/access_token"
        response = requests.post(endpoint, params=params, headers=headers)
        data = response.json()
        token = data.get("access_token")
        email = data.get("email")
        return token, email


def get_user_info(access_token, app):
    # read the GitHub manual about headers
    if app == 'github':
        headers = {"Authorization": f"token {access_token}"}
        endpoint1 = "https://api.github.com/user"
        endpoint2 = "https://api.github.com/user/emails"
        response1 = requests.get(endpoint1, headers=headers)
        response2 = requests.get(endpoint2, headers=headers)
        data1 = response1.json()
        data2 = response2.json()
        username = data1.get("login")
        email = data2[0].get("email")
        return username, email
    elif app == 'vk':
        endpoint = f"https://api.vk.com/method/users.get?access_token={access_token}&v=5.131"
        response = requests.get(endpoint)
        data = response.json()
        name = data.get("response")[0].get("first_name")
        surname = data.get("response")[0].get("last_name")
        return name, surname
