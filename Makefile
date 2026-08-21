.PHONY: run test preflight reset
run:
	cd backend && python run.py

test:
	cd backend && python -m pytest -q

preflight:
	cd backend && python -m pytest -q
	@echo JurisTwin Mastery preflight passed.

reset:
	@python reset_demo.py
