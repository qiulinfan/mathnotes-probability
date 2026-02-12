# 本地 compile & build Latex project

从 0 开始.

## 安装 Tex Live / MacTex

- windows: https://tug.org/texlive/ -> install on Windows -> [install-tl-windows.exe](https://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe).
- mac: https://tug.org/mactex/ -> [**MacTeX Download**](https://tug.org/mactex/mactex-download.html).

- linux, wsl: 

这个东西会安装很久 (windows $\approx$ 2h, mac $\approx$ 1h, linux $\approx$ 0.5h). 内容是 latex 全家桶. 

可以用

```bash
tlmgr info scheme-full
```

来验证装的是不是 full version.

安装包含了:

- 几乎所有 LaTeX 宏包 (几千个)
- 语言支持 (中文, 日文, 韩文, 阿拉伯文等)
- 引擎: pdfTeX, XeTeX, LuaTeX, MetaPost, BibTeX, Biber
- 各种字体
- 文档, 示例, 索引文件

另一种选择是 MikTex. 但是我觉得不如安装这个完整的 Texlive. 这相当于轮椅, 后续用 VSCode 的 Latex Workshop 的时候只需要配置 .vscode/settings.json 就可以直接用了. 如果用 MikTex 的话还得配置, 比如安装 strawberry perl, 安装各种小 packages 等.
(既然有免费的全家桶那就用呗



## VSCode Latex workshop.

VSCode 最好的 Latex 支持. 

不用配置文件路径, 它能找到我们的  texlive 安装的引擎和 packages



配置文件 settings.json: lualatex, 生成文件放入 build/, 自动 compile

## 项目结构

```
mathnotes-probability/
├── main.tex              # 主 LaTeX 文件
├── chapters/             # 章节文件目录
│   ├── ch01-*.tex
│   ├── ch02-*.tex
│   └── ...
├── build/                # 编译临时文件目录（自动清理）
├── build_chapters.py     # 章节 PDF 生成脚本
├── Makefile              # 编译配置
└── *.pdf                 # 生成的 PDF 文件（在根目录）
```

## 编译方式

### 使用 Makefile（推荐）

项目使用 `lualatex` 作为编译引擎，支持以下命令：

```bash
# 生成所有章节的独立 PDF
make chapters

# 生成主 PDF（包含所有章节）
make main

# 生成所有 PDF（默认生成章节 PDF）
make all

# 清理临时文件
make clean

# 完全清理（包括所有 PDF）
make clean-all
```

**特点：**
- 编译完成后自动清理 `build/` 目录中的临时文件
- PDF 文件输出到项目根目录，便于访问
- `build/` 目录只保留编译过程中的临时文件

### 章节独立 PDF 生成

`build_chapters.py` 脚本会自动解析 `main.tex` 中所有**未注释**的 `\input{chapters/xxx}` 命令，为每个章节生成独立的 PDF 文件。

**工作原理：**
1. 解析 `main.tex` 找出所有 `\input` 命令
2. 为每个章节创建临时主文件
3. 使用 `lualatex` 编译生成独立 PDF
4. 将 PDF 移动到项目根目录
5. 自动清理临时文件

**示例：**
如果 `main.tex` 中有：
```latex
\input{chapters/hw02}
```

运行 `make chapters` 后会生成 `hw02.pdf` 在项目根目录。

### 直接使用 Python 脚本

```bash
python3 build_chapters.py
```

## 文件组织

- **PDF 文件**：生成在项目根目录（如 `main.pdf`, `hw02.pdf`）
- **临时文件**：保存在 `build/` 目录，编译完成后自动清理
- **源文件**：`main.tex` 和 `chapters/*.tex` 保持不变
- **图片资源**：存放在 `assets/` 目录

## ElegantBook 使用指南

本项目使用 **ElegantBook** 文档类，提供了丰富的数学环境和代码块支持。

### 数学环境

ElegantBook 提供了多种数学环境，支持中文和英文：

**定理类环境：**
```latex
\begin{definition}[可选标题]
定义内容
\end{definition}

\begin{theorem}[可选标题]
定理内容
\end{theorem}

\begin{lemma}[可选标题]
引理内容
\end{lemma}

\begin{proposition}[可选标题]
命题内容
\end{proposition}

\begin{corollary}[可选标题]
推论内容
\end{corollary}
```

**示例和练习：**
```latex
\begin{example}[可选标题]
示例内容
\end{example}

\begin{exercise}[可选标题]
练习内容
\end{exercise}

\begin{problem}[可选标题]
问题内容
\end{problem}
```

**证明和解答：**
```latex
\begin{proof}
证明内容
\end{proof}

\begin{solution}
解答内容
\end{solution}
```

**其他环境：**
```latex
\begin{note}
注意内容
\end{note}

\begin{remark}
备注内容
\end{remark}

\begin{assumption}
假设内容
\end{assumption}

\begin{conclusion}
结论内容
\end{conclusion}
```

### 代码块

项目支持多种代码块环境，带有语法高亮：

**Python 代码：**
```latex
\begin{python}[caption={代码标题}, label=code:label-name]
import numpy as np
def example():
    return "Hello, World!"
\end{python}
```

**C++ 代码：**
```latex
\begin{cpp}[caption={代码标题}, label=code:label-name]
#include <iostream>
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
\end{cpp}
```

**终端/命令输出：**
```latex
\begin{terminal}[caption={输出标题}]
$ make chapters
找到 1 个章节:
  - chapters/hw02
\end{terminal}

% 或者使用 cmd 环境（等价）
\begin{cmd}[caption={输出标题}]
命令输出内容
\end{cmd}
```

**纯文本：**
```latex
\begin{txt}[caption={文本标题}]
纯文本内容，无语法高亮
\end{txt}
```

**内联代码：**
```latex
使用 \pythoninline{print("Hello")} 来显示内联 Python 代码。

使用 \cppinline{std::cout} 来显示内联 C++ 代码。
```

### 图片插入

项目提供了两种图片插入方式：

**方式 1：带标题和标签的图片（推荐）**
```latex
\insertpic[width=0.8\textwidth]{assets/image.png}{图片标题}{fig:label-name}
```

参数说明：
- 第一个可选参数：图片尺寸选项（如 `width=0.8\textwidth`, `height=5cm` 等）
- 第二个参数：图片路径（相对于项目根目录）
- 第三个参数：图片标题
- 第四个参数：图片标签（用于引用）

**方式 2：简单居中图片**
```latex
\pic[0.8]{assets/image.png}
```

参数说明：
- 第一个可选参数：图片宽度比例（默认 1，即 `\textwidth`）
- 第二个参数：图片路径

**图片路径搜索：**
LaTeX 会自动在以下目录中搜索图片：
- `./figure/`, `./figures/`
- `./image/`, `./images/`
- `./graphics/`, `./graphic/`
- `./pictures/`, `./picture/`
- `./assets/`（项目推荐使用）

**引用图片：**
```latex
如图 \ref{fig:label-name} 所示...
```

### 文档类配置

在 `main.tex` 中，文档类配置为：
```latex
\documentclass[lang=cn,11pt,chinesefont=nofont]{elegantbook}
```

- `lang=cn`：中文模式
- `11pt`：字体大小
- `chinesefont=nofont`：不指定中文字体（使用系统默认）

## 注意事项

1. 只有**未注释**的 `\input` 命令会被处理
2. 需要 Python 3 和 `lualatex` 支持
3. 编译过程静默运行，只显示关键信息
4. 如果编译失败，检查 `build/*.log` 文件查看详细错误信息



