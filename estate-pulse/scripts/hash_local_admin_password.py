from __future__ import annotations

from getpass import getpass

from argon2 import PasswordHasher


MIN_PASSWORD_LENGTH = 16


def generate_password_hash(password: str, confirmation: str) -> str:
    if password != confirmation:
        raise ValueError("password_confirmation_mismatch")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("password_too_short")
    return PasswordHasher().hash(password)


def main() -> int:
    try:
        password_hash = generate_password_hash(
            getpass("관리자 비밀번호: "),
            getpass("관리자 비밀번호 확인: "),
        )
    except ValueError as exc:
        messages = {
            "password_confirmation_mismatch": "비밀번호 확인이 일치하지 않습니다.",
            "password_too_short": f"비밀번호는 {MIN_PASSWORD_LENGTH}자 이상이어야 합니다.",
        }
        print(messages.get(str(exc), "비밀번호를 확인해 주세요."))
        return 1
    print(password_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
