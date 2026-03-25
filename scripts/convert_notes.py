#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


HEADING_TO_MD = {
    "chapter": "#",
    "section": "##",
    "subsection": "###",
    "subsubsection": "####",
    "paragraph": "#####",
    "subparagraph": "######",
}

MD_TO_HEADING = {
    1: "chapter",
    2: "section",
    3: "subsection",
    4: "subsubsection",
    5: "paragraph",
    6: "subparagraph",
}

THEOREM_DISPLAY_NAMES = {
    "theorem": "Theorem",
    "definition": "Definition",
    "proposition": "Proposition",
    "corollary": "Corollary",
    "lemma": "Lemma",
    "example": "Example",
    "proof": "Proof",
    "solution": "Solution",
    "remark": "Remark",
    "note": "Note",
    "exercise": "Exercise",
    "problem": "Problem",
}

CODE_ENV_NAMES = {"verbatim", "lstlisting", "minted"}

DISPLAY_NAME_TO_ENV = {
    display.lower(): env for env, display in THEOREM_DISPLAY_NAMES.items()
}

LIST_BEGIN_RE = re.compile(r"\\begin\{(itemize|enumerate)\}")
LIST_END_RE = re.compile(r"\\end\{(itemize|enumerate)\}")
INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", re.DOTALL)
MD_LIST_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-+*]|\d+[.)])\s+(?P<content>.*)$")
BLOCKQUOTE_RE = re.compile(r"^> ?(.*)$")
MD_IMAGE_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)$")
FENCE_RE = re.compile(r"^```(?P<lang>[A-Za-z0-9_+-]*)\s*$")
HTML_IMAGE_RE = re.compile(r"^<img\s+(?P<attrs>[^>]*?)/?>$", flags=re.IGNORECASE)
HTML_ATTR_RE = re.compile(r"(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(['\"])(?P<value>.*?)\2")


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_outer_blank_lines(text: str) -> str:
    return text.strip("\n")


def collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def normalize_markdown_display_math_lines(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.splitlines():
        if "$$" not in line or line.strip() == "$$":
            normalized_lines.append(line)
            continue

        prefix_match = re.match(r"^((?:>\s*)+)", line)
        prefix = prefix_match.group(1) if prefix_match else ""
        content = line[len(prefix):]
        pieces = content.split("$$")

        if len(pieces) == 1:
            normalized_lines.append(line)
            continue

        for index, piece in enumerate(pieces):
            stripped_piece = piece.strip()
            if stripped_piece:
                normalized_lines.append(f"{prefix}{stripped_piece}")
            if index < len(pieces) - 1:
                normalized_lines.append(f"{prefix}$$")

    return "\n".join(normalized_lines)


def strip_tex_comments(text: str) -> str:
    result: list[str] = []
    code_depth = 0

    for line in text.splitlines():
        stripped = line.strip()

        begin_match = re.match(r"^\\begin\{([a-zA-Z*]+)\}", stripped)
        end_match = re.match(r"^\\end\{([a-zA-Z*]+)\}", stripped)

        if code_depth == 0:
            cleaned: list[str] = []
            escaped = False
            for char in line:
                if char == "%" and not escaped:
                    break
                cleaned.append(char)
                escaped = (char == "\\" and not escaped)
                if char != "\\":
                    escaped = False
            line = "".join(cleaned).rstrip()

        if line.strip():
            result.append(line)
        elif code_depth > 0:
            result.append(line)

        if begin_match and begin_match.group(1) in CODE_ENV_NAMES:
            code_depth += 1
        if end_match and end_match.group(1) in CODE_ENV_NAMES:
            code_depth = max(0, code_depth - 1)

    return "\n".join(result)


def parse_latex_keyval_options(option_text: str | None) -> dict[str, str]:
    if not option_text:
        return {}

    options: dict[str, str] = {}
    for part in option_text.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            options[key.strip().lower()] = value.strip()
        else:
            options[item.lower()] = ""
    return options


def latex_width_to_css(width_value: str) -> str | None:
    width = width_value.replace(" ", "")
    textwidth_match = re.fullmatch(r"(?:(\d*\.?\d+)\*?)?\\(textwidth|linewidth)", width)
    if textwidth_match:
        factor = float(textwidth_match.group(1) or "1")
        percentage = factor * 100
        percentage_text = f"{percentage:.4f}".rstrip("0").rstrip(".")
        return f"{percentage_text}%"

    if re.fullmatch(r"\d*\.?\d+%", width):
        return width

    if re.fullmatch(r"\d*\.?\d+(px|cm|mm|in|pt|pc|em|rem|vw|vh|vmin|vmax|ex|ch)", width):
        return width

    return None


def build_html_img_tag(path: str, alt: str = "", width_value: str | None = None) -> str:
    attrs = [f'src="{path}"']
    if alt:
        attrs.append(f'alt="{alt}"')
    else:
        attrs.append('alt=""')

    if width_value:
        attrs.append(f'data-latex-width="{width_value}"')
        css_width = latex_width_to_css(width_value)
        if css_width:
            attrs.append(f'style="width: {css_width};"')

    return f"<img {' '.join(attrs)} />"


def convert_tex_images(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        option_text = match.group(1)
        image_path = match.group(2).strip()
        options = parse_latex_keyval_options(option_text)
        width_value = options.get("width")
        return build_html_img_tag(image_path, width_value=width_value)

    return re.sub(
        r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}",
        repl,
        text,
    )


def convert_tex_bold(text: str) -> str:
    return re.sub(r"\\textbf\{([^{}]+)\}", lambda match: f"**{match.group(1)}**", text)


def parse_bracket_argument(text: str, start: int) -> tuple[str | None, int]:
    if start >= len(text):
        return None, start

    opening = text[start]
    pairs = {"{": "}", "[": "]"}
    if opening not in pairs:
        return None, start

    closing = pairs[opening]
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
        index += 1

    return None, start


def find_matching_end(text: str, env_name: str, content_start: int) -> tuple[int, int]:
    begin_token = f"\\begin{{{env_name}}}"
    end_token = f"\\end{{{env_name}}}"
    depth = 1
    index = content_start

    while index < len(text):
        next_begin = text.find(begin_token, index)
        next_end = text.find(end_token, index)

        if next_end == -1:
            return -1, -1

        if next_begin != -1 and next_begin < next_end:
            depth += 1
            index = next_begin + len(begin_token)
            continue

        depth -= 1
        if depth == 0:
            return next_end, next_end + len(end_token)
        index = next_end + len(end_token)

    return -1, -1


def convert_tex_math(text: str) -> str:
    text = re.sub(
        r"\\begin\{align\*?\}\s*(.*?)\s*\\end\{align\*?\}",
        lambda match: f"$$\n{match.group(1).strip()}\n$$",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\begin\{equation\*?\}\s*(.*?)\s*\\end\{equation\*?\}",
        lambda match: f"$$\n{match.group(1).strip()}\n$$",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\\[\s*(.*?)\s*\\\]",
        lambda match: f"$$\n{match.group(1).strip()}\n$$",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\\\((.*?)\\\)", lambda match: f"${match.group(1).strip()}$", text, flags=re.DOTALL)
    return text


def extract_lstlisting_language(option_text: str | None) -> str:
    if not option_text:
        return ""
    match = re.search(r"language\s*=\s*([A-Za-z0-9_+-]+)", option_text, flags=re.IGNORECASE)
    return match.group(1).lower() if match else ""


def convert_tex_code_block(env_name: str, title: str | None, inner: str) -> str:
    language = ""
    if env_name == "minted":
        language = (title or "").strip().lower()
    elif env_name == "lstlisting":
        language = extract_lstlisting_language(title)

    fence = f"```{language}" if language else "```"
    body = inner.strip("\n")
    return f"\n{fence}\n{body}\n```\n"


def convert_tex_headings(fragment: str) -> str:
    for command, prefix in HEADING_TO_MD.items():
        pattern = re.compile(
            rf"(?m)^\s*\\{command}\*?\{{([^{{}}]+)\}}\s*$"
        )
        fragment = pattern.sub(lambda match: f"{prefix} {match.group(1).strip()}", fragment)
    return fragment


def quote_markdown_block(header: str, body: str) -> str:
    lines = [f"> {header}"]
    if body:
        normalized_body_lines = dedent_lines(body.splitlines())
        for line in normalized_body_lines:
            stripped_line = line.lstrip()
            lines.append(">" if not stripped_line else f"> {stripped_line}")
    return "\n".join(lines)


def split_tex_list_items(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    nested_lists = 0

    for line in text.splitlines():
        stripped = line.strip()

        if LIST_BEGIN_RE.fullmatch(stripped):
            nested_lists += 1
        elif LIST_END_RE.fullmatch(stripped):
            nested_lists = max(0, nested_lists - 1)

        item_match = re.match(r"^\s*\\item(?:\s+(.*))?$", line)
        if item_match and nested_lists == 0:
            if current:
                items.append("\n".join(current).rstrip())
            first_line = item_match.group(1) or ""
            current = [first_line]
        else:
            current.append(line)

    if current:
        items.append("\n".join(current).rstrip())

    return [item for item in items if item.strip()]


def format_md_list_item(marker: str, body: str, level: int) -> str:
    indent = "  " * level
    continuation = indent + "  "
    lines = body.splitlines() if body else [""]

    first = lines[0].strip()
    result = [f"{indent}{marker}{first}" if first else f"{indent}{marker.strip()}"]
    for line in lines[1:]:
        result.append(continuation if not line.strip() else f"{continuation}{line}")
    return "\n".join(result)


def convert_tex_list(text: str, ordered: bool, level: int) -> str:
    items = split_tex_list_items(text)
    rendered: list[str] = []

    for index, item in enumerate(items, start=1):
        marker = f"{index}. " if ordered else "- "
        rendered.append(format_md_list_item(marker, convert_tex_fragment(item, level + 1).strip("\n"), level))

    return "\n".join(rendered)


def convert_tex_environment(env_name: str, title: str | None, inner: str, level: int) -> str:
    if env_name in {"itemize", "enumerate"}:
        return convert_tex_list(inner, ordered=(env_name == "enumerate"), level=level)

    if env_name in CODE_ENV_NAMES:
        return convert_tex_code_block(env_name, title, inner)

    if env_name in THEOREM_DISPLAY_NAMES:
        header = THEOREM_DISPLAY_NAMES[env_name]
        if title:
            header = f"{header}: {title.strip()}"
        body = convert_tex_fragment(inner, level).strip("\n")
        return f"\n{quote_markdown_block(header, body)}\n"

    return f"\\begin{{{env_name}}}{inner}\\end{{{env_name}}}"


def convert_tex_fragment(text: str, level: int = 0) -> str:
    text = convert_tex_headings(text)
    result: list[str] = []
    index = 0

    while index < len(text):
        begin_match = re.search(r"\\begin\{([a-zA-Z*]+)\}", text[index:])
        if not begin_match:
            result.append(text[index:])
            break

        begin_start = index + begin_match.start()
        begin_end = index + begin_match.end()
        env_name = begin_match.group(1)
        result.append(text[index:begin_start])

        cursor = begin_end
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1

        title: str | None = None
        option_text: str | None = None
        if env_name == "lstlisting":
            parsed_option, next_cursor = parse_bracket_argument(text, cursor)
            if parsed_option is not None:
                option_text = parsed_option
                cursor = next_cursor
        elif env_name == "minted":
            parsed_option, next_cursor = parse_bracket_argument(text, cursor)
            if parsed_option is not None:
                cursor = next_cursor
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            parsed_language, next_cursor = parse_bracket_argument(text, cursor)
            if parsed_language is not None:
                option_text = parsed_language
                cursor = next_cursor

        parsed_title, next_cursor = parse_bracket_argument(text, cursor)
        if parsed_title is not None and env_name in THEOREM_DISPLAY_NAMES:
            title = parsed_title
            cursor = next_cursor
        elif option_text is not None:
            title = option_text

        end_start, end_end = find_matching_end(text, env_name, cursor)
        if end_start == -1:
            result.append(text[begin_start:])
            break

        inner = text[cursor:end_start]
        result.append(convert_tex_environment(env_name, title, inner, level))
        index = end_end

    return "".join(result)


def tex_to_md(text: str) -> str:
    text = normalize_text(text)
    text = strip_tex_comments(text)
    text = convert_tex_images(text)
    text = convert_tex_bold(text)
    text = convert_tex_math(text)
    text = convert_tex_fragment(text)
    text = normalize_markdown_display_math_lines(text)
    return collapse_blank_lines(text)


def count_indent(line: str) -> int:
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def dedent_lines(lines: list[str]) -> list[str]:
    nonblank = [count_indent(line) for line in lines if line.strip()]
    if not nonblank:
        return ["" for _ in lines]

    margin = min(nonblank)
    return [line.expandtabs(4)[margin:] if line.strip() else "" for line in lines]


def convert_md_inline_math(text: str) -> str:
    return INLINE_MATH_RE.sub(lambda match: f"\\({match.group(1)}\\)", text)


def convert_md_bold(text: str) -> str:
    return re.sub(r"\*\*([^*\n]+)\*\*", lambda match: f"\\textbf{{{match.group(1)}}}", text)


def parse_html_attrs(attr_text: str) -> dict[str, str]:
    return {
        match.group("name").lower(): match.group("value")
        for match in HTML_ATTR_RE.finditer(attr_text)
    }


def css_width_to_latex(width_value: str) -> str | None:
    width = width_value.strip()
    percent_match = re.fullmatch(r"(\d*\.?\d+)%", width)
    if percent_match:
        factor = float(percent_match.group(1)) / 100
        factor_text = f"{factor:.4f}".rstrip("0").rstrip(".")
        if factor_text == "1":
            return r"\textwidth"
        return rf"{factor_text}\textwidth"

    if re.fullmatch(r"\d*\.?\d+(cm|mm|in|pt|pc|em|rem|ex|ch)", width):
        return width

    return None


def extract_width_from_style(style_value: str) -> str | None:
    for declaration in style_value.split(";"):
        if ":" not in declaration:
            continue
        key, value = declaration.split(":", 1)
        if key.strip().lower() == "width":
            return value.strip()
    return None


def build_includegraphics(path: str, width_value: str | None = None) -> str:
    if width_value:
        return f"\\includegraphics[width={width_value}]{{{path}}}"
    return f"\\includegraphics{{{path}}}"


def convert_md_image(line: str) -> str | None:
    match = MD_IMAGE_RE.match(line.strip())
    if match:
        return build_includegraphics(match.group('path').strip())

    html_match = HTML_IMAGE_RE.match(line.strip())
    if not html_match:
        return None

    attrs = parse_html_attrs(html_match.group("attrs"))
    image_path = attrs.get("src", "").strip()
    if not image_path:
        return None

    width_value = attrs.get("data-latex-width")
    if not width_value:
        if "width" in attrs:
            width_value = css_width_to_latex(attrs["width"])
        elif "style" in attrs:
            css_width = extract_width_from_style(attrs["style"])
            if css_width:
                width_value = css_width_to_latex(css_width)

    return build_includegraphics(image_path, width_value=width_value)


def convert_md_display_math_block(body: str) -> str:
    stripped = strip_outer_blank_lines(body)
    if "&" in stripped or "\\\\" in stripped:
        return f"\\begin{{align*}}\n{stripped}\n\\end{{align*}}"
    return f"\\[\n{stripped}\n\\]"


def parse_quote_header(line: str) -> tuple[str | None, str | None]:
    stripped = line.strip()
    match = re.match(
        r"^(theorem|definition|proposition|corollary|lemma|example|proof|solution|remark|note|exercise|problem)(?:\s*[:\-]\s*(.+)|\s*\((.+)\))?$",
        stripped,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None

    env_name = DISPLAY_NAME_TO_ENV[match.group(1).lower()]
    title = match.group(2) or match.group(3)
    return env_name, title.strip() if title else None


def convert_md_quote_block(lines: list[str]) -> str:
    raw_lines: list[str] = []
    for line in lines:
        match = BLOCKQUOTE_RE.match(line)
        raw_lines.append(match.group(1) if match else line)

    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    if not raw_lines:
        return ""

    env_name, title = parse_quote_header(raw_lines[0])
    if env_name is None:
        return "\n".join(raw_lines)

    body = convert_md_fragment("\n".join(raw_lines[1:])).strip("\n")
    if title:
        if env_name in {"proof", "solution"}:
            return f"\\begin{{{env_name}}}[{title}]\n{body}\n\\end{{{env_name}}}"
        return f"\\begin{{{env_name}}}{{{title}}}\n{body}\n\\end{{{env_name}}}"

    return f"\\begin{{{env_name}}}\n{body}\n\\end{{{env_name}}}"


def collect_quote_block(lines: list[str], start: int) -> tuple[list[str], int]:
    block: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if BLOCKQUOTE_RE.match(line):
            block.append(line)
            index += 1
            continue
        break
    return block, index


def collect_display_math_block(lines: list[str], start: int) -> tuple[str, int]:
    line = lines[start].strip()
    if line != "$$":
        body = line.removeprefix("$$").removesuffix("$$").strip()
        return body, start + 1

    body_lines: list[str] = []
    index = start + 1
    while index < len(lines):
        if lines[index].strip() == "$$":
            return "\n".join(body_lines), index + 1
        body_lines.append(lines[index])
        index += 1
    return "\n".join(body_lines), index


def collect_list_block(lines: list[str], start: int) -> tuple[list[str], int]:
    block: list[str] = []
    base_indent = count_indent(lines[start])
    index = start

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            next_index = index + 1
            if next_index < len(lines) and (MD_LIST_RE.match(lines[next_index]) or count_indent(lines[next_index]) > base_indent):
                block.append(line)
                index += 1
                continue
            break

        if MD_LIST_RE.match(line) or count_indent(line) > base_indent:
            block.append(line)
            index += 1
            continue
        break

    return block, index


def collect_fenced_code_block(lines: list[str], start: int) -> tuple[str, str, int]:
    opening = FENCE_RE.match(lines[start].strip())
    language = opening.group("lang") if opening else ""
    body_lines: list[str] = []
    index = start + 1
    while index < len(lines):
        if lines[index].strip() == "```":
            return language, "\n".join(body_lines), index + 1
        body_lines.append(lines[index])
        index += 1
    return language, "\n".join(body_lines), index


def convert_md_code_block(language: str, body: str) -> str:
    _ = language
    stripped_body = body.strip("\n")
    return f"\\begin{{verbatim}}\n{stripped_body}\n\\end{{verbatim}}"


def convert_md_list_block(lines: list[str]) -> str:
    if not lines:
        return ""

    first_match = MD_LIST_RE.match(lines[0])
    if not first_match:
        return "\n".join(lines)

    base_indent = count_indent(lines[0])
    ordered = bool(re.match(r"\d+[.)]$", first_match.group("marker")))
    env_name = "enumerate" if ordered else "itemize"
    items: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        match = MD_LIST_RE.match(line)
        if match and count_indent(line) == base_indent:
            if current:
                items.append(current)
            current = [match.group("content")]
            continue
        current.append(line)

    if current:
        items.append(current)

    rendered = [f"\\begin{{{env_name}}}"]
    for item_lines in items:
        first_line = item_lines[0]
        rest = dedent_lines(item_lines[1:])
        item_body = "\n".join([first_line] + rest).strip("\n")
        converted = convert_md_fragment(item_body).strip("\n")
        converted_lines = converted.splitlines() if converted else []

        if not converted_lines:
            rendered.append("\\item")
            continue

        if converted_lines[0].startswith("\\begin{"):
            rendered.append("\\item")
            rendered.extend(converted_lines)
        else:
            rendered.append(f"\\item {converted_lines[0]}")
            rendered.extend(converted_lines[1:])

    rendered.append(f"\\end{{{env_name}}}")
    return "\n".join(rendered)


def convert_md_heading(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.*)$", line)
    if not match:
        return None

    level = len(match.group(1))
    command = MD_TO_HEADING[level]
    title = match.group(2).strip()
    return f"\\{command}{{{title}}}"


def convert_md_fragment(text: str) -> str:
    lines = normalize_text(text).split("\n")
    result: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        heading = convert_md_heading(line)
        if heading is not None:
            result.append(heading)
            index += 1
            continue

        if FENCE_RE.match(line.strip()):
            language, body, index = collect_fenced_code_block(lines, index)
            result.append(convert_md_code_block(language, body))
            continue

        if line.strip().startswith("$$") and line.strip().endswith("$$") and line.strip() != "$$":
            body, index = collect_display_math_block(lines, index)
            result.append(convert_md_display_math_block(body))
            continue

        if line.strip() == "$$":
            body, index = collect_display_math_block(lines, index)
            result.append(convert_md_display_math_block(body))
            continue

        if BLOCKQUOTE_RE.match(line):
            block, index = collect_quote_block(lines, index)
            result.append(convert_md_quote_block(block))
            continue

        converted_image = convert_md_image(line)
        if converted_image is not None:
            result.append(converted_image)
            index += 1
            continue

        if MD_LIST_RE.match(line):
            block, index = collect_list_block(lines, index)
            result.append(convert_md_list_block(block))
            continue

        result.append(convert_md_bold(convert_md_inline_math(line)))
        index += 1

    return "\n".join(result)


def md_to_tex(text: str) -> str:
    text = convert_md_fragment(text)
    return collapse_blank_lines(text)


def infer_direction(input_path: Path) -> str:
    suffix = input_path.suffix.lower()
    if suffix == ".tex":
        return "tex-to-md"
    if suffix in {".md", ".markdown"}:
        return "md-to-tex"
    raise ValueError("无法根据输入文件扩展名推断方向, 请显式传入 --direction")


def normalize_stem(stem: str) -> str:
    filename = Path(stem).name
    lower_name = filename.lower()
    for suffix in (".tex", ".md", ".markdown"):
        if lower_name.endswith(suffix):
            filename = filename[: -len(suffix)]
            break
    filename = filename.strip()
    if not filename:
        raise ValueError("章节名不能为空。示例: make tex 01-basic-combinatorics")
    return filename


def infer_direction_from_stem(chapter_dir: Path, stem: str) -> str:
    tex_path = chapter_dir / f"{stem}.tex"
    md_path = chapter_dir / f"{stem}.md"

    tex_exists = tex_path.exists()
    md_exists = md_path.exists()

    if tex_exists and not md_exists:
        return "tex-to-md"
    if md_exists and not tex_exists:
        return "md-to-tex"
    if tex_exists and md_exists:
        raise ValueError("chapters/ 中同时存在同名 .tex 和 .md, 请显式传入 --direction")

    raise FileNotFoundError(f"在 {chapter_dir} 中找不到 {stem}.tex 或 {stem}.md")


def resolve_chapter_paths(chapter_dir: Path, stem: str, direction: str) -> tuple[Path, Path]:
    normalized_stem = normalize_stem(stem)
    if direction == "tex-to-md":
        return chapter_dir / f"{normalized_stem}.tex", chapter_dir / f"{normalized_stem}.md"
    if direction == "md-to-tex":
        return chapter_dir / f"{normalized_stem}.md", chapter_dir / f"{normalized_stem}.tex"
    raise ValueError(f"不支持的转换方向: {direction}")


def build_output_path(input_path: Path, direction: str) -> Path:
    if direction == "tex-to-md":
        return input_path.with_suffix(".md")
    return input_path.with_suffix(".tex")


def convert_text(text: str, direction: str) -> str:
    if direction == "tex-to-md":
        return tex_to_md(text)
    if direction == "md-to-tex":
        return md_to_tex(text)
    raise ValueError(f"不支持的转换方向: {direction}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert note files between LaTeX and Markdown."
    )
    parser.add_argument("input", nargs="?", help="Input .tex or .md file")
    parser.add_argument("output", nargs="?", help="Output file path")
    parser.add_argument(
        "--stem",
        help="Chapter stem to convert inside chapters/. Example: 01-basic-combinatorics",
    )
    parser.add_argument(
        "--chapter-dir",
        default="chapters",
        help="Directory used together with --stem. Defaults to chapters/.",
    )
    parser.add_argument(
        "--direction",
        choices=["tex-to-md", "md-to-tex", "auto"],
        default="auto",
        help="Conversion direction. Defaults to auto-infer from input suffix.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.stem:
        chapter_dir = Path(args.chapter_dir)
        direction = (
            infer_direction_from_stem(chapter_dir, normalize_stem(args.stem))
            if args.direction == "auto"
            else args.direction
        )
        input_path, default_output_path = resolve_chapter_paths(chapter_dir, args.stem, direction)
        output_path = Path(args.output) if args.output else default_output_path
    else:
        if not args.input:
            raise ValueError("需要传入 input 文件，或使用 --stem 在 chapters/ 中按章节名转换")
        input_path = Path(args.input)
        direction = infer_direction(input_path) if args.direction == "auto" else args.direction
        output_path = Path(args.output) if args.output else build_output_path(input_path, direction)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    converted = convert_text(input_path.read_text(encoding="utf-8"), direction)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(converted, encoding="utf-8")
    print(f"Converted {input_path} -> {output_path} ({direction})")


if __name__ == "__main__":
    main()