import os
from email.utils import parseaddr
from urllib import parse

extra_schemes = ["psycopg2"]
for scheme in extra_schemes:
    parse.uses_relative.append(scheme)
    parse.uses_netloc.append(scheme)
    parse.uses_params.append(scheme)


class EnvVarMissingError(Exception):
    pass


class Env:
    def __init__(self, namespace="DJANGO") -> None:
        self.namespace = namespace

    # Generic methods

    def getn(self, key: str) -> str | None:
        """Get an env var returning None if it doesn't exist"""
        var_name = f"{self.namespace}_{key}"
        return os.environ.get(var_name)

    def get(self, key: str) -> str:
        """Get an env var raising an Error if it doesn't exist"""
        var = self.getn(key)
        if var is None:
            raise EnvVarMissingError(f"Missing env var: {self.namespace}_{key}")
        return var

    def int(self, key: str, default: int) -> int:
        var = self.getn(key)
        return int(var) if var is not None else default

    def list(self, key: str) -> list[str]:
        """Get an env var as a list of strings separated by commas."""
        value = self.getn(key)
        return [] if value is None else value.split(",")

    def url(self, key: str) -> parse.ParseResult:
        # scheme://netloc/path;parameters?query#fragment
        return parse.urlparse(self.get(key))

    # Specialized methods

    def email_list(self, key: str):
        """Expected value: comma separated list of 'User <email>'"""
        return [parseaddr(email) for email in self.list(key)]

    def db(self, key: str):
        """Expected value: postgresql://user:password@host:port/name"""

        result = self.url(key)
        result = result._replace(scheme=f"django.db.backends.{result.scheme}")
        if result.scheme == "django.db.backends.psycopg2":
            result = result._replace(scheme="django.db.backends.postgresql_psycopg2")
        return {
            # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            "ENGINE": result.scheme,
            # Or path to database file if using sqlite3.
            "NAME": result.path[1:],
            # Set to empty string for localhost. Not used with sqlite3.
            "HOST": result.hostname,
            # Set to empty string for default. Not used with sqlite3.
            "PORT": result.port,
            # Not used with sqlite3.
            "USER": result.username,
            # Not used with sqlite3.
            "PASSWORD": result.password,
            "TEST": {
                "TEMPLATE": "template0",
            }
        }
