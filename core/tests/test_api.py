from conftest import Client


def test_login_response_401():
    payload = {
        'username': 'zahra',
        'password': '12345'
    }
    response = Client.post('/users/login/', json=payload)
    assert response.status_code == 401
