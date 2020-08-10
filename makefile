default : help
	@echo ""
	@echo "No action specified."

help :
	@echo "Available actions:"
	@echo " - clean: deletes output files"
	@echo " - assemble: generates source files from input"
	@echo " - open: open output with arduino IDE (PATH must be set)"
	@echo " - upload: compiles and uploades output (linux only)"
	@echo " - all: first assamble than build"

assemble :
	@python ./source/generator.py input

open :
	@arduino ./output/main/main.ino

upload :
	@./uploader.sh

clean :
	@echo "Clearing output..."
	@mkdir -p ./output
	@rm -rf ./output/*

all : clean assemble