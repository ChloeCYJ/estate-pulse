from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping

import streamlit as st

from modules.services.local_admin_auth_service import (
    LocalAdminAuthenticationError,
    LocalAdminAuthService,
    LocalAdminConfig,
    LocalAdminPrincipal,
)


LOCAL_ADMIN_SESSION_KEY = "local_admin_principal"
LOCAL_ADMIN_ERROR_KEY = "local_admin_error"


def load_local_admin_config(secrets: Mapping[str, object]) -> LocalAdminConfig:
    try:
        section = secrets.get("local_admin", {})
        if not isinstance(section, Mapping):
            return LocalAdminConfig(enabled=False, username=None, password_hash=None)
        return LocalAdminConfig(
            enabled=_as_bool(section.get("enabled", False)),
            username=_optional_text(section.get("username")),
            password_hash=_optional_text(section.get("password_hash")),
        )
    except Exception:
        return LocalAdminConfig(enabled=False, username=None, password_hash=None)


def is_admin_portal_requested(query_params: Mapping[str, object]) -> bool:
    try:
        value = query_params.get("admin")
    except Exception:
        return False
    if isinstance(value, (list, tuple)):
        value = value[-1] if value else None
    return str(value or "").strip() == "1"


def load_local_admin_principal(
    session_state: Mapping[str, object],
) -> LocalAdminPrincipal | None:
    payload = session_state.get(LOCAL_ADMIN_SESSION_KEY)
    if not isinstance(payload, Mapping):
        return None
    username = _optional_text(payload.get("username"))
    if username is None or payload.get("role") != "admin":
        return None
    return LocalAdminPrincipal(username=username)


def authenticate_local_admin(
    *,
    session_state: MutableMapping[str, object],
    auth_service: LocalAdminAuthService,
    username: str,
    password: str,
) -> LocalAdminPrincipal | None:
    try:
        principal = auth_service.authenticate(username=username, password=password)
    except LocalAdminAuthenticationError as exc:
        session_state[LOCAL_ADMIN_ERROR_KEY] = exc.code
        return None
    session_state[LOCAL_ADMIN_SESSION_KEY] = {
        "username": principal.username,
        "role": principal.role,
    }
    session_state.pop(LOCAL_ADMIN_ERROR_KEY, None)
    return principal


def logout_local_admin(session_state: MutableMapping[str, object]) -> None:
    session_state.pop(LOCAL_ADMIN_SESSION_KEY, None)
    session_state.pop(LOCAL_ADMIN_ERROR_KEY, None)


def render_local_admin_gate(
    *,
    auth_service: LocalAdminAuthService,
    admin_renderer: Callable[[], None],
) -> None:
    principal = load_local_admin_principal(st.session_state)
    if principal is not None:
        st.caption(f"로컬 관리자 · {principal.username}")
        if st.button("관리자 로그아웃"):
            logout_local_admin(st.session_state)
            st.rerun()
            return
        admin_renderer()
        return

    st.title("관리자 로그인")
    if not auth_service.config.enabled:
        st.warning("로컬 관리자 로그인이 비활성화되어 있습니다.")
        return
    if not auth_service.config.is_configured:
        st.warning("로컬 관리자 계정 설정이 필요합니다.")
        return

    with st.form("local_admin_login_form"):
        username = st.text_input("관리자 아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")

    if submitted:
        principal = authenticate_local_admin(
            session_state=st.session_state,
            auth_service=auth_service,
            username=username,
            password=password,
        )
        if principal is None:
            if st.session_state.get(LOCAL_ADMIN_ERROR_KEY) == "admin_not_configured":
                st.error("로컬 관리자 계정 설정을 확인해 주세요.")
            else:
                st.error("관리자 아이디 또는 비밀번호가 올바르지 않습니다.")
            return
        st.rerun()


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
