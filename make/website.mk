# Website template targets. The Makefile includes this file with `-include make/*.mk`.

.PHONY: messages-compile package

# The page tests check the Spanish text, and .mo files are gitignored:
# compile the catalogues before any test run.
test test-cov check-fast: messages-compile

messages-compile: export DJANGO_SETTINGS_MODULE := config.settings.test
messages-compile:
	$(RUN) python manage.py compilemessages --ignore=.venv

# Build a clean zip of the project to send to the OEES tech team.
package:
	python3 scripts/package.py
