cover:
	nosetests --with-yanc -v -s --with-cov --cov-report term-missing --cov StockCollection --cov model

test:
	nosetests --with-yanc -v -s

requirements:
	pip freeze > requirements.txt