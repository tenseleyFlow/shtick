.PHONY: help install uninstall clean reinstall reshim

help:
	@echo "Shtick Makefile"
	@echo "  make install      - pip install -e . && asdf reshim python"
	@echo "  make uninstall    - pip uninstall shtick"
	@echo "  make clean        - rm -rf **/*/*.egg-info"
	@echo "  make reshim       - asdf reshim python"
	@echo "  make reinstall    - Uninstall, clean, then install & reshim"

install:
	pip install -e .
	asdf reshim python

uninstall:
	pip uninstall -y shtick

clean:
	rm -rf **/*/*.egg-info

reshim:
	asdf reshim python

reinstall: uninstall clean install

test:
	pytest tests/
