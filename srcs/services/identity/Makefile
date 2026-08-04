################################## VARIABLES ###################################
RUN 								= uv run
MESSAGE							?= "migration"
REVISION						?= head
DOWNGRADE_REVISION	?= -1

#################################### COLORS ####################################

DEFAULT_COLOR		= \033[0;39m
RED_COLOR				= \033[0;91m
GREEN_COLOR			= \033[0;92m
YELLOW_COLOR		= \033[0;93m
BLUE_COLOR			= \033[0;94m

#################################### RULES #####################################

.PHONY: migration upgrade downgrade current history heads run status

migration:
	$(RUN) alembic revision --autogenerate -m "$(MESSAGE)"

upgrade:
	$(RUN) alembic upgrade $(REVISION)

downgrade:
	$(RUN) alembic downgrade "$(DOWNGRADE_REVISION)"

current:
	$(RUN) alembic current

history:
	$(RUN) alembic history

status:
	$(RUN) python -m src.infrastructure.database.config.migration_status

heads:
	$(RUN) alembic heads

run:
	$(RUN) fastapi dev