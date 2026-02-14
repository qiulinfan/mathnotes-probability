#!/usr/bin/env python3
from pathlib import Path


IFRAME_TEMPLATE = '<iframe src="{pdf}" style="width: 100%; height: 95vh; border: 0;"></iframe>'


def build_chapter_markdown(stem: str, pdf_name: str) -> str:
    return (
        f"# {stem}\n\n"
        f"{IFRAME_TEMPLATE.format(pdf=pdf_name)}\n\n"
        "[← Back to Index](index.md)\n"
    )


def build_index_markdown(chapter_files: list[tuple[str, str]]) -> str:
    lines = ["# Chapters", "", "## PDFs", ""]

    if not chapter_files:
        lines.append("No chapter PDFs found in docs/. Run `make` first.")
        lines.append("")
        return "\n".join(lines)

    for title, md_name in chapter_files:
        lines.append(f"- [{title}]({md_name})")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated automatically from docs/*.pdf*")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    pdf_files = sorted(p for p in docs_dir.glob("*.pdf") if p.is_file())

    chapter_entries: list[tuple[str, str]] = []

    for pdf_path in pdf_files:
        stem = pdf_path.stem
        md_name = f"{stem}.md"
        md_path = docs_dir / md_name

        md_path.write_text(
            build_chapter_markdown(stem=stem, pdf_name=pdf_path.name),
            encoding="utf-8",
        )
        chapter_entries.append((stem, md_name))

    index_path = docs_dir / "index.md"
    index_path.write_text(build_index_markdown(chapter_entries), encoding="utf-8")

    print(f"Generated {len(chapter_entries)} chapter markdown file(s).")
    print(f"Updated {index_path.relative_to(project_root).as_posix()}")


if __name__ == "__main__":
    main()
