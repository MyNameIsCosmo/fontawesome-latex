all: run
.PHONY: all run debug pdf display clean release env

run:
	python3 fontawesome-latex.py

debug:
	python3 fontawesome-latex.py --debug

xelatex pdf:
	cd output && \
	xelatex fontawesome.tex

xdg-open display:
	xdg-open output/fontawesome.pdf

env venv:
	virtualenv --python=python3 --always-copy .env && \
	. .env/bin/activate && \
	pip install -r requirements.txt
	echo "Virtual environment created!"
	echo ""
	echo "Type:"
	echo "    source .env/bin/activate"

release:
	-rm release.zip
	-rm -rf output/*.aux
	-rm -rf output/*.log
	cd release && \
	zip ../release.zip README.md
	cd output && \
	zip ../release.zip ./* ./fonts/*

clean:
	-rm -rf tmp
	-rm -rf output
	-rm texput.log

clean-env:
	rm -rf .env

$(V).SILENT:
