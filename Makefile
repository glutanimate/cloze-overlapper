# builds zip file for AnkiWeb (among other things)

VERSION = $(git describe HEAD --tags --abbrev=0)
ADDON = "cloze-overlapper"

release: ui zip clean_dist

clean: clean_zip clean_dist

clean_zip:
	rm $(ADDON)-*.zip

clean_dist:
	rm -rf dist

ui:
	rm -rf $(ADDON)/forms
	./tools/build_ui.sh

zip:
	rm -rf dist
	mkdir -p dist
	find . -name '*.pyc' -delete
	cp *.py dist/
	./tools/build_ui.sh
	cp -r cloze_overlapper dist/
	cd dist && zip -r ../$(ADDON)-$(VERSION).zip *