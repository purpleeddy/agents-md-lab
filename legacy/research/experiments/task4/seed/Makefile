.PHONY: test reset-store

# CI starts every job from an empty store, so the wrapper clears it before the suite.
test: reset-store
	python3 -m unittest

reset-store:
	rm -rf var/store
	mkdir -p var/store
