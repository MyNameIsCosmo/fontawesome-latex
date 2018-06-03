all: run
.PHONY: all

run:
	python3 fontawesome-latex.py

debug:
	python3 fontawesome-latex.py --debug

xelatex pdf:
	cd output && \
	xelatex fontawesomefree.tex && \
	xelatex fontawesomefreesolid.tex && \
	xelatex fontawesomebrandsregular.tex

xdg-open display:
	xdg-open output/fontawesomefree.pdf && \
	xdg-open output/fontawesomefreesolid.pdf && \
	xdg-open output/fontawesomebrandsregular.pdf

env venv:
	virtualenv --python=python3 --always-copy .env && \
	. .env/bin/activate && \
	pip install -r requirements.txt
	echo "Virtual environment created!"
	echo ""
	echo "Type:"
	echo "    source .env/bin/activate"


clean:
	rm -rf tmp
	rm -rf output
	rm texput.log

clean-env:
	rm -rf .env

$(V).SILENT:
