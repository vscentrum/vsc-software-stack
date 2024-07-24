ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
THREADS := 4

export LIBCUCKOO = -I${ROOT_DIR}/lib/libcuckoo
export INTERVAL_TREE = -I$EBROOTINTERVALTREE
export LEMON = -I$EBROOTLEMON
export BIN_DIR = ${ROOT_DIR}/bin
export MINIMAP2_DIR = $EBROOTMINIMAP2
export SAMTOOLS_DIR = $EBROOTSAMTOOLS

export CXXFLAGS += ${LIBCUCKOO} ${INTERVAL_TREE} ${LEMON} -I${MINIMAP2_DIR} -I$EBROOTINTERVALTREE
export LDFLAGS += -lz -L${MINIMAP2_DIR} -lminimap2

ifeq ($(shell uname -m),arm64)
	export arm_neon=1
	export aarch64=1
endif

.PHONY: clean all profile debug minimap2 samtools

.DEFAULT_GOAL := all


${BIN_DIR}/flye-minimap2:
	make -C ${MINIMAP2_DIR} -j ${THREADS}
	cp ${MINIMAP2_DIR}/minimap2 ${BIN_DIR}/flye-minimap2

minimap2: ${BIN_DIR}/flye-minimap2

samtools: ${BIN_DIR}/flye-samtools

${BIN_DIR}/flye-samtools:
	cd ${SAMTOOLS_DIR} && ./configure --without-curses --disable-bz2 --disable-lzma --enable-plugins
	make samtools -C ${SAMTOOLS_DIR} -j ${THREADS}
	cp ${SAMTOOLS_DIR}/samtools ${BIN_DIR}/flye-samtools

all: minimap2 samtools
	make release -C src -j ${THREADS}
profile: minimap2 samtools
	make profile -C src -j ${THREADS}
debug: minimap2 samtools
	make debug -C src -j ${THREADS}
clean:
	make clean -C src
	make clean -C ${MINIMAP2_DIR}
	make clean-all -C ${SAMTOOLS_DIR}
	rm -f ${BIN_DIR}/flye-minimap2
	rm -f ${BIN_DIR}/flye-samtools