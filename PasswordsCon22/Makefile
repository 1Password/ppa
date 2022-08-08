LATEXMK_RC= latexmkrc

%.pdf: %.tex
	latexmk -r $(LATEXMK_RC) $(LATEXMK_OPTIONS) $<

all: pwcon22.pdf
