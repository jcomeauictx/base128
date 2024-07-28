SCRIPTS := $(wildcard *.py)
PYTHON ?= python3
PYLINT ?= $(shell which pylint pylint3 true 2>/dev/null | head -n 1)
%.doctest: %.py
	$(PYTHON) -m doctest $<
doctest: $(SCRIPTS:.py=.doctest)
%.pylint: %.py
	$(PYLINT) $<
pylint: $(SCRIPTS:.py=.pylint)
