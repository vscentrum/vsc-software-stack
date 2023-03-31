SHELL = /bin/bash
UNAME_S := $(shell uname -s)

AUTOMATIC_LIBBOOST_LOCAL_INSTALL=yes
## adapt those values to your system
#HDF5_INCLUDE=/usr/include/hdf5/serial/
#HDF5_LD=/usr/lib/x86_64-linux-gnu/hdf5/serial/
#ifeq ($(UNAME_S),Darwin)
#HDF5_INCLUDE=/Users/admin/miniconda3/include
#HDF5_LD=/Users/admin/miniconda3/lib
#AEC_LD=-L/opt/local/lib/libaec/lib
#RPATH=-rpath .
#endif

all: lordec_141

CXX = g++
RM = rm -f
MV = mv
CP = cp

############## Source files #################
CFILES_CORRECT = lordec-correct.cpp utils.cpp
CFILES_TEST_CORRECT = unittest-lordec-correct.cpp
CFILES_CATCHTEST_CORRECT = catchtest-lordec-correct.cpp
#CFILES_STATS = statistics.cpp
CFILES_STATS = lordec-stat.cpp
CFILES_TRIM = lordec-trim.cpp
CFILES_TRIM_SPLIT = lordec-trim-split.cpp
CFILES_GRAPH = lordec-build-SR-graph.cpp

############# Object files #################
OBJS_CORRECT = $(CFILES_CORRECT:.cpp=.o)
OBJS_TEST_CORRECT = $(CFILES_TEST_CORRECT:.cpp=.o)
OBJS_CATCHTEST_CORRECT = $(CFILES_CATCHTEST_CORRECT:.cpp=.o)
OBJS_STATS = $(CFILES_STATS:.cpp=.o)
OBJS_TRIM = $(CFILES_TRIM:.cpp=.o)
OBJS_TRIM_SPLIT = $(CFILES_TRIM_SPLIT:.cpp=.o)

############ Binaries to produce ############
PROG = LoRDEC
PROG_CORRECT = lordec-correct
PROG_TEST_CORRECT = unittest-lordec-correct
PROG_CATCHTEST_CORRECT = catchtest-lordec-correct
PROG_STATS = lordec-stat
PROG_TRIM = lordec-trim
PROG_TRIM_SPLIT = lordec-trim-split
PROG_PB_STAT = pb-stat
PROG_GRAPH = lordec-build-SR-graph
HPC_SCRIPT=tools/lordec_sge_slurm_wrapper.sh
# all binaries
PROGS = lordec-correct lordec-stat lordec-trim lordec-trim-split pb-stat lordec-build-SR-graph LoRDEC unittest-lordec-correct catchtest-lordec-correct
# ER 28.02.16 test for an option to control temporary disk location 
TEST_GRAPH = test-create-tmp-opt

##################### Dependencies to BOOST and GATB ############
# on MacOS, we need to get boost include files
ifeq ($(UNAME_S),Darwin)
$(PROG_GRAPH) $(OBJS_TEST_CORRECT) $(OBJS_CATCHTEST_CORRECT) $(OBJS_CORRECT) $(OBJS_STATS) $(OBJS_TRIM) $(OBJS_TRIM_SPLIT): boost_include/boost/graph/graph_traits.hpp
endif

ifeq ($(AUTOMATIC_LIBBOOST_LOCAL_INSTALL),yes)
$(PROG_GRAPH) $(OBJS_TEST_CORRECT) $(OBJS_CATCHTEST_CORRECT) $(OBJS_CORRECT) $(OBJS_STATS) $(OBJS_TRIM) $(OBJS_TRIM_SPLIT): boost_include/boost/graph/graph_traits.hpp
endif
# ANYWAY we need GATB (compiled and installed) to compile all the objects
# $(PROG_GRAPH) $(OBJS_TEST_CORRECT) $(OBJS_CATCHTEST_CORRECT) $(OBJS_CORRECT) $(OBJS_STATS) $(OBJS_TRIM) $(OBJS_TRIM_SPLIT): gatb_v$(GATBVERSION)$(SUFFIX)/include/gatb/gatb_core.hpp

# get version from a file
VERSION := $(shell cat version.txt)
LICENSE=./LICENSE/Licence_CeCILL_V2.1-en.txt

# for testing
DATA=./DATA
RES=./RES
TEST_SCRIPT=test-lordec.sh

# These also need to be included in distribution package
HPPFILES=lordec-gen.hpp

############### SET GENERAL VARIABLES ##################
# those variables are used for lordec binaries and test binaries
ifeq ($(UNAME_S),Darwin)
ADDITIONAL_INCLUDE="-Iboost_include/"
MACMACROS=-DUSE_NEW_CXX -DBOOST_NO_CXX11_RVALUE_REFERENCES=1
endif

ifeq ($(AUTOMATIC_LIBBOOST_LOCAL_INSTALL),yes)
ADDITIONAL_INCLUDE="-Iboost_include/"
endif
GATB=gatb_v$(GATBVERSION)$(SUFFIX)
CPPFLAGS = -w -I$(GATB)/include/ $(ADDITIONAL_INCLUDE) -DGATB_V$(GATBSHORTVERSION) -DLORDECVERSION=$(VERSION)$(SUFFIX) -DGATBVERSION=$(GATBVERSION)$(SUFFIX) $(MACMACROS) -std=c++0x -O3 $(CDEBUG)
LDFLAGS = -L$(GATB)/lib/ -lgatbcore -lhdf5$(HDFSUFFIX) -ldl -lz -lpthread -std=c++0x -O3 $(EXTRALDFLAGS)
CXXFLAGS = -w #-Wall  # put compiler settings here
####################################################

# binary list to build lordec
lordecbins: $(PROG_CORRECT) $(PROG_STATS) $(PROG_TRIM) $(PROG_TRIM_SPLIT) $(PROG_GRAPH)

################### How to build each binary ###################
$(PROG_CORRECT): $(OBJS_CORRECT)
	$(CXX) $(OBJS_CORRECT) $(LDFLAGS) -o $@

$(PROG_TEST_CORRECT): $(OBJS_TEST_CORRECT)
	$(CXX) $(OBJS_TEST_CORRECT) $(LDFLAGS) -o $@

$(PROG_CATCHTEST_CORRECT): $(OBJS_CATCHTEST_CORRECT)
	$(CXX) $(OBJS_CATCHTEST_CORRECT) $(LDFLAGS) -o $@

$(PROG_STATS): $(OBJS_STATS)
	$(CXX) $(OBJS_STATS) $(LDFLAGS) -o $@ 

$(PROG_TRIM): $(OBJS_TRIM)
	$(CXX) $(OBJS_TRIM) $(LDFLAGS) -o $@ 

$(PROG_TRIM_SPLIT): $(OBJS_TRIM_SPLIT)
	$(CXX) $(OBJS_TRIM_SPLIT) $(LDFLAGS) -o $@ 

$(PROG_GRAPH): $(CFILES_GRAPH)
	$(CXX)  $@.cpp -o $@ $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS)

# ER 28.02.16 test for an option to control temporary disk location 
$(TEST_GRAPH): $(CFILES_GRAPH)
	$(CXX)  $@.cpp -o $@ $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS)

# version with .o file
# $(PROG_GRAPH): $(OBJS_GRAPH)
# 	$(CXX) $(OBJS_GRAPH) $(LDFLAGS) -o $@ 

# $(PROG_PB_STAT): $@.o  #$@.cpp
# 	$(CXX)  $@.o -o $@ $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS)

#################### How to build objects #####################
$(OBJS_TEST_CORRECT): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

$(OBJS_CATCHTEST_CORRECT): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

$(OBJS_CORRECT): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

$(OBJS_STATS): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

$(OBJS_TRIM): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

$(OBJS_TRIM_SPLIT): %.o: %.cpp
	$(CXX) $< $(CPPFLAGS) -c

################################### GENERIC TARGETS ##############################################
# The following targets are supposed to be called by the user.
# With Makefile wildcards (%), it's impossible to modify the prerequisites because they are evaluated
# before rules executions. So here, we set all the variables and run MAKE again with a complete environment.
# This way we can factorize a lot.

lordec_%:
	GATBSHORTVERSION=$*;\
	GATBVERSION=$(shell echo $(*) | sed 's:\(.\):.\1:g' | sed 's:^\.::g');\
	GATBSHORTVERSION=$$GATBSHORTVERSION GATBVERSION=$$GATBVERSION CMAKEDEBUG=$(CMAKEDEBUG) SUFFIX=$(SUFFIX) HDFSUFFIX=$(HDFSUFFIX) CDEBUG=$(CDEBUG) EXTRALDFLAGS=$(EXTRALDFLAGS) $(MAKE) lordecbins

lordecdebug_%: CMAKEDEBUG=-DCMAKE_BUILD_TYPE=Debug
lordecdebug_110: CMAKEDEBUG=-Ddebug=1
lordecdebug_%: SUFFIX=_debug
lordecdebug_%: HDFSUFFIX=_debug
# for GATB 1.1.x and 1.2.x, linking with libhdf5 does not need a suffix
lordecdebug_110 lordecdebug_120 lordecdebug_121 lordecdebug_122: HDFSUFFIX=
lordecdebug_%: CDEBUG=-g
lordecdebug_%: lordec_%
	@echo DEBUG done

lordecstatic_%: EXTRALDFLAGS=-static
lordecstatic_%: lordec_%
	@echo STATIC done

unittest_%:
	GATBSHORTVERSION=$*;\
	GATBVERSION=$(shell echo $(*) | sed 's:\(.\):.\1:g' | sed 's:^\.::g');\
	GATBSHORTVERSION=$$GATBSHORTVERSION GATBVERSION=$$GATBVERSION EXTRALDFLAGS="-lcppunit -static" $(MAKE) $(PROG_TEST_CORRECT)

catchtest_%:
	GATBSHORTVERSION=$*;\
	GATBVERSION=$(shell echo $(*) | sed 's:\(.\):.\1:g' | sed 's:^\.::g');\
	GATBSHORTVERSION=$$GATBSHORTVERSION GATBVERSION=$$GATBVERSION $(MAKE) $(PROG_CATCHTEST_CORRECT)

catchtestcov_%:
	GATBSHORTVERSION=$*;\
	GATBVERSION=$(shell echo $(*) | sed 's:\(.\):.\1:g' | sed 's:^\.::g');\
	EXTRALDFLAGS=-lgcov CDEBUG="-fprofile-arcs -ftest-coverage -g" GATBSHORTVERSION=$$GATBSHORTVERSION GATBVERSION=$$GATBVERSION $(MAKE) $(PROG_CATCHTEST_CORRECT)

##################### COMPILE GATB ############################
%/include/gatb/gatb_core.hpp:
		echo $@;\
		rm -rf v$(GATBVERSION).tar.gz gatb-core-$(GATBVERSION) && \
		wget https://github.com/GATB/gatb-core/archive/v$(GATBVERSION).tar.gz && \
		tar xf v$(GATBVERSION).tar.gz && \
		cd gatb-core-$(GATBVERSION)/gatb-core/ && \
		mkdir build && cd build && \
		cmake -DCMAKE_INSTALL_PREFIX=../../../gatb_v$(GATBVERSION)$(SUFFIX) $(CMAKEDEBUG) .. && \
		$(MAKE) && $(MAKE) install && \
		cd ../../.. && rm -r v$(GATBVERSION).tar.gz gatb-core-$(GATBVERSION)

##################### compulsory on MACOS, optional on Linux : install boost includes manually #########################
boost_include/boost/graph/graph_traits.hpp:
		rm -rf boost_include boost_1_64_0 boost_1_64_0.tar.gz && \
		wget --no-check-certificate https://kent.dl.sourceforge.net/project/boost/boost/1.64.0/boost_1_64_0.tar.gz && \
		tar xf boost_1_64_0.tar.gz && \
		mkdir boost_include && \
		mv boost_1_64_0/boost boost_include/ && \
		rm -rf boost_1_64_0 boost_1_64_0.tar.gz

bin:
	mkdir bin

instbin:
	$(MV) $(PROG_CORRECT) $(PROG_STATS) $(PROG_TRIM) $(PROG_TRIM_SPLIT) $(PROG_GRAPH) bin

install:
	$(MV) $(PROG_CORRECT) $(PROG_STATS) $(PROG_TRIM) $(PROG_TRIM_SPLIT) $(PROG_GRAPH) $(PREFIX)/
	$(CP) $(HPC_SCRIPT) $(PREFIX)/

clean:
	$(RM) $(OBJS_CORRECT) $(OBJS_TEST_CORRECT) $(OBJS_CATCHTEST_CORRECT) $(OBJS_STATS) $(OBJS_TRIM) $(OBJS_TRIM_SPLIT) $(PROGS)

clean_dep:
	rm -rf gatb_v* gatb-core* v1*

purge: clean
	$(RM) $(PROG_CORRECT) $(PROG_STATS) $(PROG_TRIM) $(PROG_TRIM_SPLIT) $(PROG_GRAPH)

dist:
	mkdir $(PROG)-$(VERSION)
	cp $(CFILES_CORRECT) $(PROG)-$(VERSION)/
	cp $(CFILES_STATS) $(PROG)-$(VERSION)/
	cp $(CFILES_TRIM) $(PROG)-$(VERSION)/
	cp $(CFILES_TRIM_SPLIT) $(PROG)-$(VERSION)/
	cp $(CFILES_GRAPH) $(PROG)-$(VERSION)/
	cp $(LICENSE) $(PROG)-$(VERSION)/LICENSE
	cp $(HPPFILES) $(PROG)-$(VERSION)/
	cp -r $(DATA) $(PROG)-$(VERSION)/
	cp $(TEST_SCRIPT) $(PROG)-$(VERSION)/
	cp Makefile.dist $(PROG)-$(VERSION)/Makefile
	sed 's/VERSION/$(VERSION)/g' < README.org > $(PROG)-$(VERSION)/README.org
	sed 's/VERSION/$(VERSION)/g' < README.html > $(PROG)-$(VERSION)/README.html
	tar zcvf $(PROG)-$(VERSION).tar.gz $(PROG)-$(VERSION)

debian:
	cd build_debian/;\
	./build.sh
	mv build_debian/lordec-bin_$(VERSION)_amd64.deb ./

conda:
	cd conda;\
	conda build lordec

source_tarball: lordec-src_$(VERSION).tar.bz2

lordec-src_$(VERSION).tar.bz2:
	git clone https://gite.lirmm.fr/rivals/lordec /tmp/lordec-src_$(VERSION) &&\
	cp /tmp/lordec-src_$(VERSION)/tools/lordec_sge_slurm_wrapper.sh /tmp/lordec-src_$(VERSION)/ &&\
	rm -rf /tmp/lordec-src_$(VERSION)/tools/ /tmp/lordec-src_$(VERSION)/.git /tmp/lordec-src_$(VERSION)/build_debian/ /tmp/lordec-src_$(VERSION)/catch* /tmp/lordec-src_$(VERSION)/test-lordec.sh /tmp/lordec-src_$(VERSION)/conda /tmp/lordec-src_$(VERSION)/DATA/ /tmp/lordec-src_$(VERSION)/README.html /tmp/lordec-src_$(VERSION)/README.org /tmp/lordec-src_$(VERSION)/tests_snakemake /tmp/lordec-src_$(VERSION)/unittest-lordec-correct.cpp /tmp/lordec-src_$(VERSION)/.gitlab-ci.yml /tmp/lordec-src_$(VERSION)/.gitignore &&\
	cd /tmp && tar cjvf lordec-src_$(VERSION).tar.bz2 lordec-src_$(VERSION) && cd - &&\
	rm -rf /tmp/lordec-src_$(VERSION) &&\
	mv /tmp/lordec-src_$(VERSION).tar.bz2 ./

bin_tarball: lordec-bin_$(VERSION).tar.bz2

lordec-bin_$(VERSION).tar.bz2: all
	rm -rf lordec-bin_$(VERSION) &&\
	mkdir lordec-bin_$(VERSION) &&\
	strip $(PROGS) ;\
	cp $(PROGS) $(HPC_SCRIPT) lordec-bin_$(VERSION) ;\
	tar cjvf lordec-bin_$(VERSION).tar.bz2 lordec-bin_$(VERSION) && rm -rf lordec-bin_$(VERSION)

dist-clean:
	$(RM) -r $(PROG)-$(VERSION)/

test:
	./$(TEST_SCRIPT)
