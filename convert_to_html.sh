#!/bin/bash

# LaTeX 转 HTML 转换脚本
# 使用方法: ./convert_to_html.sh [input.tex] [output.html]

INPUT_FILE="${1:-main.tex}"
OUTPUT_FILE="${2:-output.html}"

# 检查 pandoc 是否安装
if ! command -v pandoc &> /dev/null; then
    echo "错误: pandoc 未安装"
    echo ""
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc"
    echo "  或者访问: https://pandoc.org/installing.html"
    exit 1
fi

echo "正在将 $INPUT_FILE 转换为 $OUTPUT_FILE ..."

# 使用 pandoc 转换
# --mathjax: 使用 MathJax 渲染数学公式
# --standalone: 生成完整的 HTML 文档
# --toc: 生成目录
# --number-sections: 给章节编号
pandoc "$INPUT_FILE" \
    --from=latex \
    --to=html5 \
    --mathjax \
    --standalone \
    --toc \
    --number-sections \
    --output="$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✓ 转换成功！输出文件: $OUTPUT_FILE"
    echo ""
    echo "提示: 如果数学公式显示不正常，可能需要:"
    echo "  1. 确保网络连接正常（MathJax 需要从 CDN 加载）"
    echo "  2. 或者使用 --katex 替代 --mathjax（需要安装 KaTeX）"
else
    echo "✗ 转换失败"
    exit 1
fi
