def test_api_ads(app, client):
    res = client.get('/api/v1/get_ads')
    assert res.status_code == 200


def test_api_users(app, client):
    res = client.get('/api/v1/get_users')
    assert res.status_code == 200


def test_api_user(app, client):
    res = client.get('/api/v1/get_users/abcdefg@mail.ru')
    assert res.status_code == 404
