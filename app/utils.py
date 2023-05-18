import requests
from flask import Flask, redirect, request
from flask_sqlalchemy import SQLAlchemy
from .models import Ad, User, Photo
from . import bcrypt


def fill_database(app: Flask, db: SQLAlchemy):
    with app.app_context():
        try:
            password = bcrypt.generate_password_hash('password')
            u = User(name='User1', email='user1@mail.ru', password=password)
            db.session.add(u)
            db.session.commit()
            u_id = db.session.query(User.id).where(User.name == 'User1').first().id
            for i in range(1, 10):
                ad = Ad(creator_id=u_id, name=f'Ad{i}', description=f'description{i}', price=i)
                db.session.add(ad)
                ad_id = db.session.query(User.id).where(Ad.name == ad.name).first().id
                photo = Photo(ad_id=ad_id, path='static/imgs/1.jpg')
                db.session.add(photo)
                db.session.commit()
            db.session.commit()
        except:
            pass


class AbstractAuth:
    def __init__(self, app_id, secret, url_redirect, scope):
        self.app_id = app_id
        self.secret = secret
        self.url_redirect = url_redirect
        self.scope = scope
        self.token_url = ''
        self.authorize_url = ''

    def generate_link(self):
        params = dict(client_id=self.app_id,
                      redirect_uri=self.url_redirect,
                      scope=self.scope,
                      response_type="code")
        response = requests.get(self.authorize_url, params=params)
        return redirect(response.url)

    def get_token_by_code(self, request, information):
        code = request.args.get("code")
        params = dict(client_id=self.app_id,
                      client_secret=self.secret,
                      redirect_uri=self.url_redirect,
                      code=code)
        headers = {"Accept": "application/json"}
        response = requests.post(self.token_url, params=params, headers=headers)
        data = response.json()
        info = [data.get(i) for i in information]
        return info

    def get_user_info(self, access_token):
        pass


class VkAuth(AbstractAuth):
    def __init__(self, vk_id, vk_secret, url_redirect):
        super().__init__(vk_id, vk_secret, url_redirect, 'email')
        self.app_id = vk_id
        self.app_secret = vk_secret
        self.token_url = 'https://oauth.vk.com/access_token'
        self.authorize_url = 'https://oauth.vk.com/authorize'

    def generate_link(self):
        super().generate_link()

    def get_token_by_code(self, code, information):
        super().get_token_by_code(code, ["token", "email"])

    def get_user_info(self, access_token):
        endpoint = f"https://api.vk.com/method/users.get?access_token={access_token}&v=5.131"
        response = requests.get(endpoint)
        data = response.json()
        name = data.get("response")[0].get("first_name")
        return name


class GithubAuth(AbstractAuth):
    def __init__(self, url_redirect):
        super().__init__('2273d84c17c586d01c89', '99106c9933c71257f12c4a262041d3b0b23000b4', url_redirect, 'user')
        self.token_url = 'https://github.com/login/oauth/access_token'
        self.authorize_url = 'https://github.com/login/oauth/authorize'

    def generate_link(self):
        super().generate_link()

    def get_token_by_code(self, code, information):
        super().get_token_by_code(code, ["token", ])

    def get_user_info(self, access_token):
        headers = {"Authorization": f"token {access_token}"}
        endpoint = "https://api.github.com/user"
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        name = data.get("name")
        username = data.get("login")
        return name, username


def generate_link(url_redirect, service_id, app):
    if app == 'github':
        params = dict(client_id=service_id,  # the client ID you received from GitHub when you registered
                      redirect_uri=url_redirect,  # the URL in your application where users will be sent after authorization
                      scope="user",  # type of access
                      response_type="code")  # request the code
        endpoint = "https://github.com/login/oauth/authorize"
        response = requests.get(endpoint, params=params)
        return response.url
    elif app == 'vk':
        params = dict(client_id=service_id,  # the client ID you received from GitHub when you registered
                      redirect_uri=url_redirect,
                      # the URL in your application where users will be sent after authorization
                      scope="email",  # type of access
                      response_type="code")  # request the code
        endpoint = "https://oauth.vk.com/authorize"
        response = requests.get(endpoint, params=params)
        return response.url


def get_token_by_code(code, url_redirect, app, service_id, service_secret):
    if app == 'github':
        params = dict(client_id= service_id,
                      client_secret=service_secret,
                      redirect_uri=url_redirect,
                      code=code)
        headers = {"Accept": "application/json"}
        endpoint = "https://github.com/login/oauth/access_token"
        response = requests.post(endpoint, params=params, headers=headers)
        data = response.json()
        token = data.get("access_token")
        return token
    elif app == 'vk':
        params = dict(client_id=service_id,
                      client_secret=service_secret,
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
        endpoint = "https://api.github.com/user"
        response = requests.get(endpoint, headers=headers)

        data = response.json()
        name = data.get("name")
        username = data.get("login")
        private_repos_count = data.get("total_private_repos")
        return name, username, private_repos_count
    elif app == 'vk':
        endpoint = f"https://api.vk.com/method/users.get?access_token={access_token}&v=5.131"
        response = requests.get(endpoint)
        data = response.json()
        name = data.get("response")[0].get("first_name")
        surname = data.get("response")[0].get("last_name")
        return name, surname