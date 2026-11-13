# Reuse the existing guest, or delegate creation to the interactive target.
vm-ensure:
	@vm_present=false; \
	for disk in "$(VM_DIR)"/ubuntu-server-cloud-*.qcow2; do \
		if [ -f "$$disk" ]; then vm_present=true; break; fi; \
	done; \
	if [ "$$vm_present" = false ]; then \
		$(MAKE) --no-print-directory create-vm; \
	fi

# Keep stop and launch sequential, including when Make runs with -j.
vm-restart:
	@$(MAKE) --no-print-directory stop-vm
	@$(MAKE) --no-print-directory launch-vm

.PHONY: vm-ensure vm-restart
