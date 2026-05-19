from src.auth import AuthService


def test_login_success():
    svc = AuthService()
    assert svc.login("admin", "secret") is True
