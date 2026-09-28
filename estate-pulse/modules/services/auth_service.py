from __future__ import annotations

from dataclasses import dataclass


class AuthenticationResolutionError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class VerifiedIdentity:
    issuer: str
    subject: str
    provider: str
    email: str | None
    display_name: str | None


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    display_name: str | None
    email: str | None
    provider: str


class AuthService:
    def __init__(self, user_account_repository) -> None:
        self.user_account_repository = user_account_repository

    def resolve(self, identity: VerifiedIdentity) -> AuthenticatedUser:
        issuer = str(identity.issuer or "").strip()
        subject = str(identity.subject or "").strip()
        if not issuer or not subject:
            raise AuthenticationResolutionError("invalid_identity")

        account = self.user_account_repository.get_by_identity(
            issuer=issuer,
            subject=subject,
        )
        if account is None:
            account = self.user_account_repository.create_user_with_identity(
                issuer=issuer,
                subject=subject,
                provider=str(identity.provider or "Social").strip() or "Social",
                email=_optional_text(identity.email),
                display_name=_optional_text(identity.display_name),
            )
        else:
            self.user_account_repository.touch_identity(
                identity_id=int(account["identity_id"]),
            )

        return AuthenticatedUser(
            id=int(account["user_id"]),
            display_name=_optional_text(account.get("display_name")),
            email=_optional_text(account.get("email")),
            provider=str(account.get("provider") or identity.provider or "Social"),
        )


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
