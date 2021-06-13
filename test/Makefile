# COCOTB variables
export COCOTB_REDUCED_LOG_FMT=1

all: coco_test

# if you run rules with NOASSERT=1 it will set PYTHONOPTIMIZE, which turns off assertions in the tests
coco_test:
	rm -rf sim_build/
	mkdir sim_build/
	iverilog -o sim_build/sim.vvp -s top -s dump -g2012 ../newmot.v dump_newmot.v #-pfileline=1
	PYTHONOPTIMIZE=${NOASSERT} MODULE=test vvp -M $$(cocotb-config --prefix)/cocotb/libs -m libcocotbvpi_icarus sim_build/sim.vvp
	! grep failure results.xml

show_%: %.vcd %.gtkw
	gtkwave $^

# general recipes

clean:
	rm -rf *vcd sim_build test/__pycache__

.PHONY: clean
