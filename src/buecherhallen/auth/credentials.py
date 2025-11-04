import os


class Credentials:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


def retrieve_credentials() -> Credentials:
    username = __get_required_env('BH_USERNAME')
    password = __get_required_env('BH_PASSWORD')
    return Credentials(username, password)


def __get_required_env(env_name: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        raise ValueError(f"Environment variable {env_name} is required but not set")
    return value
