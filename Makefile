# Makefile for Basketball Calendar project

.PHONY: help lint lint-fix install test clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install project dependencies"
	@echo "  make lint       - Run pylint on all Python files"
	@echo "  make lint-fix   - Auto-fix common linting issues (imports, whitespace)"
	@echo "  make clean      - Remove Python cache files"

install:
	pip install -r requirements.txt

lint:
	python -m pylint main.py eku_main.py update_attendees.py

lint-fix:
	python -m isort main.py eku_main.py update_attendees.py
	@echo "Trailing whitespace must be fixed manually in your editor"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
