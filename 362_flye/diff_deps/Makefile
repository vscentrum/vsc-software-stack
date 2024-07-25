ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
THREADS := 4

export LIBCUCKOO = -I${ROOT_DIR}/lib/libcuckoo
export INTERVAL_TREE = -I${ROOT_DIR}/lib/interval_tree
export LEMON = -I$(EBROOTLEMON)/include
export BIN_DIR = ${ROOT_DIR}/bin
export MINIMAP2_DIR = $(EBROOTMINIMAP2)
export SAMTOOLS_DIR = $(EBROOTSAMTOOLS)

export CXXFLAGS += ${LIBCUCKOO} ${INTERVAL_TREE} ${LEMON} -I${MINIMAP2_DIR}/include
export LDFLAGS += -lz -L${MINIMAP2_DIR} -lminimap2

ifeq ($(shell uname -m),arm64)
	export arm_neon=1
	export aarch64=1
endif

.PHONY: clean all profile debug minimap2 samtools

.DEFAULT_GOAL := all


${BIN_DIR}/flye-minimap2:
	cp ${MINIMAP2_DIR}/bin/minimap2 ${BIN_DIR}/flye-minimap2

minimap2: ${BIN_DIR}/flye-minimap2

samtools: ${BIN_DIR}/flye-samtools

${BIN_DIR}/flye-samtools:
	cp ${SAMTOOLS_DIR}/bin/samtools ${BIN_DIR}/flye-samtools

all: minimap2 samtools
	make release -C src -j ${THREADS}
profile: minimap2 samtools
	make profile -C src -j ${THREADS}
debug: minimap2 samtools
	make debug -C src -j ${THREADS}
clean:
	make clean -C src
	rm -f ${BIN_DIR}/flye-minimap2
	rm -f ${BIN_DIR}/flye-samtools