SCRIPTS := $(wildcard *.py)
PYTHON ?= python3
%.doctest: %.py
	$(PYTHON) -m doctest $<
doctest: $(SCRIPTS:.py=.doctest)
