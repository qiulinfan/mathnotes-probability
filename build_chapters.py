#!/usr/bin/env python3
"""
为 main.tex 中的每个 chapter 生成独立的 PDF 文件
"""
import re
import os
import subprocess
import tempfile
from pathlib import Path

def extract_input_commands(tex_file):
    """从 LaTeX 文件中提取所有的 input 命令"""
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配 \input{chapters/xxx} 或 % \input{chapters/xxx}
    pattern = r'(?:^|\n)\s*%?\s*\\input\{([^}]+)\}'
    matches = re.findall(pattern, content, re.MULTILINE)
    
    # 只保留未注释的 input 命令（不包含 %）
    inputs = []
    for line in content.split('\n'):
        stripped = line.strip()
        # 检查是否是未注释的 \input 命令
        if stripped.startswith('\\input{') and not stripped.startswith('%'):
            match = re.search(r'\\input\{([^}]+)\}', stripped)
            if match:
                inputs.append(match.group(1))
    
    return inputs

def create_chapter_main(original_main, chapter_path, output_dir, project_root):
    """为单个 chapter 创建临时的主文件"""
    chapter_name = Path(chapter_path).stem
    
    # 读取原始主文件
    with open(original_main, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    # 创建新的主文件内容，只包含指定的 chapter
    # 找到 \begin{document} 之后的内容
    doc_start = main_content.find('\\begin{document}')
    if doc_start == -1:
        raise ValueError("找不到 \\begin{document}")
    
    # 找到 \end{document}
    doc_end = main_content.find('\\end{document}')
    if doc_end == -1:
        raise ValueError("找不到 \\end{document}")
    
    # 使用原始路径（相对于项目根目录）
    # 因为我们会从项目根目录编译
    chapter_path_obj = Path(chapter_path)
    
    # 构建新的内容
    preamble = main_content[:doc_start + len('\\begin{document}')]
    # 移除 frontmatter 和 tableofcontents（对于单个 chapter 可能不需要）
    # 但保留它们以便保持格式一致
    new_content = preamble + '\n'
    new_content += '\\mainmatter\n'
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
        print("错误: 未找到 lualatex。请安装 TeX Live 或 MiKTeX。")
        print("在 Ubuntu/Debian 上: sudo apt-get install texlive-luatex")
        return None
    
    # 从项目根目录编译，这样能找到 elegantbook.cls 等文件
    # 但输出到 build 目录
    original_dir = os.getcwd()
    try:
        os.chdir(project_root)
        
        # 计算相对于项目根目录的 tex_file 路径
        if tex_file.is_absolute():
            rel_tex_file = tex_file.relative_to(project_root)
        else:
            rel_tex_file = tex_file
        
        # 运行 lualatex（可能需要多次编译以处理交叉引用）
        # 使用 -output-directory 指定输出目录，-interaction=batchmode 静默模式
        cmd = ['lualatex', '-interaction=batchmode',
               f'-output-directory={output_dir}', str(rel_tex_file)]
        
        # 第一次编译（静默模式）
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 第二次编译（处理交叉引用，静默模式）
        subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查 PDF 是否生成
        pdf_file = output_dir / tex_file.with_suffix('.pdf').name
        if pdf_file.exists():
            return pdf_file
        else:
            # 如果失败，显示错误信息
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
    
    # 提取所有的 input 命令
    chapters = extract_input_commands(main_tex)
    
    if not chapters:
        print("未找到任何 \\input 命令")
        return
    
    if not chapters:
        print("未找到任何 \\input 命令")
        return
    
    print(f"找到 {len(chapters)} 个章节:")
    for ch in chapters:
        print(f"  - {ch}")
    
    print("\n开始生成独立的 PDF...")
    
    generated_pdfs = []
    for chapter_path in chapters:
        chapter_name = Path(chapter_path).stem
        
        try:
            # 创建临时主文件
            temp_main = create_chapter_main(main_tex, chapter_path, build_dir, project_root)
            
            # 编译
            pdf_file = compile_tex(temp_main, build_dir, project_root)
            if pdf_file:
                # 将 PDF 移动到项目根目录
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
