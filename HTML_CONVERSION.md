# LaTeX 转 HTML 指南

## 方法 1: 使用 Pandoc (推荐)

### 安装 Pandoc

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install pandoc
```

**或者从官网安装最新版本:**
```bash
# 下载 .deb 包
wget https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-1-amd64.deb
sudo dpkg -i pandoc-3.1.9-1-amd64.deb
```

### 使用方法

**方法 A: 使用提供的脚本**
```bash
./convert_to_html.sh main.tex output.html
```

**方法 B: 直接使用 pandoc 命令**
```bash
pandoc main.tex \
    --from=latex \
    --to=html5 \
    --mathjax \
    --standalone \
    --toc \
    --number-sections \
    --output=output.html
```

### 选项说明

- `--mathjax`: 使用 MathJax 渲染数学公式（需要网络连接）
- `--standalone`: 生成完整的 HTML 文档（包含 `<html>`, `<head>`, `<body>` 标签）
- `--toc`: 生成目录
- `--number-sections`: 给章节编号
- `--css=style.css`: 可以指定自定义 CSS 文件

### 离线使用（使用 KaTeX）

如果需要离线使用，可以使用 KaTeX 替代 MathJax:

```bash
pandoc main.tex \
    --from=latex \
    --to=html5 \
    --katex \
    --standalone \
    --toc \
    --output=output.html
```

注意: KaTeX 需要先下载相关文件，或者使用 CDN。

## 方法 2: 使用 tex4ht

### 安装
```bash
sudo apt-get install texlive-extra-utils
```

### 使用方法
```bash
htlatex main.tex "html,mathjax"
```

## 方法 3: 使用 LaTeX.js (在线/本地)

LaTeX.js 是一个纯 JavaScript 的 LaTeX 到 HTML 转换器，可以在浏览器中运行。

访问: https://latex.js.org/

## 注意事项

1. **中文支持**: Pandoc 对中文支持较好，但可能需要确保输入文件是 UTF-8 编码
2. **数学公式**: MathJax 需要网络连接，KaTeX 可以离线使用
3. **自定义样式**: 可以使用 `--css` 选项添加自定义 CSS
4. **复杂文档类**: 如果使用特殊的文档类（如 elegantbook），可能需要预处理或调整

## 常见问题

### 数学公式不显示
- 确保使用了 `--mathjax` 或 `--katex` 选项
- 检查网络连接（MathJax 需要从 CDN 加载）
- 尝试使用 KaTeX 替代

### 中文乱码
- 确保源文件是 UTF-8 编码
- 在 HTML 中添加 `<meta charset="UTF-8">`（pandoc 会自动添加）

### 样式问题
- 使用 `--css` 选项添加自定义样式
- 或者手动编辑生成的 HTML 文件
