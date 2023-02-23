.PHONY: all zip clean mypy pylint vendor fix
all: zip

PACKAGE_NAME := video_search

zip: $(PACKAGE_NAME).ankiaddon

$(PACKAGE_NAME).ankiaddon: src/*
	rm -f $@
	find src/ -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	( cd src/; zip -r ../$@ * -x meta.json -x "user_files/media/*" -x "user_files/*.db" )

vendor:
	./vendor.sh

fix:
	python -m black src --exclude=vendor
	python -m isort src

mypy:
	python -m mypy src

pylint:
	python -m pylint src

clean:
	rm -f $(PACKAGE_NAME).ankiaddon
