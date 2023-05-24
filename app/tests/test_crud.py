from .. import db


def test_registration(app, client):
    data = dict(email='rfgfdgfgf@mail.ru', name='asddsdfdv', password1='qw', password2='qw')
    res = client.post('/registrate', data=data)
    assert res.status_code == 200


def test_login(app, client):
    data = dict(email='rfgfdfgf@mail.ru', password='qw')
    res = client.post('/login', data=data)
    assert res.status_code == 200


def test_edit_profile(app, client):
    data = dict(email='rfgfdgfgf@mail.ru', name='asddsdfdv', old_password='qw', new_password1='qw12', new_password2='qw12')
    res = client.post('/editprofile', data=data)
    assert res.status_code == 302


def test_create_ad(app, client):
    data = dict(name='asddsdfdv', description='adfeffsdce', category='kids', price='21')
    res = client.post('/ad/create', data=data)
    assert res.status_code == 302


def test_ad_delete(app, client):
    res = client.get('/ad/1/delete')
    assert res.status_code == 302
