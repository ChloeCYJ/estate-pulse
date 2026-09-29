from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping

import streamlit as st

from modules.services.auth_service import (
    AuthenticatedUser,
    AuthenticationResolutionError,
    AuthService,
    VerifiedIdentity,
)


AUTH_PROVIDER_KEY = "auth0"
SAFE_SEARCH_QUERY_KEY = "commercial_search_home_query"


@dataclass(frozen=True)
class CommercialAuthContext:
    user: AuthenticatedUser | None
    error_code: str | None


def resolve_commercial_auth_context(
    *,
    user_claims: Mapping[str, object],
    auth_service: AuthService,
) -> CommercialAuthContext:
    if not bool(user_claims.get("is_logged_in", False)):
        return CommercialAuthContext(user=None, error_code=None)

    issuer = _optional_text(user_claims.get("iss"))
    subject = _optional_text(user_claims.get("sub"))
    if issuer is None or subject is None:
        return CommercialAuthContext(user=None, error_code="invalid_identity")

    identity = VerifiedIdentity(
        issuer=issuer,
        subject=subject,
        provider=_provider_label(subject),
        email=_optional_text(user_claims.get("email")),
        display_name=_optional_text(user_claims.get("name")),
    )
    try:
        return CommercialAuthContext(
            user=auth_service.resolve(identity),
            error_code=None,
        )
    except AuthenticationResolutionError as exc:
        return CommercialAuthContext(user=None, error_code=exc.code)
    except Exception:
        return CommercialAuthContext(user=None, error_code="account_resolution_failed")


def build_commercial_auth_view_model(
    *,
    context: CommercialAuthContext,
    has_finance_profile: bool,
) -> dict[str, object]:
    if context.error_code is not None:
        message = (
            "로그인 설정이 필요합니다. 운영자에게 문의해 주세요."
            if context.error_code == "auth_not_configured"
            else "로그인 정보를 확인하지 못했습니다. 다시 로그인해 주세요."
        )
        return {
            "status": "error",
            "display_name": None,
            "email": None,
            "provider": None,
            "finance_profile_exists": False,
            "error": {
                "code": context.error_code,
                "message": message,
            },
        }
    if context.user is None:
        return {
            "status": "anonymous",
            "display_name": None,
            "email": None,
            "provider": None,
            "finance_profile_exists": False,
            "error": None,
        }
    return {
        "status": "authenticated",
        "display_name": context.user.display_name,
        "email": context.user.email,
        "provider": context.user.provider,
        "finance_profile_exists": bool(has_finance_profile),
        "error": None,
    }


def clear_commercial_sensitive_state(
    session_state: MutableMapping[str, object],
) -> None:
    for key in list(session_state):
        if str(key).startswith("commercial_") and key != SAFE_SEARCH_QUERY_KEY:
            session_state.pop(key, None)


def login_commercial_user() -> None:
    try:
        st.login(AUTH_PROVIDER_KEY)
    except Exception:
        st.error("로그인 설정이 완료되지 않았습니다. 운영자에게 문의해 주세요.")


def logout_commercial_user() -> None:
    clear_commercial_sensitive_state(st.session_state)
    st.logout()


def _provider_label(subject: str) -> str:
    connection = subject.split("|", 1)[0].lower()
    return {
        "google-oauth2": "Google",
        "kakao": "Kakao",
        "naver": "Naver",
    }.get(connection, "Social")


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
