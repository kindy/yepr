
yepr/yep_grako.py: yepr/grammar/yep.grako
	grako $< > $@ && perl -p -i'.fix' -e's/(from __future__ import.*\n)/\1from builtins import object\n/' $@


test: yepr/yep_grako.py
	nosetests

ci-test:
	nosetests --with-coverage --cover-package=yepr

