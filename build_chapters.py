#!/usr/bin/env python3
"""
为 main.tex 中的每个 chapter 生成独立的 PDF 文件
自动计算正确的章节编号
"""
import re
import os
import subprocess
from pathlib import Path


def extract_all_inputs(tex_file):
    """从 main.tex 中提取所有 input 行（包括注释掉的），保持顺序。
    返回 list of (chapter_path, is_commented)
    """
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    all_inputs = []
    for line in content.split('\n'):
        stripped = line.strip()
        # 匹配注释和非注释的 \input 命令
        match = re.match(r'^(%\s*)?\\input\{([^}]+)\}', stripped)
        if match:
            is_commented = match.group(1) is not None
            chapter_path = match.group(2)
            all_inputs.append((chapter_path, is_commented))

    return all_inputs


def detect_chapter_type(chapter_tex_file):
    """检测章节文件使用的是 \\chapter{} 还是 \\chapter*{}
    返回 'numbered' 或 'unnumbered'
    """
    with open(chapter_tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找第一个 \chapter 命令
    match = re.search(r'\\chapter(\*?)\s*[\[{]', content)
    if match:
        if match.group(1) == '*':
            return 'unnumbered'
        else:
            return 'numbered'

    # 默认当作 numbered
    return 'numbered'


def compute_chapter_numbers(all_inputs, project_root):
    """根据所有 input 的顺序，计算每个章节在编译时的 chapter 计数器值。
    返回 dict: chapter_path -> chapter_counter_before（即该章节编译前应设置的计数器值）
    """
    chapter_counter = 0
    chapter_numbers = {}

    for chapter_path, _is_commented in all_inputs:
        # Handle both with and without .tex extension
        if not chapter_path.endswith('.tex'):
            tex_file = project_root / (chapter_path + '.tex')
        else:
            tex_file = project_root / chapter_path
        if not tex_file.exists():
            continue

        ch_type = detect_chapter_type(tex_file)
        if ch_type == 'numbered':
            # \chapter{} 会让计数器 +1，所以编译前计数器应该是当前值
            chapter_numbers[chapter_path] = chapter_counter
            chapter_counter += 1
        else:
            # \chapter*{} 不影响计数器
            chapter_numbers[chapter_path] = chapter_counter

    return chapter_numbers


def create_chapter_main(original_main, chapter_path, output_dir, project_root, chapter_counter):
    """为单个 chapter 创建临时的主文件，设置正确的章节计数器"""
    chapter_name = Path(chapter_path).stem

    # 读取原始主文件
    with open(original_main, 'r', encoding='utf-8') as f:
        main_content = f.read()

    # 找到 \begin{document}
    doc_start = main_content.find('\\begin{document}')
    if doc_start == -1:
        raise ValueError("找不到 \\begin{document}")

    chapter_path_obj = Path(chapter_path)

    # 构建新的内容
    preamble = main_content[:doc_start + len('\\begin{document}')]
    new_content = preamble + '\n'
    new_content += '\\mainmatter\n'
    # 设置正确的 chapter 计数器
    new_content += f'\\setcounter{{chapter}}{{{chapter_counter}}}\n'
    new_content += f'\\input{{{chapter_path_obj.as_posix()}}}\n'
    new_content += '\\end{document}'

    # 写入临时文件
    output_file = output_dir / f'{chapter_name}_main.tex'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return output_file


def compile_tex(tex_file, output_dir, project_root):
    """编译 LaTeX 文件生成 PDF"""
    tex_file = Path(tex_file)
    output_dir = Path(output_dir)
    project_root = Path(project_root)

    # 检查 lualatex 是否可用
    try:
        subprocess.run(['lualatex', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到 lualatex。请安装 TeX Live。")
        return None

    # 从项目根目录编译
    original_dir = os.getcwd()
    try:
        os.chdir(project_root)

        if tex_file.is_absolute():
            rel_tex_file = tex_file.relative_to(project_root)
        else:
            rel_tex_file = tex_file

        cmd = ['lualatex', '-interaction=batchmode',
               f'-output-directory={output_dir}', str(rel_tex_file)]

        # 编译两次（处理交叉引用）
        result = subprocess.run(cmd, capture_output=True, text=True)
        subprocess.run(cmd, capture_output=True, text=True)

        # 检查 PDF 是否生成
        pdf_file = output_dir / tex_file.with_suffix('.pdf').name
        if pdf_file.exists():
            return pdf_file
        else:
            if result.returncode != 0 and result.stderr:
                print(f"错误: {result.stderr[:200]}")
            return None

    finally:
        os.chdir(original_dir)


def main():
    project_root = Path(__file__).parent
    main_tex = project_root / 'main.tex'
    build_dir = project_root / 'build'
    build_dir.mkdir(exist_ok=True)

    # 提取所有 input 命令（包括注释掉的）
    all_inputs = extract_all_inputs(main_tex)

    if not all_inputs:
        print("未找到任何 \\input 命令")
        return

    # 计算每个章节的正确编号
    chapter_numbers = compute_chapter_numbers(all_inputs, project_root)

    # 筛选出未注释的章节
    active_chapters = [(path, commented) for path, commented in all_inputs if not commented]

    if not active_chapters:
        print("未找到任何未注释的 \\input 命令")
        return

    print(f"找到 {len(active_chapters)} 个章节:")
    for ch_path, _ in active_chapters:
        # Handle both with and without .tex extension
        if not ch_path.endswith('.tex'):
            tex_file = project_root / (ch_path + '.tex')
            ch_name = Path(ch_path).stem
        else:
            tex_file = project_root / ch_path
            ch_name = Path(ch_path).stem
        ch_type = detect_chapter_type(tex_file) if tex_file.exists() else '?'
        counter = chapter_numbers.get(ch_path, 0)
        if ch_type == 'numbered':
            print(f"  - {ch_name} (Chapter {counter + 1})")
        else:
            print(f"  - {ch_name} (unnumbered)")

    print("\n开始生成独立的 PDF...")

    generated_pdfs = []
    for chapter_path, _ in active_chapters:
        # Normalize path for lookup (ensure it has .tex)
        if not chapter_path.endswith('.tex'):
            normalized_path = chapter_path
            chapter_path_with_tex = chapter_path + '.tex'
        else:
            normalized_path = chapter_path[:-4]  # Remove .tex for stem
            chapter_path_with_tex = chapter_path
        
        chapter_name = Path(chapter_path).stem
        counter = chapter_numbers.get(chapter_path, 0)

        try:
            temp_main = create_chapter_main(
                main_tex, chapter_path, build_dir, project_root, counter)

            pdf_file = compile_tex(temp_main, build_dir, project_root)
            if pdf_file:
                final_pdf = project_root / f'{chapter_name}.pdf'
                if pdf_file != final_pdf:
                    pdf_file.rename(final_pdf)
                generated_pdfs.append(final_pdf)
                print(f"  ✓ 生成: {final_pdf.name}")
            else:
                print(f"  ✗ 失败: {chapter_name}")

        except Exception as e:
            print(f"  ✗ 错误: {chapter_name} - {e}")

    print(f"\n完成! 生成了 {len(generated_pdfs)} 个 PDF 文件:")
    for pdf in generated_pdfs:
        print(f"  - {pdf}")


if __name__ == '__main__':
    main()
