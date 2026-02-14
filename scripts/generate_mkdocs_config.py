#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path


def get_origin_remote(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def parse_owner_repo(remote_url: str) -> tuple[str, str, str]:
    if not remote_url:
        return "unknown", "notes", ""

    normalized = remote_url.strip()
    normalized = normalized[:-4] if normalized.endswith(".git") else normalized

    https_match = re.match(r"https?://[^/]+/([^/]+)/([^/]+)$", normalized)
    ssh_match = re.match(r"git@[^:]+:([^/]+)/([^/]+)$", normalized)

    if https_match:
        owner, repo = https_match.groups()
        repo_url = normalized
    elif ssh_match:
        owner, repo = ssh_match.groups()
        repo_url = f"https://github.com/{owner}/{repo}"
    else:
        owner, repo = "unknown", Path(normalized).stem or "notes"
        repo_url = normalized

    return owner, repo, repo_url


def page_title_from_md(md_path: Path) -> str:
    try:
        for line in md_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    except FileNotFoundError:
        pass
    return md_path.stem


def generate_nav_items(docs_dir: Path) -> list[tuple[str, str]]:
    pages = sorted(
        p
        for p in docs_dir.glob("*.md")
        if p.is_file() and p.name.lower() != "index.md"
    )

    return [(page_title_from_md(page), page.name) for page in pages]


def build_mkdocs_yaml(
    site_name: str,
    site_author: str,
    repo_name: str,
    repo_url: str,
    nav_items: list[tuple[str, str]],
    include_extra_css: bool,
) -> str:
    lines: list[str] = [
        f"site_name: {site_name}",
        f"site_author: {site_author}",
        f"site_url: {repo_url}",
        "use_directory_urls: false",
        "remote_branch: gh-deploy",
        "",
        f"repo_name: {repo_name}",
        f"repo_url: {repo_url}",
        "",
        "theme:",
        "  name: material",
        "",
        "plugins:",
        "  - search",
        "",
        "markdown_extensions:",
        "  - tables",
        "  - attr_list",
        "  - md_in_html",
    ]

    if include_extra_css:
        lines.extend(["", "extra_css:", "  - stylesheets/extra.css"])

    lines.extend(["", "nav:", "  - Home: index.md"])

    if nav_items:
        lines.append("  - Chapters:")
        for title, filename in nav_items:
            safe_title = title.replace(":", "-")
            lines.append(f"    - {safe_title}: {filename}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    remote_url = get_origin_remote(project_root)
    owner, repo, repo_url = parse_owner_repo(remote_url)

    nav_items = generate_nav_items(docs_dir)
    include_extra_css = (docs_dir / "stylesheets" / "extra.css").exists()

    mkdocs_content = build_mkdocs_yaml(
        site_name=repo,
        site_author=owner,
        repo_name=repo,
        repo_url=repo_url,
        nav_items=nav_items,
        include_extra_css=include_extra_css,
    )

    mkdocs_path = project_root / "mkdocs.yml"
    mkdocs_path.write_text(mkdocs_content, encoding="utf-8")

    print(f"Updated {mkdocs_path.relative_to(project_root).as_posix()}")
    print(f"Discovered {len(nav_items)} chapter page(s) from docs/*.md")


if __name__ == "__main__":
    main()
