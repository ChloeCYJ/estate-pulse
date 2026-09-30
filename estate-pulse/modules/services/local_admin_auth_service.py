from __future__ import annotations

from dataclasses import dataclass
import hmac
import logging
from typing import Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


logger = logging.getLogger(__name__)
PLACEHOLDER_PREFIX = "REPLACE_WITH_"


@dataclass(frozen=True)
class LocalAdminConfig:
    enabled: bool
    username: str | None
    password_hash: str | None

    @property
    def is_configured(self) -> bool:
        username = str(self.username or "").strip()
        password_hash = str(self.password_hash or "").strip()
        return bool(
            self.enabled
            and username
            and password_hash
            and not username.startswith(PLACEHOLDER_PREFIX)
            and not password_hash.startswith(PLACEHOLDER_PREFIX)
        )


@dataclass(frozen=True)
class LocalAdminPrincipal:
    username: str
    role: Literal["admin"] = "admin"


class LocalAdminAuthenticationError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class LocalAdminAuthService:
    def __init__(
        self,
        config: LocalAdminConfig,
        *,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.config = config
        self.password_hasher = password_hasher or PasswordHasher()

    def authenticate(self, *, username: str, password: str) -> LocalAdminPrincipal:
        if not self.config.enabled:
            logger.warning("Local administrator login rejected: disabled")
            raise LocalAdminAuthenticationError("admin_disabled")
        if not self.config.is_configured:
            logger.error("Local administrator login rejected: configuration unavailable")
            raise LocalAdminAuthenticationError("admin_not_configured")

        configured_username = str(self.config.username or "").strip()
        submitted_username = str(username or "").strip()
        username_matches = hmac.compare_digest(
            configured_username.encode("utf-8"),
            submitted_username.encode("utf-8"),
        )

        try:
            password_matches = bool(
                self.password_hasher.verify(
                    str(self.config.password_hash),
                    str(password or ""),
                )
            )
        except VerifyMismatchError:
            password_matches = False
        except (InvalidHashError, VerificationError) as exc:
            logger.error("Local administrator login rejected: invalid password hash")
            raise LocalAdminAuthenticationError("admin_not_configured") from exc

        if not username_matches or not password_matches:
            logger.warning("Local administrator login failed")
            raise LocalAdminAuthenticationError("invalid_credentials")

        logger.info("Local administrator login succeeded")
        return LocalAdminPrincipal(username=configured_username)
