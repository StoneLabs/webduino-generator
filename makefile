default :
	@echo "No action specified."
	@echo " - clean: deletes output files"
	@echo " - assemble: generates source files from input"
	@echo " - open: open output with arduino IDE (PATH must be set)"
	@echo " - all: first assamble than build"

assemble :
	@python ./source/generator.py input

open :
	@arduino ./output/main/main.ino

clean :
	@echo "Clearing output..."
	@mkdir -p ./output
	@rm -rf ./output/*

all : clean assemble