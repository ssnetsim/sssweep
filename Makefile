PYPKG := sssweep

.SUFFIXES:
.PHONY: help install clean

help:
	@echo "options are: install clean"

install:
	python3 setup.py install --user

clean:
	rm -rf build dist $(PYPKG).egg-info $(PYPKG)/*.pyc $(PYPKG)/__pycache__

count:
	@wc $(PYPKG)/*.py | sort -n -k1
	@echo "files : "$(shell echo $(PYPKG)/*.py | wc -w)
	@echo "commits : "$(shell git rev-list HEAD --count) 
