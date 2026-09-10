################################## VARIABLES ###################################

ROOT_DIR := $(shell git rev-parse --show-toplevel)
PORT      = $(AI_PROCESSING_PORT)

##################################### RULES ####################################

include $(ROOT_DIR)/shared/mk/service.mk

############################## OVERRIDE VARIABLES ##############################

# This service uses its own dedicated pgvector-enabled Postgres instance,
# overriding the shared instance's connection info pulled in above.
POSTGRES_PORT     := $(AI_POSTGRES_PORT)
