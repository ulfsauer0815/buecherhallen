import os


class Credentials:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


def retrieve_credentials() -> Credentials:
    username = os.getenv('BH_USERNAME')
    password = os.getenv('BH_PASSWORD')
    return Credentials(username, password)
