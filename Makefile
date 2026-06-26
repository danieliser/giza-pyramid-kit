.PHONY: generate validate serve clean

generate:
	python3 generate_giza_kit.py

validate:
	python3 validate_geometry.py

serve:
	python3 -m http.server 8026

clean:
	rm -rf __pycache__ .playwright-cli
