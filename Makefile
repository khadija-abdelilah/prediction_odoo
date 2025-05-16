## This makefile is used to start the docker compose environment and stop it
## with the command "make start" and "make stop"

.PHONY: build logs tests
DIR := $(notdir $(CURDIR))
CMD := docker compose -p $(DIR) -f docker/docker-compose.yml
ODOO_CONTAINER := "dija-odoo"

# ------------  mkdir section ---------------
# Create odoo directory and test directory if they don't exist
$(shell mkdir -p odoo)
$(shell mkdir -p odoo_tests)
# ------------  mkdir section ---------------


help:
	@echo "Available commands:"
	@echo "  build		Build the docker compose environment"
	@echo "  clean		Same as 'stop' but with volumes removal"
	@echo "  init		Create fresh new database without demo data"
	@echo "  init_demo	Create fresh new database with demo data"
	@echo "  psql		Start psql console"
	@echo "  restart 	Restart the docker compose environment"
	@echo "  shell		Start Odoo shell"
	@echo "  start		Start the docker compose environment"
	@echo "  stop		Stop the docker compose environment"
	@echo "  tests		Launch the python tests"

build:
	$(CMD) build

## Create fresh new database without demo data
init: stop clean start

clean:
	$(CMD) down -v && $(CMD) rm

psql:
	$(CMD) up -d db  && $(CMD) exec db psql -U odoo

restart:
	$(CMD) restart

start_with_debug:
	$(CMD) up -d && docker attach lpcr-odoo

shell:
	$(CMD) up -d \
	&& $(CMD) exec odoo server/odoo-bin shell -c config/odoo.conf

start:
	$(CMD) up -d && docker attach $(ODOO_CONTAINER)

stop:
	$(CMD) down && $(CMD) rm

## Tests
test:
	ODOO_ARGS="--stop-after-init --test-tags $$TEST_TAGS" $(CMD) up --exit-code-from odoo

tests:
	TEST="1" && $(CMD) -f docker/docker-compose.tests.yml up --build --exit-code-from odoo \
	&& $(CMD) -f docker/docker-compose.tests.yml down
