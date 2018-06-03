run:
	python3 fontawesome-latex.py

debug:
	python3 fontawesome-latex.py --debug

xelatex:
	cd output && \
	xelatex fontawesomefree.tex && \
	xelatex fontawesomefreesolid.tex && \
	xelatex fontawesomebrandsregular.tex

xdg-open:
	xdg-open output/fontawesomefree.pdf && \
	xdg-open output/fontawesomefreesolid.pdf && \
	xdg-open output/fontawesomebrandsregular.pdf

clean:
	rm -rf tmp
	rm -rf output
	rm texput.log
