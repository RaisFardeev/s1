def test_create(app, client):
    res = client.get('/ad/create')
    assert res.satus_code == 404
