default :
	@echo "No action specified."
	@echo " - clean: deletes output files"
	@echo " - assemble: generates source files from input"
	@echo " - build: build hex file from source files"
	@echo " - all: first assamble than build"

assemble :
	python ./source/generator.py input

clean :
	@echo "Clearing output..."
	@rm -r ./output/*