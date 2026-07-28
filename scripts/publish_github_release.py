#!/usr/bin/env python3
"""Create or update a GitHub Release and upload the .ankiaddon (uses git credential)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chinese_word_synonyms.about_meta import ADDON_VERSION, CHANGELOG  # noqa: E402

REPO = "sageozzeus/Chinese-Word-Synonyms"


def _github_token() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=False,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("No GitHub credential for github.com (git push must work first).")


def _api(
    method: str,
    url: str,
    *,
    data: dict | None = None,
    raw: bytes | None = None,
    extra_headers: dict | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {_github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "chinese-word-synonyms-release",
    }
    if extra_headers:
        headers.update(extra_headers)
    body: bytes | None = raw
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} {url}: {e.read().decode()}") from e


def _release_notes(version: str) -> str:
    lines = [f"## Chinese Word Synonyms {version}", ""]
    for v, bullets in CHANGELOG:
        if v == version:
            for b in bullets:
                lines.append(f"- {b}")
            return "\n".join(lines)
    return f"Release {version}."


def main() -> None:
    version = ADDON_VERSION
    tag = f"v{version}"
    asset_path = ROOT / f"chinese_word_synonyms-{version}.ankiaddon"
    if not asset_path.is_file():
        raise SystemExit(f"Missing {asset_path.name} — run the zip build first.")

    notes = _release_notes(version)
    releases = _api("GET", f"https://api.github.com/repos/{REPO}/releases?per_page=100")
    release = next((r for r in releases if r.get("tag_name") == tag), None)

    if not release:
        release = _api(
            "POST",
            f"https://api.github.com/repos/{REPO}/releases",
            data={
                "tag_name": tag,
                "target_commitish": "main",
                "name": tag,
                "body": notes,
                "draft": False,
            },
        )
        print(f"Created release {tag}")
    else:
        _api(
            "PATCH",
            f"https://api.github.com/repos/{REPO}/releases/{release['id']}",
            data={"body": notes, "name": tag},
        )
        print(f"Updated release {tag}")

    upload_url = release["upload_url"].split("{")[0]
    asset_name = asset_path.name
    for a in release.get("assets", []):
        if a.get("name") == asset_name:
            _api("DELETE", f"https://api.github.com/repos/{REPO}/releases/assets/{a['id']}")
            print(f"Removed previous asset {asset_name}")

    data = asset_path.read_bytes()
    asset = _api(
        "POST",
        f"{upload_url}?name={asset_name}",
        raw=data,
        extra_headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(data)),
        },
    )
    print(asset.get("browser_download_url") or release.get("html_url"))


if __name__ == "__main__":
    main()
