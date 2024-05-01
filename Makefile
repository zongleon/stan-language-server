install:
	poetry build
	python3.9 -m pip install --force-reinstall --no-deps dist/stan_language_server-0.1.0-py3-none-any.whl
