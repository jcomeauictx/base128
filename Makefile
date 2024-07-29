SCRIPTS := $(wildcard *.py)
PYTHON ?= python3
PYLINT ?= $(shell which pylint pylint3 true 2>/dev/null | head -n 1)
%.doctest: %.py
	$(PYTHON) -m doctest $< 2>&1 | less
doctest: $(SCRIPTS:.py=.doctest)
%.pylint: %.py
	$(PYLINT) $<
pylint: $(SCRIPTS:.py=.pylint)
profile: base128.profile
%.profile: %.py
	cat /tmp/bash.b128 | python3 -OO -c "import cProfile; \
	 from $* import dispatch; \
         cProfile.run(\"dispatch('decode', None, '/tmp/bash.d128')\", \
	  '/tmp/base128.profile.log')"
