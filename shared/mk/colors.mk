DEFAULT_COLOR := \033[0;39m
RED_COLOR     := \033[0;91m
GREEN_COLOR   := \033[0;92m
YELLOW_COLOR  := \033[0;93m
BLUE_COLOR    := \033[0;94m
CYAN_COLOR    := \033[0;96m

define print
	printf "$(1)$(2)$(DEFAULT_COLOR)\n"
endef