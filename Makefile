.PHONY: generate validate serve release clean

generate:
	python3 generate_giza_kit.py

validate:
	python3 validate_geometry.py

serve:
	python3 -m http.server 8026

release: generate validate
	python3 scripts/prepare_release.py

clean:
	rm -rf __pycache__ .playwright-cli
