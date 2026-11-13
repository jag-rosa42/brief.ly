# Reuse the existing guest, or delegate creation to the interactive target.
vm-ensure:
	@vm_present=false; \
	for disk in "$(VM_DIR)"/ubuntu-server-cloud-*.qcow2; do \
		if [ -f "$$disk" ]; then vm_present=true; break; fi; \
	done; \
	if [ "$$vm_present" = false ]; then \
		$(MAKE) --no-print-directory create-vm; \
	fi

.PHONY: vm-ensure
