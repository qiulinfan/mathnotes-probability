.PHONY: all main chapters docs deploy depoly clean

PYTHON := python3
ifeq ($(OS),Windows_NT)
PYTHON := python
endif

# 默认目标：生成主 PDF 和所有章节 PDF
all: chapters
	@$(MAKE) -s clean

# 生成主 PDF
main:
	@lualatex -interaction=batchmode -output-directory=build main.tex > /dev/null 2>&1 || true
	@lualatex -interaction=batchmode -output-directory=build main.tex > /dev/null 2>&1 || true
	@mv build/main.pdf main.pdf 2>/dev/null || true
	@$(MAKE) -s clean

# 为每个章节生成独立的 PDF
chapters:
	@$(PYTHON) scripts/build_chapters.py
	@$(MAKE) -s clean

docs:
	@$(PYTHON) scripts/generate_docs_pages.py
	@$(PYTHON) scripts/generate_mkdocs_config.py

deploy:
	@mkdocs build
	@mkdocs gh-deploy --force --remote-branch gh-deploy

depoly: deploy


# 清理生成的文件
clean:
	-@rm -f build/*.aux build/*.log build/*.out build/*.toc build/*.fdb_latexmk build/*.fls build/*.synctex.gz
	-@rm -f build/*.bcf build/*.run.xml build/*.bbl build/*.blg
	-@rm -f build/*_main.tex

# 完全清理（包括 PDF）
clean-all: clean
	-@rm -f build/*.pdf *.pdf
