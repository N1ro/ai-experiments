class AuthService:
    def login(self, username, password):
        return username == "admin" and password == "secret"

    def logout(self, session_id):
        return True

    def reset_password(self, email):
        return f"Reset link sent to {email}"
