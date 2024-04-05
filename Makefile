install:
	poetry build
	pip3 install dist/stan_language_server-0.1.0-py3-none-any.whl --force-reinstall
