build: clean
	.venv/bin/python setup.py py2app

clean:
	rm -rf build dist .eggs

install: venv
	.venv/bin/python -m pip install -r requirements.txt

run: venv
	.venv/bin/python watson-statusbar.py

venv:
ifeq ($(wildcard .venv),)
	@echo "[-] Creating a virtual environment in .venv/..."
	@test -d venv || python3 -m venv .venv
	@echo "[-] Updating pip..."
	@.venv/bin/python3 -m pip install -q --upgrade pip
	@echo "[-] Done!"
endif