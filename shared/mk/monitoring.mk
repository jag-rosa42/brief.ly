# Monitoring runs as an independent Compose project on the shared networks.
MONITORING_COMPOSE = $(COMPOSE) -f compose.monitoring.yaml
MONITORING_TARGETS := monitoring-up monitoring-down monitoring-ps monitoring-logs

.PHONY: monitoring-storage $(MONITORING_TARGETS)

# Create only missing volumes. Existing ${DOMAIN}_* volumes came from the old
# application project and contain the monitoring history and Grafana state.
monitoring-storage:
	@for volume in prometheus_data grafana_data pushgateway_data; do \
		$(CONTAINER_CMD) volume inspect "$(DOMAIN)_$$volume" >/dev/null 2>&1 || \
			$(CONTAINER_CMD) volume create "$(DOMAIN)_$$volume" >/dev/null || exit $$?; \
	done

monitoring-up: shared-networks monitoring-storage
	@test -s shared/secrets/grafana_admin_password || { printf '[MONITORING] Missing Grafana password. Run make secrets or make vm-sync.\n' >&2; exit 1; }
	@$(MONITORING_COMPOSE) up -d --wait
	@$(call print,$(GREEN_COLOR),[MONITORING] Grafana: http://127.0.0.1:$(GRAFANA_PORT))

monitoring-down:
	@$(MONITORING_COMPOSE) down

monitoring-ps:
	@$(MONITORING_COMPOSE) ps

monitoring-logs:
	@$(MONITORING_COMPOSE) logs -f $(SERVICE)
