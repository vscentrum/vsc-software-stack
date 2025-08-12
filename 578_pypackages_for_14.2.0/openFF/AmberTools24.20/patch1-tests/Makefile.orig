######    Top-level targets, for general use:    ############################
include $(AMBERHOME)/config.h
export AMBERHOME=$(AMBER_PREFIX)

fast: fast.$(INSTALLTYPE)

test::
	./test_at_serial.sh

test.nopython::
	./test_at_serial.sh nopython

test.parallel::
	./test_at_parallel.sh

test.openmp::
	./test_at_openmp.sh

test.cuda.serial::
	./test_at_cuda_serial.sh

test.cuda.parallel::
	./test_at_cuda_parallel.sh

test.hip.serial::
	./test_at_cuda.sh hip

######    Intermediate-level targets:    ############################

fast.serial: clean is_amberhome_defined \
	fast.cpptraj fast.ambpdb fast.pytraj fast.antechamber fast.mdgx \
	fast.leap fast.unitcell fast.resp fast.py_resp fast.reduce fast.pbsa fast.gbnsr6 \
	fast.parmed fast.elsize fast.sqm fast.rism1d \
	fast.rism3d fast.paramfit \
	fast.cphstats fast.cestats fast.charmmlipid2amber fast.cpinutil \
	fast.ceinutil fast.cpeinutil fast.genremdinputs fast.fitpkaeo fast.fixremdcouts \
	fast.pymsmt fast.mmpbsa

fast.antechamber:
	cd antechamber && $(MAKE) fast
fast.charmmlipid2amber:
fast.cphstats:
fast.cestats:
fast.cpinutil:
fast.ceinutil:
fast.cpeinutil:
fast.genremdinputs:
fast.fitpkaeo:
fast.fixremdcouts:
fast.cpptraj: test.cpptraj
fast.ambpdb: test.ambpdb
fast.elsize:
fast.FEW:  # no fast testing
fast.gbnsr6:
fast.leap:
	cd leap && $(MAKE) fast
fast.mdgx:
fast.mm_pbsa:  # no fast testing
fast.mmpbsa:
	cd mmpbsa_py && $(MAKE) fast
fast.paramfit:
fast.parmed:
	cd parmed/normal_prmtop && ./Run.parmed # keep syntax consistent? (make fast); still 8 (s).
fast.pbsa:
fast.pymsmt:
fast.pytraj:
	cd pytraj && $(MAKE) fast
fast.reduce:
fast.resp:
fast.py_resp:
fast.rism1d:
fast.rism3d:
fast.sqm:
fast.unitcell:

test.serial: clean is_amberhome_defined \
	test.cpptraj test.pytraj test.antechamber test.mdgx \
	test.leap test.unitcell test.resp test.py_resp test.reduce test.pbsa test.gbnsr6 \
	test.parmed test.elsize test.sqm test.rism1d test.kmmd \
	test.rism3d test.paramfit test.mm_pbsa \
	test.FEW test.cphstats test.cestats test.charmmlipid2amber \
	test.cpinutil test.ceinutil test.cpeinutil test.genremdinputs test.fitpkaeo \
	test.fixremdcouts test.pymsmt test.packmol-memgen test.mmpbsa test.bar_pbsa \
	test.Quick

test.serial.nopython: clean is_amberhome_defined \
	test.cpptraj test.antechamber test.mdgx \
	test.leap test.unitcell test.resp test.reduce test.pbsa test.gbnsr6 \
	test.elsize test.sqm test.rism1d test.kmmd \
	test.rism3d test.paramfit test.mm_pbsa \
	test.FEW test.cphstats test.cestats

test.openmp2: clean is_amberhome_defined
	cd ../src/cpptraj/test && $(MAKE) -k test

test.parallel2: clean is_amberhome_defined \
	test.cpptraj test.rism3d test.bar_pbsa \
	test.Quick.MPI test.mmpbsa.parallel

test.cuda.serial2: clean is_amberhome_defined \
	test.pbsa.cuda test.cpptraj.cuda test.mdgx.cuda test.Quick.cuda

test.cuda.parallel2: clean is_amberhome_defined \
	test.Quick.cuda.MPI

test.pbsa.cuda:
	cd pbsa_cuda_cg && ./test.sh
	cd pbsa_cuda_mg && ./test.sh
	cd pbsa_cuda_sor && ./test.sh
	cd pbsa_cuda_ipbsas2 && ./test.sh
	cd pbsa_cuda_ipb6 && ./Run.IIM.min
	cd pbsa_cuda_ipb7 && ./Run.IIM.min
	cd pbsa_cuda_ipb8 && ./Run.IIM.min

test.mdgx.cuda:
	cd mdgx && ./Run.existence
	cd mdgx/Peptides && ./Test.peptides ${AMBERHOME}/bin/mdgx.cuda cuda

test.kmmd:
	cd kmmd/kmmd_sander && ./Run.kmmd
	cd kmmd/kmmd_sander_gb && ./Run.kmmd

test.ambermini: test.leap test.sqm test.antechamber test.reduce test.paramfit

test.ptraj:
	-cd ptraj_rmsa && ./Run.rms
	-cd ptraj_rms && ./Run.rms
#	-cd ptraj_les && ./Run.les
	-cd ptraj_matrix && ./Run.matrix
	-cd ptraj_order && ./Run.order
	-cd ptraj_trajectory && ./Run.ptraj
	-cd ptraj_remd_netcdf && ./Run.ptraj $(NETCDF)
	-cd ptraj_comprehensive && ./Run.comprehensive $(NETCDF)

test.antechamber:
	cd antechamber && $(MAKE) -k test

test.leap:
	cd leap && $(MAKE) -k test

test.unitcell:
	cd xtalutil/UnitCell && $(MAKE)

test.cpptraj:
	cd ../src/cpptraj/test && $(MAKE) -k test

test.cpptraj.cuda:
	cd ../src/cpptraj/test && $(MAKE) -e OPT=cuda -k test

test.cpptraj.hip:
	cd ../src/cpptraj/test && $(MAKE) -e OPT=hip -k test

test.pytraj:
	cd pytraj && $(MAKE)

test.pymsmt:
	cd pymsmt/mcpb/g03-ff14SB && ./Run.pymsmt
	cd pymsmt/mcpb/g09-ff14SB && ./Run.pymsmt
	cd pymsmt/mcpb/g09-ff19SB && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff14SB && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff14SB-zmx && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff19SB && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff19SB-fq && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff19SB-modsem && ./Run.pymsmt
	cd pymsmt/mcpb/g16-ff19SB-opc && ./Run.pymsmt
	cd pymsmt/mcpb/gms-ff14SB && ./Run.pymsmt
	cd pymsmt/mcpb/ezaff-ff14SB && ./Run.pymsmt
	cd pymsmt/pdbsearcher && ./Run.pymsmt
	cd pymsmt/amb2chm_psf && ./Run.pymsmt
	cd pymsmt/amb2chm_par && ./Run.pymsmt
	cd pymsmt/amb2gro && ./Run.pymsmt
	cd pymsmt/pdb2mol2 && ./Run.pymsmt

test.paramfit:
	cd paramfit && $(MAKE) -k test

test.resp:
	cd resp && ./Run.ade

test.py_resp:
	cd py_resp && ./py_resp_test.run

test.reduce:
	cd reduce && ./Run.reduce

test.mdgx:
	-cd mdgx/1p7e && ./Test.1p7e
	-cd mdgx/NVTwat && ./Test.nvtwat
	-cd mdgx/MLE && ./Test.mle
	-cd mdgx/Settle && ./Test.settle
	-cd mdgx/CMAP && ./Test.cmap
	-cd mdgx/MCBarostat && ./Test.mcb
	-cd mdgx/TIP4P && ./Test.tip4p
	-cd mdgx/ForceCalc && ./Test.frcc
	-cd mdgx/AddEP && ./Test.addep
	-cd mdgx/QFit && ./Test.qfit
	-cd mdgx/Triclinic && ./Test.triclinic
	-cd mdgx/Torsion && ./Test.torsion
	-cd mdgx/ConfSamp && ./Test.cs
	-cd mdgx/Peptides && ./Test.peptides
	-cd mdgx/Topology && ./Test.prmtop
	-cd mdgx/Topology && ./Test.prmtop_vs
	-cd mdgx/Topology && ./Test.tip4p
	-cd mdgx/Topology && ./Test.tip5p
	-cd mdgx/Topology && ./Test.methanol

test.pbsa:
	-cd pbsa_dmp && ./test
	-cd pbsa_crgview && ./Run.ion.min
	-cd pbsa_bcopt && ./Run.dmp.min
	-cd pbsa_saopt && ./Run.dmp.min
	-cd pbsa_tri && ./Run.dmp.min
	-cd pbsa_rot && ./Run.charge.min
	-cd pbsa_lpb && ./Run.lsolver.min
	-cd pbsa_ipb2 && ./Run.110D.min
	-cd pbsa_tsr && ./Run.tsrb.min
	-cd pbsa_radi && ./Run.ion.min
	-cd pbsa_npb && ./test
	-cd pbsa_frc && ./test
	-cd pbsa_delphi && ./test
	-cd pbsa_ligand && ./Run.t4bnz.min
	-cd pbsa_ipb4 && ./Run.IIM.min
	-cd pbsa_ipb5 && ./Run.ion.min
	-cd pbsa_np3m && ./Run.ion.min
	-cd pbsa_memb_test && ./Run.memb.test
	-cd pbsa_phiout && ./Run.dmp.min

test.bar_pbsa:
	cd bar_pbsa && ./Run.bar_pbsa

test.gbnsr6:
	-cd gbnsr6 && ./Run.gbnsr6.min

test.ambpdb:
	-cd ambpdb && ./Run.ambpdb
	-cd ambpdb_tz2 && ./Run.ambpdb

test.ambpdb.first:
	-cd ambpdb_first_protein && ./Run.ambpdb
	-cd ambpdb_first_rna && ./Run.ambpdb

test.elsize:
	cd elsize && ./Run.elsize

test.chamber:
	-cd ./chamber/trans-but-2-ene && ./Run
	-cd ./chamber/ala_ala_ala && ./Run
	-cd ./chamber/ala_ala_ala && ./Runx
	-cd ./chamber/poly_pro_gas && ./Run.poly_pro_gas_chamber
	-cd ./chamber/glucose && ./Run
	-cd ./chamber/dhfr_gas && ./Run.dhfr_gas_chamber
	-cd ./chamber/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_chamber
	-cd ./chamber/2b1q-trlose-wat-c36 && ./Run
	-cd ./chamber/test-c27-vmd-psf && ./Run

test.cphstats:
	-cd cphstats && ./Run.cphstats

test.cestats:
	-cd cestats && ./Run.cestats

test.Quick:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick; cd ../src/quick && ./runtest --serial ;\
	fi ;\
	)

test.Quick.MPI:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick.MPI; cd ../src/quick && ./runtest --mpi ;\
	fi ;\
	)

test.Quick.cuda:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick.cuda; cd ../src/quick && ./runtest --cuda ;\
	fi ;\
	)

test.Quick.cuda.MPI:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick.cuda.MPI; cd ../src/quick && ./runtest --cudampi ;\
	fi ;\
	)

test.Quick.hip:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick.hip; cd ../src/quick && ./runtest --hip ;\
	fi ;\
	)

test.Quick.hip.MPI:
	@(if [ "$(QUICK)" = 'yes' ]; then \
	export TESTsander=$(BINDIR)/quick.hip.MPI; cd ../src/quick && ./runtest --hipmpi ;\
	fi ;\
	)

test.sqm:
	-cd ./sqm/c2h2 && ./Run
	-cd ./sqm/ch3f && ./Run
	-cd ./sqm/nma && ./Run
	-cd ./sqm/znh+ && ./Run
	-cd ./sqm/h2s && ./Run
	-cd ./sqm/dhplus && ./Run
	-cd ./sqm/fecp2 && ./Run
	-cd ./sqm/external_charges && ./Run
	-cd ./sqm/dftb3 && ./Run

test.rism1d:
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/spc-kh && ./Run.spc; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/spc-psen && ./Run.spc-nacl-3; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/spc-hnc && ./Run.spc-lj; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/tip3p-kh && ./Run.tip3p; fi

test.rism1d.dev: test.rism1d
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-kh && ./Run.spc-nacl; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-kh && ./Run.spc-lj; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-psen && ./Run.spc-1; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-psen && ./Run.spc-3; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-psen && ./Run.spc-nacl-1; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-psen && ./Run.spc-nacl-2; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/spc-hnc && ./Run.spc; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/tip3p-kh && ./Run.tip3p-nacl; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/tip3p-kk-2008 && ./Run.tip3p-nacl-1; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/tip3p-kk-2008 && ./Run.tip3p-nacl-2; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/tip3p-kk-2008 && ./Run.tip3p-nacl-3; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/tip3p-kk-2008 && ./Run.tip3p-nacl-4; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/spc-polyt && ./Run.spc; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/spc-mv0 && ./Run.spc; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/lj-py && ./Run.lj; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/dt && ./Run.all; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd ./rism1d/dev/ && $(MAKE); fi

test.rism3d: test.rism3d.open test.rism3d.periodic
test.rism3d.open:
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_list; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp2; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_astol_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_selftest_hnc; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_selftest_kh; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_selftest_pse3; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_ljfit_boxset_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_ljfit_bufferset_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_ljset_bufferfit_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_ljset_bufferset_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_ljtol_bufferfit_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_nacl_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_nacl_tree_fast; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/ala && ./Run.rism_sp_tree_fast; fi

test.rism3d.periodic:
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/4lzta && ./Run.4lzta.kh.pme; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/1ahoa && ./Run.1ahoa.kh.pme; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/PH4+_triclinic && ./Run.PH4+_triclinic.kh.pme.center0; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/PH4+_triclinic && ./Run.PH4+_triclinic.kh.pme.center1; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/PH4+_triclinic && ./Run.PH4+_triclinic.kh.pme.center2; fi

test.rism3d.periodic.dev:
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/PH4+ && ./Run.PH4+.kh.pme; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/imidazoleH+ && ./Run.imidazoleH+.kh.pme; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/2igd && ./Run.2igd.kh.pme; fi
	-if [ -n "$(TESTRISMSFF)" ]; then cd rism3d/1d23 && ./Run.1d23.kh.pme; fi

test.saxs:
	- cd saxs && ./Run.saxs

test.mmpbsa:
	cd mmpbsa_py && $(MAKE) test

test.mmpbsa.parallel:
	cd mmpbsa_py && $(MAKE) test.parallel

test.mm_pbsa:
	cd ../src/mm_pbsa/Examples && AMBER_SOURCE=$(AMBER_SOURCE) ./Run.mmpbsa.test

test.FEW:
	cd ../src/FEW/examples/test && AMBER_SOURCE=$(AMBER_SOURCE) ./Run.few.test

test.packmol-memgen:
	cd packmol_memgen/ && ./Run.packmol-memgen

test.parmed:
	cd parmed/normal_prmtop && ./Run.parmed
	cd parmed/chamber_prmtop && ./Run.parmed
	cd parmed/solvated_prmtop && ./Run.parmed
	cd parmed/change_parms && ./Run.parmed
	cd parmed/multifiles && ./Run.parmed
	cd parmed/add12_6_4 && ./Run.parmed
	cd parmed/ti_merge && ./Run.parmed
	cd parmed/chamber && ./Run.parmed

test.cpinutil:
	cd cpinutil && ./Run.cpin

test.ceinutil:
	cd ceinutil && ./Run.cein

test.cpeinutil:
	cd cpeinutil && ./Run.cpein

test.genremdinputs:
	cd genremdinputs && ./Run.genremdinputs

test.fitpkaeo:
	cd fitpkaeo && ./Run.fitpkaeo

test.fixremdcouts:
	cd fixremdcouts && ./Run.fixremdcouts

test.charmmlipid2amber:
	cd charmmlipid2amber && ./Run.charmmlipid2amber

test.pysander:
	cd ../../test/sanderapi && make Python

test.python: test.pysander test.parmed test.pytraj test.pymsmt \
	     test.cpinutil test.ceinutil test.cpeinutil test.genremdinputs test.fitpkaeo \
	     test.fixremdcouts test.mmpbsa test.py_resp test.bar_pbsa

finished.cuda:
	@echo ""
	@echo "Finished CUDA test suite for AmberTools at `date`."
	@echo ""

finished.cuda.parallel:
	@echo ""
	@echo "Finished CUDA parallel test suite for AmberTools at `date`."
	@echo "Tests ran with DO_PARALLEL=\"${DO_PARALLEL}\"."
	@echo ""

finished.serial:
	@echo ""
	@echo "Finished serial test suite for AmberTools at `date`."
	@echo ""

finished.parallel:
	@echo ""
	@echo "Finished parallel test suite for AmberTools at `date`."
	@echo "Tests ran with DO_PARALLEL=\"${DO_PARALLEL}\"."
	@echo ""

is_amberhome_defined:
	@(if [ -z "$(AMBERHOME)" ] ; then \
	    echo "Error: AMBERHOME should be defined or else some tests will fail !" ;\
	    exit 2 ;\
	fi ;\
	)

clean:
	-./test_at_clean.sh
	-cd antechamber && $(MAKE) -k clean
	-cd mmpbsa_py && $(MAKE) -k clean
	-cd ../src/mm_pbsa/Examples && ./Run.mmpbsa.clean
	-cd ../src/FEW/examples/test && ./Run.few.clean
	-cd ../src/cpptraj/test && $(MAKE) -k clean
	-cd leap && $(MAKE) -k clean
	-cd leap/glycam/06j && ./Run.glycam clean
	-cd leap/glycam/06EPb && ./Run.glycam clean
	-cd leap/glycam/06j_10 && ./Run.glycam clean
	-cd leap/glycam/06j_12SB && ./Run.glycam clean

check:
	(find . -name "*.dif" ! -size 0c -print | \
	while read dif ;\
	do \
	    echo $$dif ;\
	    cat $$dif ;\
	    echo ;\
	done ;\
	)
