from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata


@dataclass(frozen=True)
class _LawdCodeRow:
    code: str
    sido: str
    sigungu: str | None
    dong: str | None


class LawdCodeService:
    def __init__(self, source_path: Path | str | None = None) -> None:
        self.source_path = Path(source_path) if source_path is not None else _default_source_path()
        self._rows: list[_LawdCodeRow] | None = None

    def resolve_lawd_code(
        self,
        *,
        sido: str | None,
        sigungu: str | None,
        dong: str | None,
    ) -> str | None:
        exact_matches = self.find_lawd_code_matches(
            sido=sido,
            sigungu=sigungu,
            dong=dong,
        )
        if len(exact_matches) == 1:
            return exact_matches[0][:5]

        normalized_sido = _normalize_sido_text(sido)
        normalized_sigungu = _normalize_region_text(sigungu)
        normalized_dong = _normalize_region_text(dong)
        if not normalized_sido:
            return None

        rows = self._load_rows()
        if normalized_sigungu and normalized_dong:
            for row in rows:
                if (
                    _normalize_sido_text(row.sido) == normalized_sido
                    and _normalize_region_text(row.sigungu) == normalized_sigungu
                    and _normalize_region_text(row.dong) == normalized_dong
                ):
                    return row.code[:5]
            return None

        if normalized_sigungu:
            for row in rows:
                if (
                    _normalize_sido_text(row.sido) == normalized_sido
                    and _normalize_region_text(row.sigungu) == normalized_sigungu
                    and not _normalize_region_text(row.dong)
                ):
                    return row.code[:5]

        for row in rows:
            if (
                _normalize_sido_text(row.sido) == normalized_sido
                and not _normalize_region_text(row.sigungu)
                and not _normalize_region_text(row.dong)
            ):
                return row.code[:5]
        return None

    def find_lawd_code_matches(
        self,
        *,
        sido: str | None,
        sigungu: str | None,
        dong: str | None,
    ) -> list[str]:
        normalized_sido = _normalize_sido_text(sido)
        normalized_sigungu = _normalize_region_text(sigungu)
        normalized_dong = _normalize_region_text(dong)
        if not normalized_sido or not normalized_dong:
            return []

        matches: list[str] = []
        for row in self._load_rows():
            if (
                _normalize_sido_text(row.sido) == normalized_sido
                and _normalize_region_text(row.sigungu) == normalized_sigungu
                and _normalize_region_text(row.dong) == normalized_dong
            ):
                matches.append(row.code)
        return matches

    def list_search_regions(self) -> list[dict[str, str | None]]:
        regions: list[dict[str, str | None]] = []
        seen_codes: set[str] = set()
        for row in self._load_rows():
            if _normalize_region_text(row.dong):
                continue
            if not row.sigungu and not _is_top_level_search_region(row.sido):
                continue
            lawd_code = row.code[:5]
            if lawd_code in seen_codes:
                continue
            seen_codes.add(lawd_code)
            regions.append(
                {
                    "lawd_code": lawd_code,
                    "sido": row.sido,
                    "sigungu": row.sigungu,
                }
            )
        regions.sort(
            key=lambda item: (
                _normalize_sido_text(item["sido"]),
                _normalize_region_text(item["sigungu"]),
                item["lawd_code"],
            )
        )
        return regions

    def _load_rows(self) -> list[_LawdCodeRow]:
        if self._rows is not None:
            return self._rows

        text = _read_source_text(self.source_path)
        rows: list[_LawdCodeRow] = []
        for index, line in enumerate(text.splitlines()):
            if index == 0 or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            raw_code, raw_name, raw_status = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if not raw_code.isdigit() or len(raw_code) != 10 or raw_status != "\uc874\uc7ac":
                continue
            sido, sigungu, dong = _split_lawd_name(raw_name)
            rows.append(
                _LawdCodeRow(
                    code=raw_code,
                    sido=sido,
                    sigungu=sigungu,
                    dong=dong,
                )
            )

        self._rows = rows
        return rows


def _default_source_path() -> Path:
    workspace_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        workspace_root / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc.txt",
        workspace_root / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc" / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc.txt",
        workspace_root / "estate-pulse" / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc.txt",
        workspace_root / "estate-pulse" / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc" / "\ubc95\uc815\ub3d9\ucf54\ub4dc \uc804\uccb4\uc790\ub8cc.txt",
    ]
    for candidate_path in candidate_paths:
        if candidate_path.exists():
            return candidate_path
    return candidate_paths[0]


def _read_source_text(source_path: Path) -> str:
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return source_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return source_path.read_text(encoding="utf-8", errors="ignore")


def _split_lawd_name(raw_name: str) -> tuple[str, str | None, str | None]:
    tokens = [token.strip() for token in raw_name.split() if token.strip()]
    if not tokens:
        return "", None, None

    sido = tokens[0]
    remainder = tokens[1:]
    if not remainder:
        return sido, None, None
    if len(remainder) == 1:
        token = remainder[0]
        if _looks_like_sigungu(token):
            return sido, token, None
        return sido, None, token

    first = remainder[0]
    if _looks_like_sigungu(first):
        return sido, first, " ".join(remainder[1:]) or None
    return sido, None, " ".join(remainder) or None


def _looks_like_sigungu(value: str) -> bool:
    return value.endswith(("\uc2dc", "\uad70", "\uad6c"))


def _is_top_level_search_region(sido: str) -> bool:
    return sido.endswith("\ud2b9\ubcc4\uc790\uce58\uc2dc")


def _normalize_region_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return "".join(normalized.split())


def _normalize_sido_text(value: str | None) -> str:
    normalized = _normalize_region_text(value)
    return _SIDO_ALIASES.get(normalized, normalized)


_SIDO_ALIASES = {
    "\uc11c\uc6b8\uc2dc": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
    "\ubd80\uc0b0\uc2dc": "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
    "\ub300\uad6c\uc2dc": "\ub300\uad6c\uad11\uc5ed\uc2dc",
    "\uc778\ucc9c\uc2dc": "\uc778\ucc9c\uad11\uc5ed\uc2dc",
    "\uad11\uc8fc\uc2dc": "\uad11\uc8fc\uad11\uc5ed\uc2dc",
    "\ub300\uc804\uc2dc": "\ub300\uc804\uad11\uc5ed\uc2dc",
    "\uc6b8\uc0b0\uc2dc": "\uc6b8\uc0b0\uad11\uc5ed\uc2dc",
    "\uc138\uc885\uc2dc": "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
}
