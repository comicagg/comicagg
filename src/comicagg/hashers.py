import hashlib

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_noop as _


class LegacySHA1PasswordHasher(BasePasswordHasher):
    """Support legacy salted SHA-1 passwords until they are upgraded on login."""

    algorithm = "sha1"

    def encode(self, password, salt):
        self._check_encode_args(password, salt)
        digest = hashlib.sha1((salt + password).encode()).hexdigest()
        return f"{self.algorithm}${salt}${digest}"

    def decode(self, encoded):
        algorithm, salt, digest = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {"algorithm": algorithm, "salt": salt, "hash": digest}

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        return constant_time_compare(encoded, self.encode(password, decoded["salt"]))

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("salt"): mask_hash(decoded["salt"], show=2),
            _("hash"): mask_hash(decoded["hash"]),
        }

    def harden_runtime(self, password, encoded):
        # Legacy SHA-1 has no adjustable work factor.
        pass
