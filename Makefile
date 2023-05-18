.PHONY: all zip ankiweb fix mypy pylint vendor clean

all: zip ankiweb

zip:
	python -m ankiscripts.build --type package --qt all --exclude user_files/**/ --exclude user_files/*.db

ankiweb:
	python -m ankiscripts.build --type ankiweb --qt all --exclude user_files/**/ --exclude user_files/*.db

fix:
	python -m black src tests --exclude="forms|vendor"
	python -m isort src tests

mypy:
	python -m mypy src tests

pylint:
	python -m pylint src tests

vendor:
	./vendor.sh

clean:
	rm -rf build/
