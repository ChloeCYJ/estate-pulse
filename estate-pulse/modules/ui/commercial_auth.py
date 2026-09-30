from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Mapping, MutableMapping
from urllib.parse import urlparse

import streamlit as st

from modules.services.auth_service import (
    AuthenticatedUser,
    AuthenticationResolutionError,
    AuthService,
    VerifiedIdentity,
)


AUTH_PROVIDER_KEY = "auth0"
AUTH_CONNECTION_CLAIM = "https://estate-pulse.app/connection"
SAFE_SEARCH_QUERY_KEY = "commercial_search_home_query"
AUTH_ERROR_SESSION_KEY = "commercial_auth_error_code"

LOGGER = logging.getLogger(__name__)

AUTH_ERROR_MESSAGES = {
    "auth_not_configured": "로그인 설정이 완료되지 않았습니다. 운영자에게 문의해 주세요.",
    "login_start_failed": "로그인 화면을 열지 못했습니다. 잠시 후 다시 시도해 주세요.",
    "invalid_identity": "로그인 정보를 확인하지 못했습니다. 로그아웃 후 다시 로그인해 주세요.",
    "account_resolution_failed": "회원 정보를 준비하지 못했습니다. 잠시 후 다시 시도해 주세요.",
}

PROVIDER_LABELS = {
    "google": "Google",
    "google-oauth2": "Google",
    "kakao": "Kakao",
    "kakao-oauth2": "Kakao",
    "naver": "Naver",
    "naver-oauth2": "Naver",
}


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
        provider=_provider_label(
            subject,
            connection_name=_optional_text(user_claims.get(AUTH_CONNECTION_CLAIM)),
        ),
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
    except Exception as exc:
        LOGGER.warning(
            "Commercial account resolution failed (%s)",
            type(exc).__name__,
        )
        return CommercialAuthContext(user=None, error_code="account_resolution_failed")


def apply_commercial_auth_session_error(
    *,
    context: CommercialAuthContext,
    session_state: MutableMapping[str, object],
) -> CommercialAuthContext:
    if context.user is not None:
        session_state.pop(AUTH_ERROR_SESSION_KEY, None)
        return context
    if context.error_code is not None:
        return context

    pending_error = str(session_state.get(AUTH_ERROR_SESSION_KEY) or "").strip()
    if pending_error not in AUTH_ERROR_MESSAGES:
        return context
    return CommercialAuthContext(user=None, error_code=pending_error)


def build_commercial_auth_view_model(
    *,
    context: CommercialAuthContext,
    has_finance_profile: bool,
) -> dict[str, object]:
    if context.error_code is not None:
        message = AUTH_ERROR_MESSAGES.get(
            context.error_code,
            "로그인을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.",
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


def validate_commercial_auth_configuration(
    secrets: Mapping[str, object],
) -> str | None:
    auth = _mapping(secrets.get("auth"))
    provider = _mapping(auth.get(AUTH_PROVIDER_KEY))
    required_values = (
        auth.get("redirect_uri"),
        auth.get("cookie_secret"),
        provider.get("client_id"),
        provider.get("client_secret"),
        provider.get("server_metadata_url"),
    )
    if any(_missing_or_placeholder(value) for value in required_values):
        return "auth_not_configured"

    redirect_uri = urlparse(str(auth["redirect_uri"]).strip())
    metadata_uri = urlparse(str(provider["server_metadata_url"]).strip())
    local_redirect = redirect_uri.hostname in {"localhost", "127.0.0.1"}
    if (
        len(str(auth["cookie_secret"]).strip()) < 32
        or not redirect_uri.netloc
        or redirect_uri.path != "/oauth2callback"
        or redirect_uri.scheme not in ({"http", "https"} if local_redirect else {"https"})
        or metadata_uri.scheme != "https"
        or not metadata_uri.netloc
        or not metadata_uri.path.endswith("/.well-known/openid-configuration")
    ):
        return "auth_not_configured"
    return None


def login_commercial_user() -> str | None:
    try:
        configuration_error = validate_commercial_auth_configuration(st.secrets)
    except Exception as exc:
        LOGGER.warning(
            "Commercial auth configuration unavailable (%s)",
            type(exc).__name__,
        )
        configuration_error = "auth_not_configured"
    if configuration_error is not None:
        st.session_state[AUTH_ERROR_SESSION_KEY] = configuration_error
        st.error(AUTH_ERROR_MESSAGES[configuration_error])
        st.rerun()
        return configuration_error

    st.session_state.pop(AUTH_ERROR_SESSION_KEY, None)
    try:
        st.login(AUTH_PROVIDER_KEY)
    except Exception as exc:
        error_code = "login_start_failed"
        st.session_state[AUTH_ERROR_SESSION_KEY] = error_code
        LOGGER.warning(
            "Commercial login start failed (%s)",
            type(exc).__name__,
        )
        st.error(AUTH_ERROR_MESSAGES[error_code])
        st.rerun()
        return error_code
    return None


def logout_commercial_user() -> None:
    clear_commercial_sensitive_state(st.session_state)
    st.logout()


def _provider_label(subject: str, *, connection_name: str | None = None) -> str:
    connections = (
        str(connection_name or "").strip().lower(),
        subject.split("|", 1)[0].strip().lower(),
    )
    for connection in connections:
        if connection in PROVIDER_LABELS:
            return PROVIDER_LABELS[connection]
    return "Social"


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _missing_or_placeholder(value: object) -> bool:
    text = str(value or "").strip()
    return not text or text.startswith("REPLACE_WITH_")
