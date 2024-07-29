SCRIPTS := $(wildcard *.py)
PYTHON ?= python3
PYLINT ?= $(shell which pylint pylint3 true 2>/dev/null | head -n 1)
PROFILE_LOG := profile.raw.log
PROFILE_TXT := profile.txt.log
%.doctest: %.py
	$(PYTHON) -m doctest $< 2>&1 | less
doctest: $(SCRIPTS:.py=.doctest)
%.pylint: %.py
	$(PYLINT) $<
pylint: $(SCRIPTS:.py=.pylint)
profile: base128.$(PROFILE_TXT)
%.$(PROFILE_LOG): %.py
	cat /tmp/bash.b128 | $(PYTHON) -OO -c "import cProfile; \
	 from $* import dispatch; \
         cProfile.run(\"dispatch('decode', None, '/tmp/bash.d128')\", '$@')"
%.$(PROFILE_TXT): %.$(PROFILE_LOG)
	$(PYTHON) -OO -c "import pstats; p = pstats.Stats('$<'); \
	 p.sort_stats('cumulative').print_stats()" | tee $@
clean:
	rm -f dummy *.log
distclean:
	rm -rf dummy __pycache__
