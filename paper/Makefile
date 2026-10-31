.PHONY: all paper clean

all: paper

paper:
	latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex

clean:
	latexmk -C
	rm -f *.bbl *.synctex.gz
