
yepr/yep_grako.py: yepr/grammar/yep.grako
	grako $< > $@


test: yepr/yep_grako.py
	nosetests

ci-test:
	nosetests

