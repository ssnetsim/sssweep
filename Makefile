PYPKG := sssweep

.SUFFIXES:
.PHONY: help install clean

help:
	@echo "options are: install clean"

install:
	python3 setup.py install --user

clean:
	rm -rf build dist $(PYPKG).egg-info $(PYPKG)/*.pyc $(PYPKG)/__pycache__
