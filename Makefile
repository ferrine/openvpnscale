ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: superuser reset-hard migrations

superuser:
		docker-compose run web python /code/manage.py createsuperuser

reset-hard:
		docker-compose down -v

migrations:
		docker-compose run web python /code/manage.py makemigrations
		docker-compose run web python /code/manage.py migrate
