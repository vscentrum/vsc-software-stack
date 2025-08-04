SHELL=/bin/sh
AMBER_VERSION=24

include $(AMBERHOME)/config.h

#Cuda Options
#------------
#Precision model to test (options are SPFP, SPDP, DPDP) - default is DPFP
PREC_MODEL=DPFP
#------------

######    Top-level targets, for general use:    ############################

test: clean
	./test_amber_serial.sh

test.parallel: clean
	./test_amber_parallel.sh

test.cuda.serial: clean
	./test_amber_cuda_serial.sh

test.cuda.serial.SPFP: clean
	./test_amber_cuda_serial.sh SPFP

test.cuda.parallel: clean
	./test_amber_cuda_parallel.sh

test.cuda.parallel.SPFP: clean
	./test_amber_cuda_parallel.sh SPFP

test.hip.serial: clean
	./test_amber_hip_serial.sh

test.hip.serial.SPFP: clean
	./test_amber_hip_serial.sh SPFP

test.hip.parallel: clean
	./test_amber_hip_parallel.sh

test.hip.parallel.SPFP: clean
	./test_amber_hip_parallel.sh SPFP

######    Intermediate-level targets for AmberTools:    #############

fast.sanderapi:
	cd sanderapi && $(MAKE) Python # 3 (s)

test.serial:  test.serial.MM test.serial.QMMM test.serial.sander.SEBOMD \
    test.serial.emil test.serial.sanderapi test.serial.fetoolkit

test.serial.nopython:  test.serial.MM test.serial.QMMM test.serial.sander.SEBOMD \
    test.serial.emil test.serial.fetoolkit.nopython

test.serial.sander.MM: test.sander.BASIC.nopar test.sander.BASIC \
	test.sander.GB test.sander.LES test.sander.PIMD.partial \
	test.serial.sander.nfe test.sander.pgm test.pbsa test.sander.constph test.sander.conste \
	test.sander.constphe test.sander.RISM  test.serial.sander.kmmd \
	test.sander.crgreloc test.serial.sander.AMD test.serial.sander.sgld \
	test.serial.sander.emap test.sander.OIN test.sander.CHARMM \
	test.sander.SINR test.sander.music test.sander.middle-scheme \
	test.sander.TFE 

test.serial.MM: test.serial.sander.MM test.nmode

test.serial.QMMM: \
	test.sander.QMMM.nopar test.sander.QMMM \
	test.sander.DFTB.nopar test.sander.DFTB \
	test.sander.EXTERN test.sander.Quick \
	test.sander.TeraChem \
	test.sander.ABFQMMM \
	test.sander.DFTBPLUS \
	test.sander.XTB \
	test.sander.DEEPMDKIT \
	test.sander.QMMM.DLFIND

test.serial.sander: test.serial.sander.MM test.serial.QMMM

test.serial.gem.pmemd: test.gem.pmemd.$(PMEMD_GEM)

test.parallel.gem.pmemd: test.gem.pmemd.MPI.$(PMEMD_GEM)

######    Intermediate-level targets for Amber:    ##################

test.serial.pmemd: test.serial.pmemd.basic test.serial.pmemd.TI \
	test.serial.emil.pmemd test.serial.pmemd.nfe  \
	test.serial.pmemd.amd test.serial.pmemd.kmmd  \
	test.serial.pmemd.middle-scheme

test.parallel.pmemd: test.parallel.pmemd.basic test.parallel.pmemd.TI \
	test.pmemd.REM test.parallel.pmemd.nfe test.pmemd.neb \
	test.parallel.pmemd.amd test.parallel.pmemd.mbar test.parallel.pmemd.kmmd \
	test.parallel.pmemd.middle-scheme

test.cuda.serial2: test.pmemd.cuda test.sander.Quick.cuda

test.parallel.cuda: test.pmemd.cuda.MPI test.sander.Quick.cuda.MPI

test.hip.serial2: test.pmemd.hip test.sander.Quick.hip

test.parallel.hip: test.pmemd.hip.MPI test.sander.Quick.hip.MPI

test.parallel.at:  test.parallel.MM test.parallel.QMMM \
	test.parallel.sander.SEBOMD

######   More specialized rules; not for general use ################

test.parallel.4proc:
	-cd rem_gb_4rep && ./Run.rem
	-cd rrem_gb_4rep_boltzmann && ./Run.rem
	-cd rrem_gb_4rep_nonboltzmann && ./Run.rem
	-cd PIMD/full_cmd_water/equilib && ./Run.full_cmd
	-cd PIMD/full_cmd_water/start && ./Run.full_cmd
	-cd PIMD/full_cmd_water/restart && ./Run.full_cmd
	-cd PIMD/full_nmpimd_water && ./Run.full_pimd
	-cd PIMD/full_pimd_ln_water && ./Run.full_pimd_ln
	-cd PIMD/full_pimd_nhc_water && ./Run.full_pimd_nhc
	-cd PIMD/full_pimd_ntp_water && ./Run.full_pimd_ntp
	-cd PIMD/full_rpmd_water && ./Run.full_rpmd
	-cd nfe && ./run-parallel.sh

test.parallel.MM: test.sander.BASIC.MPI test.sander.GB.MPI \
	test.sander.REM test.sander.TI test.sander.LES.MPI \
	test.neb test.parallel.sander.nfe test.sander.CHARMM.MPI \
	test.sander.PIMD.MPI.partial test.sander.PIMD.MPI.full \
	test.sander.constph.MPI test.sander.conste.MPI \
	test.sander.constphe.MPI test.sander.pgm.MPI test.sander.RISM.MPI \
	test.sander.crgreloc.MPI test.parallel.sander.AMD \
	test.parallel.sander.sgld test.parallel.sander.emap \
	test.sander.OIN.MPI test.sander.SINR.MPI test.sander.music.MPI \
	test.sander.middle-scheme.MPI test.parallel.sander.kmmd \
	test.sander.TFE.MPI

test.parallel.QMMM: \
	test.sander.QMMM.MPI test.sander.DFTB.MPI test.sander.EXTERN.MPI \
	test.sander.ADQMMM.MPI test.sander.ABFQMMM.MPI test.sander.Quick.MPI \
	test.sander.TeraChem.MPI test.sander.DFTBPLUS.MPI test.sander.XTB.MPI \
	test.sander.DEEPMDKIT.MPI

test.parallel.EVB:  test.sander.EVB

######    Individual targets, for specialized use:    ######################
# GBNSR6
test.serial.mmpbsa_py:
	-cd mmpbsa_py && chmod +x ./Run.sh && python3 test.py

test.sander.BASIC.nopar:
	-cd dmp && ./Run.dmp
	-cd adenine && ./Run.adenine
	-cd variable_14 && ./Run.variable_14_igb1
	-cd rdc && ./Run.nef
	-cd pgm_4wat && ./Runw4_gas

test.sander.BASIC:
	-cd cytosine && ./Run.cytosine
	-cd nonper && ./Run.nonper
	-cd nonper && ./Run.egb6
	-cd nonper && ./Run.nonper.belly
	-cd nonper && ./Run.nonper.belly.mask
	-cd nonper && ./Run.nonper.min
	-cd nonper && ./Run.cap
	-cd nonper && ./Run.nonper.nocut
	-cd tip4p && ./Run.tip4p
	-cd tip4p && ./Run.tip4p_mcbar
	-cd tip4p && ./Run.tip4p_nve
	-cd tip5p && ./Run.tip5p
	-cd tip5p && ./Run.tip5p_nve
	-cd 4096wat && ./Run.pure_wat
	-cd 4096wat && ./Run.pure_wat_fswitch
	-cd 4096wat && ./Run.pure_wat_nmr_temp_reg
	-cd 4096wat && ./Run.vrand
	-cd 4096wat && ./Run.frcdmp
	-cd 4096wat_oct && ./Run.pure_wat_oct
	-cd dhfr && ./Run.dhfr && ./Run.dhfr prmtop_an
	-cd dhfr && ./Run.dhfr.noboxinfo
	-cd dhfr && ./Run.dhfr.noshake
	-cd dhfr && ./Run.dhfr.ntx
	-cd dhfr && ./Run.dhfr.bussi
	-cd dhfr && ./Run.dhfr.min
	-cd dhfr && ./Run.dhfr.min_prcg
	-cd dhfr && ./Run.dhfr.xmin
	-cd ff14ipq && ./Run.ff14ipq
	-cd variable_14 && ./Run.variable_14_ntb1
	-cd gact_ips && ./Run.ips
	-cd gact_ips && ./Run.ipsnve
	-cd gact_ips && ./Run.ips_dfft
	-cd gact_ips && ./Run.ips_vacuum
	-cd polarizable_water && ./Run.pol_wat
	-cd ubiquitin && ./Run.ubiquitin
	-cd dna_pol && ./Run.dna_pol
	-cd trx && ./Run.trx
	-cd trx && ./Run.trx.cpln
	-cd rdc && ./Run.dip
	-cd rdc && ./Run.csa
	-cd rdc && ./Run.csa_min
	-cd rdc && ./Run.nmr
	-cd pcsa && ./Run.dip
	-cd pcsa && ./Run.csa
	-cd pcsa && ./Run.csa2
	-cd pcsa && ./Run.csa_min
	-cd tgtmd/change_target && ./Run.tgtmd
	-cd tgtmd/change_target.rms && ./Run.tgtmd
	-cd tgtmd/change_target.ntr && ./Run.tgtmd
	-cd tgtmd/conserve_ene && ./Run.tgtmd
	-cd tgtmd/minimize && ./Run.tgtmin
	-cd tgtmd/PME && ./Run.tgtPME
	-cd mtmdtest && ./Run.mtmdtest
	-cd trajene && ./Run.trajene
	-cd trajene_box && ./Run.trajene
	-cd trajene_netcdf && ./Run.trajene $(NETCDF)
	-cd alp && ./Run.alp
	-cd umbrella && ./Run.umbrella
	-cd noesy && ./Run.noesy
	-cd jar && ./Run.jarz
	-cd plane_plane_restraint && ./Run.dinuc_plpt
	-cd plane_plane_restraint && ./Run.dinuc_pln
	-cd iwrap2 && ./Run.iwrap2
	-cd idecomp1 && ./run_idecomp1.sh
	-cd idecomp4 && ./run_idecomp4.sh
	-cd bintraj && ./Run.bintraj $(NETCDF)
	-cd netcdf && $(MAKE) -k test OPT=$(NETCDF)
	-cd velocity_write && ./Run.vel1
	-cd velocity_write && ./Run.vel2
#    Constant surface tension (csurften > 0)
	-cd csurften && ./Run.csurften_z-dir
#    Semi-isotropic pressure coupling (csurften > 0 AND ntp = 3)
	-cd csurften && ./Run.csurften_z-dir_npt_3
#    Solvation Energy via LIE theory
	-cd linear_interaction_energy && ./Run.lie
#    NMR Opt Test Cases
	-cd nmropt && $(MAKE) all
#    LJ 12-6-4 potential test
	-cd lj_12-6-4 && ./Run.12-6-4
#    Directional pressure scaling (baroscalingdir > 0)
	-cd baroscalingdir && ./Run.baroscalingdir_z-dir
#    test ff19SB
	-cd ff19SB && ./Run.sander

test.sander.BASIC.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.BASIC
	-export TESTsander=$(BINDIR)/sander.MPI; cd 4096wat && ./Run.column_fft
	-export TESTsander=$(BINDIR)/sander.MPI; cd jar_multi && ./Run.jarz
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_eth2meth_gas && ./Run.test1
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_eth2meth_gas && ./Run.test2
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_ggcc && ./Run.test1
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_ggcc && ./Run.test2
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_mpi/phosphate && ./Run.mp

test.sander.GB:
	-cd gb_rna && ./Run.gbrna
	-cd gb_rna && ./Run.gbrna.min
	-cd gb_rna && ./Run.gbrna.ln
	-cd gb_rna && ./Run.gbrna.ips
	-cd gbsa_xfin && ./Run.gbsa1
	-cd circ_dna && ./Run.circdna
	-cd gb2_trx && ./Run.trxox
	-cd gb7_trx && ./Run.trxox && ./Run.trxox prmtop_an
	-cd gb7_trx && ./Run.trxox_md
	-cd gb8_trx && ./Run.trxox
	-cd gb8_trx && ./Run.trxox_md && ./Run.trxox_md prmtop_an
	-cd gbneck2nu/1hji && ./Run.1hji_md
	-cd gbneck2nu/modified_nu/3p4a/ && ./Run.3p4a
	-cd alpb_trx && ./Run.trxox
#	-cd gb1_cox2 && ./Run.cox2

test.sander.TFE:
	-cd gbsa_tfe && ./Run.gbsa1_tfe

test.sander.pgm:
	-cd pgm_512wat    && ./Run.min
	-cd pgm_512wat    && ./Run.nve
	-cd pgm_512wat    && ./Run.npt

test.sander.pgm.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.pgm

test.serial.sander.SEBOMD:
	-cd sebomd/AM1/dimethylether       && ./min.csh && ./md.csh
	-cd sebomd/AM1/methionine          && ./min.csh && ./md.csh
	-cd sebomd/AM1/n-methyl-acetamide  && ./min.csh && ./md.csh
	-cd sebomd/AM1/nucleoside          && ./min.csh && ./md.csh
	-cd sebomd/AM1/water1              && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-PhoT/dimethylether      && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-PhoT/methionine         && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-PhoT/n-methyl-acetamide && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-PhoT/nucleoside         && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-PhoT/water1             && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-CB1/dimethylether      && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-CB1/n-methyl-acetamide && ./min.csh && ./md.csh
	-cd sebomd/AM1-d-CB1/water1             && ./min.csh && ./md.csh
	-cd sebomd/DC/water32              && ./min.csh && ./md.csh
	-cd sebomd/Ewald-CM1/Water2        && ./md.csh
	-cd sebomd/Ewald-ConstantCharge/Water2   && ./md.csh
	-cd sebomd/Ewald-Mulliken/Water2   && ./md.csh
	-cd sebomd/MinimumImage/Water2     && ./md.csh
	-cd sebomd/method3/alaninedipeptide  && ./min.csh && ./md.csh
	-cd sebomd/method3/ethanol_and_water && ./min.csh && ./md.csh
	-cd sebomd/MNDO/dimethylether      && ./min.csh && ./md.csh
	-cd sebomd/MNDO/methionine         && ./min.csh && ./md.csh
	-cd sebomd/MNDO/n-methyl-acetamide && ./min.csh && ./md.csh
	-cd sebomd/MNDO/nucleoside         && ./min.csh && ./md.csh
	-cd sebomd/MNDO/water1             && ./min.csh && ./md.csh
	-cd sebomd/RM1/dimethylether       && ./min.csh && ./md.csh
	-cd sebomd/RM1/methionine          && ./min.csh && ./md.csh
	-cd sebomd/RM1/n-methyl-acetamide  && ./min.csh && ./md.csh
	-cd sebomd/RM1/nucleoside          && ./min.csh && ./md.csh
	# -cd sebomd/RM1/water1              && ./min.csh && ./md.csh
	-cd sebomd/RM1/water1              && ./md.csh
	-cd sebomd/PIF2/dimethylether      && ./min.csh && ./md.csh
	-cd sebomd/PIF2/water1             && ./min.csh && ./md.csh
	-cd sebomd/PIF2/doublewater        && ./min.csh && ./md.csh
	-cd sebomd/PIF2/ethanol_and_water  && ./min.csh && ./md.csh
	-cd sebomd/PIF3/water1             && ./min.csh && ./md.csh
	-cd sebomd/PIF3/doublewater        && ./min.csh && ./md.csh
	-cd sebomd/PIF3/ethanol_and_water  && ./min.csh && ./md.csh
	-cd sebomd/PM3/alaninedipeptide    && ./min.csh && ./md.csh
	-cd sebomd/PM3/dimethylether       && ./min.csh && ./md.csh
	-cd sebomd/PM3/methionine          && ./min.csh && ./md.csh
	-cd sebomd/PM3/n-methyl-acetamide  && ./min.csh && ./md.csh
	-cd sebomd/PM3/nucleoside          && ./min.csh && ./md.csh
	-cd sebomd/PM3/water1              && ./min.csh && ./md.csh

test.parallel.sander.SEBOMD:
	-export TESTsander=$(BINDIR)/sander.MPI; cd sebomd/DC/water32 && ./min.csh && ./md.csh

test.sander.constph:
	cd cnstph/implicit && ./Run.cnstph
	cd cnstph/explicit && ./Run.cnstph

test.sander.conste:
	cd cnste/implicit && ./Run.cnste
	cd cnste/explicit && ./Run.cnste

test.sander.constphe:
	cd cnstphe/implicit && ./Run.cnstphe
	cd cnstphe/explicit && ./Run.cnstphe
	cd cnstphe_merged/implicit && ./Run.cnstphe
	cd cnstphe_merged/explicit && ./Run.cnstphe

test.sander.constph.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph/implicit && ./Run.cnstph
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph/explicit && ./Run.cnstph
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/TempRem && ./Run.cnstph_remd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREM && ./Run.pHremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREMrst && ./Run.pHremdrst
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/Explicit_pHREM && ./Run.pHremd

test.sander.conste.MPI:
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste/implicit && ./Run.cnste
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste/explicit && ./Run.cnste
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste_remd/TempRem && ./Run.cnste_remd
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste_remd/EREM && ./Run.Eremd
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste_remd/EREMrst && ./Run.Eremdrst
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnste_remd/Explicit_EREM && ./Run.Eremd

test.sander.constphe.MPI:
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnstphe/implicit && ./Run.cnstphe
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnstphe/explicit && ./Run.cnstphe
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnstphe_merged/implicit && ./Run.cnstphe
	-export TESTsander=$(AMBERHOME)/bin/sander.MPI; cd cnstphe_merged/explicit && ./Run.cnstphe

test.sander.GB.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.GB

test.sander.TFE.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.TFE

test.sander.CHARMM:
	-cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.min
	-cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.md
	-cd chamber/md_engine/dhfr_cmap && ./Run.dhfr_charmm.min
	-cd chamber/md_engine/dhfr_cmap && ./Run.dhfr_charmm.md
	-cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.min
	-cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.md
	-cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.min
	-cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.md

test.sander.CHARMM.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.CHARMM

#  following are parallel only:
test.sander.TI:
	-export TESTsander=$(BINDIR)/sander.MPI; cd sodium && ./Run.sodium
	-export TESTsander=$(BINDIR)/sander.MPI; cd pheMTI && ./Run.0
	-export TESTsander=$(BINDIR)/sander.MPI; cd pheMTI && ./Run.1
	-export TESTsander=$(BINDIR)/sander.MPI; cd pheMTI && ./Run.lambda0
	-export TESTsander=$(BINDIR)/sander.MPI; cd pheMTI && ./Run.lambda1
	-export TESTsander=$(BINDIR)/sander.MPI; cd campTI && ./Run.campTI
	-export TESTsander=$(BINDIR)/sander.MPI; cd softcore && ./Run_sc
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_decomp; ./Run.ti_decomp
	-export TESTsander=$(BINDIR)/sander.MPI; cd ti_decomp; ./Run.ti_decomp_sc

#  following are parallel only:
test.sander.EVB:
	-cd evb/malon_bond_umb_GAFF && ./Run.evb
	-cd evb/malon_bond_umb_GAFF_MORSIFY && ./Run.evb
	-cd evb/malon_bond_umb_GAFF_MORSIFY_XVDW && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_nmpimd_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_pimd_ld_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_pimd_nhc_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_EXP-XCH && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_EXP-XCH_pimd_ld_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_EXP-XCH_pimd_nhc_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_EXP-XCH_nmpimd_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_GAUSS-XCH && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_GAUSS-XCH_pimd_ld_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_GAUSS-XCH_pimd_nhc_full && ./Run.evb
	-cd evb/malon_dbonds_umb_GAFF_MORSIFY_XVDW_GAUSS-XCH_nmpimd_full && ./Run.evb
	-cd evb/malon_emap_GAFF_MORSIFY && ./Run.evb
	-cd evb/malon_emap_GAFF_MORSIFY_XVDW && ./Run.evb
	-cd evb/malon_bond_umb_dg_UFF_3DG && ./Run.evb
	-cd evb/malon_bond_umb_dg_UFF_3DG_nmpimd_full && ./Run.evb
	-cd evb/malon_bond_umb_dg_UFF_3DG_pimd_ld_full && ./Run.evb
	-cd evb/malon_bond_umb_dg_UFF_3DG_pimd_nhc_full && ./Run.evb
	-cd evb/malon_bond_umb_dg_UFF_3DG_pimd_nhc_full_TI-MASS && ./Run.evb
	-cd evb/malon_dbond_umb_dg_UFF_3DG_pimd_nhc_full_TI-MASS && ./Run.evb
	-cd evb/malon_dbonds_umb_dg_UFF_3DG_qi_full_2D-PMF && ./Run.evb
	-cd evb/malon_dbonds_umb_dg_UFF_3DG_qi_full_corrF && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_3DG && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_9DG && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_9DG_pimd_ld_full && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_9DG_pimd_nhc_full && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_9DG_nmpimd_full && ./Run.evb
	-cd evb/poh_dbonds_umb_dg_UFF_9DG_nmpimd_full_TST-freqf && ./Run.evb

test.sander.EVBDEBUG:
	-cd evb_debug/hcn_dg_cart && ./Run.evb
	-cd evb_debug/hcn_dg_cart_irc && ./Run.evb
	-cd evb_debug/hcn_dg_cart_irc_dgelsd && ./Run.evb
	-cd evb_debug/hcn_dg_cart_irc_dgelsy && ./Run.evb
	-cd evb_debug/hcn_dg_int_irc_grad && ./Run.evb
	-cd evb_debug/poh_EVB_CART_DIIS && ./Run.evb
	-cd evb_debug/poh_EVB_INT_DIIS && ./Run.evb
	-cd evb_debug/poh_gfchk_GMRES && ./Run.evb
	-cd evb_debug/poh_gfchk_GMRES_K3_R32_UFF_dyn && ./Run.evb
	-cd evb_debug/poh_gfchk_GMRES_K5_R32_UFF_dyn && ./Run.evb
	-cd evb_debug/poh_gfchk_GMRES_K7_R32_UFF_dyn && ./Run.evb
	-cd evb_debug/poh_gfchk_GMRES_K9_R32_UFF_dyn && ./Run.evb

test.sander.LES:
	-cd LES_noPME && ./Run.LESmd
	-cd LES_noPME && ./Run.LESmd.rdiel
	-cd LES && ./Run.PME_LES
	-cd LES_CUT && ./Run.LES
	-cd LES_TEMP && ./Run.2temp
	-cd LES_GB && ./Run.LES

test.sander.LES.MPI:
	export TESTsanderLES=$(BINDIR)/sander.LES.MPI; $(MAKE) -k test.sander.LES

test.sander.lmod:
#   don't run the sander lmod tests by default: they tend to diverge
	-cd vancomycin_lmod && ./Run.vancomycin_lmod
	-cd trpcage_lmod && ./Run.lmod
	-cd vancomycin_lmod_dock && ./Run.vancomycin_lmod_dock

test.sander.QMMM.nopar:
	-cd qmmm2/input_validation && ./Run.invalid_atom_ids
	-cd qmmm2/input_validation && ./Run.non_unique_qm_atoms
	-cd qmmm2/pure_QM_MD && ./Run.nma
	-cd qmmm2/pure_QM_MD && ./Run.nma_md
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_0
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_2
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_3
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_4
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_5
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_6
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_diag_routine_7
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_qmgb0
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_qmgb1
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_qmgb2
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_qmgb2_saltcon
	-cd qmmm2/pure_QM_MD && ./Run.nma_md_qmgb3
	-cd qmmm2/pure_QM_MD && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_shake && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_tight_p && ./Run.nma
	-cd qmmm2/pure_QM_MD_tight_p && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_PDDGPM3 && ./Run.nma
	-cd qmmm2/pure_QM_MD_PDDGPM3 && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_PDDGPM3 && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_PDDGPM3_08 && ./Run.nma
	-cd qmmm2/pure_QM_MD_PDDGPM3_08 && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_PDDGMNDO && ./Run.nma
	-cd qmmm2/pure_QM_MD_PDDGMNDO && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_PDDGMNDO && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_AM1 && ./Run.nma
	-cd qmmm2/pure_QM_MD_AM1 && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_AM1 && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_AM1_ADDMM && ./Run.nma
	-cd qmmm2/pure_QM_MD_AM1_ADDMM && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_RM1 && ./Run.nma
	-cd qmmm2/pure_QM_MD_RM1 && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_RM1 && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_MNDO && ./Run.nma
	-cd qmmm2/pure_QM_MD_MNDO && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_MNDO && ./Run.C6H4FCL_md
	-cd qmmm2/pure_QM_MD_PM6 && ./Run.nma
	-cd qmmm2/pure_QM_MD_PM6 && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_NUMER_DERIV && ./Run.nma
	-cd qmmm2/pure_QM_MD_NUMER_DERIV && ./Run.nma_md
	-cd qmmm2/pure_QM_MD_NUMER_DERIV && ./Run.nma_md_qmgb0
	-cd qmmm2/pure_QM_MD_NUMER_DERIV && ./Run.nma_md_qmgb2
	-cd qmmm2/pure_QM_MD_NUMER_DERIV && ./Run.nma_md_qmgb2_saltcon
	-cd qmmm2/1-2-ethanediol_PM3CARB1 && ./Run.PM3CARB1_md
	-cd qmmm2/lysine_PM3 && ./Run.lysine
	-cd qmmm2/lysine_PM3 && ./Run.lysine_md
	-cd qmmm2/lysine_PM3 && ./Run.lysine_md_qmmm_int0
	-cd qmmm2/lysine_PM3 && ./Run.lysine_md_qmmm_int2
	-cd qmmm2/lysine_PM3 && ./Run.lysine_md_lnk_dis_neg
	-cd qmmm2/lysine_PM3 && ./Run.lysine_md_lnk_method2
	-cd qmmm2/lysine_PM3_qmgb0 && ./Run.lysine
	-cd qmmm2/lysine_PM3_qmgb0 && ./Run.lysine_md
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_igb2
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_igb5
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_igb7
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_adjust_q1
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_adjust_q2
	-cd qmmm2/lysine_PM3_qmgb2 && ./Run.lysine_md_lnk_dis_neg
	-cd qmmm2/lysine_PM3_qmgb2_alpb && ./Run.lysine_md
	-cd qmmm2/lysine_PM3_calc_mulliken && ./Run.lysine
	-cd qmmm2/lysine_PM3_calc_mulliken && ./Run.lysine_md
	-cd qmmm2/lysine_PM3_calc_dipole && ./Run.lysine
	-cd qmmm2/lysine_PM3_calc_dipole && ./Run.lysine_md
	-cd qmmm2/lysine_PM3_calc_dipole && ./Run.lysine_qmmm
	-cd qmmm2/lysine_AM1 && ./Run.lysine
	-cd qmmm2/lysine_AM1 && ./Run.lysine_md
	-cd qmmm2/lysine_MNDO && ./Run.lysine
	-cd qmmm2/lysine_MNDO && ./Run.lysine_md
	-cd qmmm2/lysine_PM6 && ./Run.lysine
	-cd qmmm2/lysine_PM6 && ./Run.lysine_md
	-cd qmmm2/meoh-nh3_PM6-DH+ && ./Run.meoh-nh3
	-cd qmmm2/meoh-nh3_PM6-DH+ && ./Run.meoh-nh3_md
	-cd qmmm2/PM3-MMX && ./Run.water_dimer.x
	-cd qmmm2/PM3-MMX && ./Run.ammonia_dimer.x
	-cd qmmm2/PM3-MMX && ./Run.formic_acid_dimer.x
	-cd qmmm2/PM3-MMX2 && ./Run.water_dimer.x
	-cd qmmm2/PM3-MMX2 && ./Run.ammonia_dimer.x
	-cd qmmm2/PM3-MMX2 && ./Run.formic_acid_dimer.x
	-cd qmmm2/PM3-MMX2 && ./Run.methanethiol.x
	-cd qmmm2/znme2/ && ./Run.min
	-cd qmmm2/znme2/ && ./Run.md
	-cd qmmm2/cysdip/ && ./Run.mndod.min
	-cd qmmm2/cysdip/ && ./Run.mndod.md
	-cd qmmm2/cysdip/ && ./Run.mndod-mm.min
	-cd qmmm2/cysdip/ && ./Run.mndod-mm.md

test.sander.QMMM:
	-cd qmmm2/xcrd_build_test/ && ./Run.oct_nma_imaged
	-cd qmmm2/xcrd_build_test/ && ./Run.oct_nma_noimage
	-cd qmmm2/xcrd_build_test/ && ./Run.ortho_qmewald0
	-cd qmmm2/xcrd_build_test/ && ./Run.truncoct_qmewald0
	-cd qmmm2/crambin_2 && ./Run.crambin
	-cd qmmm2/crambin_2 && ./Run.crambin_md
	-cd qmmm2/crambin_2 && ./Run.crambin_md_calc_mulliken
	-cd qmmm2/crambin_2 && ./Run.crambin_md_qmgb2
	-cd qmmm2/crambin_2 && ./Run.crambin_md_qmgb2_alpb
	-cd qmmm2/crambin_2 && ./Run.crambin_md_qmgb2_aq1
	-cd qmmm2/crambin_2 && ./Run.crambin_md_qmgb2_aq2
	-cd qmmm2/crambin_2 && ./Run.crambin_md_qmgb2_saltcon
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_internal
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dspev
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dspevd
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dspevx
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dsyev
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dsyevd
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_dsyevr
	-cd qmmm2/1NLN_test_diagonalizers && ./Run.1NLN_auto
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_min
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_aq1
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_aq2
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_mmcorr
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_qmewald2
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb2
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_aq2_NUMER_DERIV
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_lnk_dis_neg
	-cd qmmm2/1NLN_periodic_lnk_atoms && ./Run.1NLN_MD_ntb1_lnk_method2
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.notimaged
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.notimaged_md
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.notimaged_md_pme
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.notimaged_md_pme_qmewald
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.notimaged_md_pme_qmewald_lowmem
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.imaged
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.imaged_md
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.img_center
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.img_center_md
	-cd qmmm2/MG_QM_water_MM_AM1_periodic && ./Run.img_center_bigqmcut_md
	-cd qmmm2/crambin && ./Run.crambin
	-cd qmmm2/crambin && ./Run.crambin_md_hot_start
	-cd qmmm2/crambin && ./Run.crambin_md
	-cd qmmm2/tip3p_cap && ./Run.tip3p_cap
	-cd qmmm2/tip3p_cap && ./Run.tip3p_cap_md
	-cd qmmm2/tip3p_cap && ./Run.tip3p_cap_md.shake
	-cd qmmm2/tip3p_cap && ./Run.tip3p_cap_md.shake_qmshakeoff
	-cd qmmm2/MG_QM_water_MM_AM1_qmcut && ./Run.MG_QM_water_MM
	-cd qmmm2/MG_QM_water_MM_AM1_qmcut && ./Run.MG_QM_water_MM_MD
	-cd qmmm2/MG_QM_water_MM_AM1_qmcut_lowmem && ./Run.MG_QM_water_MM_MD
	-cd qmmm2/MG_QM_water_MM_AM1_qmcut_ADDMM && ./Run.MG_QM_water_MM
	-cd qmmm2/MG_QM_water_MM_AM1_qmcut_ADDMM && ./Run.MG_QM_water_MM_MD
	-cd qmmm2/variable_solvent && ./Run.mg_periodic_vsolv_wat
	-cd qmmm2/variable_solvent && ./Run.1NLN_MD_ntb1_vsolv
	-cd qmmm2/PM3-MMX && ./Run.crambin_md_pm3mmx
	-cd qmmm2/PM3-MMX2 && ./Run.crambin_md_pm3mmx2
	-cd qmmm2/crambin_PM6 && ./Run.crambin
	-cd qmmm2/crambin_PM6 && ./Run.crambin_md
	-cd qmmm2/PM3-MAIS && ./Run.zundel
	-cd qmmm2/PM3-MAIS && ./Run.hcl_wat
	-cd qmmm2/MechEm_nma-spcfwbox && ./Run.MechEm_PDDGPM3
	-cd qmmm2/qmmm_switching_func && ./Run.nma_md_switching
	-cd qmmm_wrap/splitwrap && ./Run.splitwrap
	-cd qmmm_wrap/wideqm && ./Run.wideqm

test.sander.QMMM.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.QMMM

test.sander.DFTB.nopar:
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_md
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_md_qmgb0
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_md_qmgb1
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_md_qmgb2
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_md_qmgb2_saltcon
	-cd qmmm_DFTB/pure_QM_MD_DFTB && ./Run.nma_disp
	-cd qmmm_DFTB/pure_QM_MD_shake_DFTB && ./Run.nma_md
	-cd qmmm_DFTB/pure_QM_MD_tight_p_DFTB && ./Run.nma
	-cd qmmm_DFTB/pure_QM_MD_tight_p_DFTB && ./Run.nma_md
	-cd qmmm_DFTB/lysine_DFTB && ./Run.lysine
	-cd qmmm_DFTB/lysine_DFTB && ./Run.lysine_md
	-cd qmmm_DFTB/lysine_DFTB && ./Run.lysine_md_lnk_dis_neg
	-cd qmmm_DFTB/lysine_DFTB && ./Run.lysine_md_lnk_method2
	-cd qmmm_DFTB/lysine_DFTB && ./Run.lysine_md_qmmm_int0
	-cd qmmm_DFTB/lysine_DFTB_qmgb0 && ./Run.lysine
	-cd qmmm_DFTB/lysine_DFTB_qmgb0 && ./Run.lysine_md
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md_igb2
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md_igb5
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md_igb7
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md_adjust_q1
	-cd qmmm_DFTB/lysine_DFTB_qmgb2 && ./Run.lysine_md_adjust_q2
	-cd qmmm_DFTB/lysine_DFTB_qmgb2_alpb && ./Run.lysine_md
	-cd qmmm_DFTB/lysine_DFTB_calc_mulliken && ./Run.lysine
	-cd qmmm_DFTB/lysine_DFTB_calc_mulliken && ./Run.lysine_md
	-cd qmmm_DFTB/3rd-order/ala8  && ./Run.ala8_PA
	-cd qmmm_DFTB/3rd-order/ala8  && ./Run.ala8_PR
	-cd qmmm_DFTB/3rd-order/water && ./Run.water
	-cd qmmm_DFTB/3rd-order/water && ./Run.water_read_mdin
	-cd qmmm_DFTB/3rd-order/water && ./Run.water_read_file
	-cd qmmm_DFTB/dftb3/water && ./Run.h2o.go
	-cd qmmm_DFTB/dftb3/water && ./Run.h2o.md

test.sander.DFTB:
	-cd qmmm_DFTB/crambin_DFTB && ./Run.crambin
	-cd qmmm_DFTB/crambin_DFTB && ./Run.crambin_md_hot_start
	-cd qmmm_DFTB/crambin_DFTB && ./Run.crambin_md
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_calc_mulliken
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_qmgb2
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_qmgb2_alpb
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_qmgb2_aq1
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_qmgb2_aq2
	-cd qmmm_DFTB/crambin_2_DFTB && ./Run.crambin_md_qmgb2_saltcon
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_ewald_ntb1
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_ewald_ntb1_link_atoms
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_ewald_ntb1_qmewald2
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_ewald_ntb2
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb1
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2_link_atoms
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2_link_atoms_aq1
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2_link_atoms_aq2
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2_qmewald2
	-cd qmmm_DFTB/aladip_tip3p_ewaldpme && ./Run.aladip_pme_ntb2_telec
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_qmcut && ./Run.MG_QM_water_MM
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_qmcut && ./Run.MG_QM_water_MM_MD
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.notimaged
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.notimaged_md
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.notimaged_md_pme
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.notimaged_md_pme_qmewald
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.imaged
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.imaged_md
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.img_center
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.img_center_md
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_periodic && ./Run.img_center_bigqmcut_md
	-cd qmmm_DFTB/MG_QM_water_MM_DFTB_qmcut_lowmem && ./Run.MG_QM_water_MM_MD
	-cd qmmm_DFTB/tip3p_cap_DFTB && ./Run.tip3p_cap
	-cd qmmm_DFTB/tip3p_cap_DFTB && ./Run.tip3p_cap_md
	-cd qmmm_DFTB/tip3p_cap_DFTB && ./Run.tip3p_cap_md.shake
	-cd qmmm_DFTB/tip3p_cap_DFTB && ./Run.tip3p_cap_md.shake_qmshakeoff
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_min
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_lnk_dis_neg
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_lnk_method2
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_aq1
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_aq1_disp
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_aq2
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb1_qmewald2
	-cd qmmm_DFTB/1NLN_periodic_lnk_atoms_DFTB && ./Run.1NLN_MD_ntb2
	-cd qmmm_DFTB/3rd-order/ala8 && ./Run.ala8_PA
	-cd qmmm_DFTB/3rd-order/ala8 && ./Run.ala8_PR
	-cd qmmm2/MechEm_nma-spcfwbox && ./Run.MechEm_DFTB
	-cd qmmm_DFTB/dftb3/nma-h2o-box && ./Run.nma-spcfw-15.md

test.sander.DFTB.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.DFTB

# following are parallel only
test.sander.ADQMMM.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI && cd qmmm2/adqmmm_na+28water && ./Run.adqmmm
	-export TESTsander=$(BINDIR)/sander.MPI && cd qmmm2/adqmmm_na+28water && ./Run.adqmmm-calc_wbk2
	-export TESTsander=$(BINDIR)/sander.MPI && cd qmmm2/adqmmm_na+28water && ./Run.adqmmm-fixedR
	-export TESTsander=$(BINDIR)/sander.MPI && cd qmmm2/adqmmm_h2o-box && ./Run.adqmmm
	-export TESTsander=$(BINDIR)/sander.MPI && cd qmmm2/adqmmm_h2o-box && ./Run.adqmmm-fixedR-calc_wbk2

test.sander.ABFQMMM:
	-cd abfqmmm/abfqmmm_water_sp && ./Run.abfqmmm_water_sp
	-cd abfqmmm/abfqmmm_water_md && ./Run.abfqmmm_water_md
	-cd abfqmmm/abfqmmm_dmpoh_md && ./Run.abfqmmm_dmpoh_md
	-cd abfqmmm/abfqmmm_lysozyme_md && ./Run.abfqmmm_lysozyme_md
	-cd abfqmmm/adqmmm_water_md && ./Run.adqmmm_water_md
	-cd abfqmmm/hotspot_water_md && ./Run.hotspot_water_md

test.sander.ABFQMMM.MPI:
	 export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.ABFQMMM

test.sander.Quick:
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/pure_QM && ./Run.h2o.blyp_6-31g ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/pure_QM && ./Run.h2o.blyp_6-31g_md ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/pure_QM && ./Run.h2o.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/QMMM_MD && ./Run.aladip.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/QMMM_MD && ./Run.aladip.hf_sto-3g.MechEm ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g ;\
	fi ;\
	)
#	@(if [ "$(QUICK)" = 'yes' ]; then \
#    cd qmmm_Quick/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g.MechEm ;\
#	fi ;\
#	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/QMMM_MD_cEw && ./Run.water-qmmm-cew ;\
	fi ;\
	)
	@(if [ "$(QUICK)" = 'yes' ]; then \
    cd qmmm_Quick/QMMM_MD_cEw && ./Run.diala-wat-qmmm-cew ;\
	fi ;\
	)

test.sander.Quick.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.Quick

test.sander.Quick.cuda:
	export TESTsander=$(BINDIR)/sander.quick.cuda; $(MAKE) -k test.sander.Quick

test.sander.Quick.cuda.MPI:
	export TESTsander=$(BINDIR)/sander.quick.cuda.MPI; $(MAKE) -k test.sander.Quick

test.sander.Quick.hip:
	export TESTsander=$(BINDIR)/sander.quick.hip; $(MAKE) -k test.sander.Quick

test.sander.Quick.hip.MPI:
	export TESTsander=$(BINDIR)/sander.quick.hip.MPI; $(MAKE) -k test.sander.Quick

test.sander.TeraChem:
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/pure_QM && ./Run.h2o.blyp_6-31g ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/pure_QM && ./Run.h2o.blyp_6-31g_md ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/QMMM_MD && ./Run.aladip.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/QMMM_MD && ./Run.aladip.hf_sto-3g.MechEm ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    cd qmmm_TeraChem/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g.MechEm ;\
	fi ;\
	)

test.sander.TeraChem.MPI:
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/QMMM_MD && ./Run.aladip.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/QMMM_MD && ./Run.aladip.hf_sto-3g.MechEm ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/QMMM_MD && ./Run.nma-spcfw-15.hf_sto-3g.MechEm ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/pure_QM_PIMD && ./Run.h2o.hf_sto-3g.pimd ;\
	fi ;\
	)
	@(if [ "$(TCPB)" = 'yes' ]; then \
    export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_TeraChem/pure_QM_REMD && ./Run.h2o.hf_sto-3g.remd ;\
	fi ;\
	)


test.sander.EXTERN:
	-cd qmmm_EXTERN/pure_QM_MD_ADF && ./Run.h2o.dftb
	-cd qmmm_EXTERN/pure_QM_MD_ADF && ./Run.h2o.dftb_md
	-cd qmmm_EXTERN/pure_QM_MD_ADF && ./Run.h2o.lda-sz
	-cd qmmm_EXTERN/pure_QM_MD_ADF && ./Run.h2o.lda-sz_md
	-cd qmmm_EXTERN/pure_QM_MD_ADF && ./Run.h2o.template.lda-sz
	-cd qmmm_EXTERN/pure_QM_MD_GAMESS && ./Run.h2o.bp86_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_GAMESS && ./Run.h2o.bp86_6-31g_md
	-cd qmmm_EXTERN/pure_QM_MD_GAMESS && ./Run.h2o.template.bp86_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_TeraChem && ./Run.h2o.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_TeraChem && ./Run.h2o.blyp_6-31g_md
	-cd qmmm_EXTERN/pure_QM_MD_TeraChem && ./Run.h2o.template.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_GAUSSIAN && ./Run.h2o.blyp_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_GAUSSIAN && ./Run.h2o.blyp_sto-3g_md
	-cd qmmm_EXTERN/pure_QM_MD_GAUSSIAN && ./Run.h2o.template.blyp_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_Quick && ./Run.h2o.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_Quick && ./Run.h2o.blyp_6-31g_md
	-cd qmmm_EXTERN/pure_QM_MD_Quick && ./Run.h2o.hf_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_Quick && ./Run.h2o.template.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_Orca && ./Run.h2o.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_Orca && ./Run.h2o.blyp_6-31g_md
	-cd qmmm_EXTERN/pure_QM_MD_Orca && ./Run.h2o.template.blyp_6-31g
	-cd qmmm_EXTERN/pure_QM_MD_NWChem && ./Run.h2o.blyp_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_NWChem && ./Run.h2o.blyp_sto-3g_md
	-cd qmmm_EXTERN/pure_QM_MD_Q-Chem && ./Run.h2o.hf_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_Q-Chem && ./Run.h2o.template.blyp_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_Q-Chem && ./Run.h2o.blyp_6-31g_md
	-cd qmmm_EXTERN/pure_QM_MD_MRCC && ./Run.h2o.hf_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_MRCC && ./Run.h2o.template.blyp_sto-3g
	-cd qmmm_EXTERN/pure_QM_MD_MRCC && ./Run.h2o.blyp_6-31g_md
	@(if [ "$(REAXFF_PUREMD)" = 'yes' ]; then \
		/bin/true \ # emit path so that users can see these are reaxff tests ;\
		echo "cd qmmm_EXTERN/pure_QM_MD_ReaxFF && ./Run.benz_water_md.reaxff" ;\
		cd qmmm_EXTERN/pure_QM_MD_ReaxFF && ./Run.benz_water_md.reaxff ;\
		/bin/true \ # pretend that we are not already in this dir ;\
		echo "cd qmmm_EXTERN/pure_QM_MD_ReaxFF && ./Run.benz_water_min.reaxff" ;\
		./Run.benz_water_min.reaxff ;\
	else \
		echo "Skipping REAXFF_PUREMD tests" ;\
	fi ;\
	)
	-cd qmmm_EXTERN/QMMM_MD_ADF && ./Run.aladip.blyp_dz.MechEm
	-cd qmmm_EXTERN/QMMM_MD_ADF && ./Run.nma-spcfw-15.blyp_dz.MechEm
	-cd qmmm_EXTERN/QMMM_MD_Orca && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Orca && ./Run.aladip.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_Orca && ./Run.nma-spcfw-15.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Orca && ./Run.nma-spcfw-15.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_TeraChem && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_TeraChem && ./Run.aladip.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_TeraChem && ./Run.nma-spcfw-15.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_TeraChem && ./Run.nma-spcfw-15.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_GAUSSIAN && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_GAUSSIAN && ./Run.nma-spcfw-15.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Quick && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Quick && ./Run.aladip.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_Quick && ./Run.nma-spcfw-15.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Quick && ./Run.nma-spcfw-15.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_NWChem && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Q-Chem && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Q-Chem && ./Run.aladip.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_Q-Chem && ./Run.nma-spcfw-15.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_Q-Chem && ./Run.nma-spcfw-15.hf_sto-3g.MechEm
	-cd qmmm_EXTERN/QMMM_MD_MRCC && ./Run.aladip.hf_sto-3g
	-cd qmmm_EXTERN/QMMM_MD_MRCC && ./Run.nma-spcfw-15.hf_sto-3g
	@(if [ "$(REAXFF_PUREMD)" = 'yes' ]; then \
		/bin/true \ # emit path so that users can see these are reaxff tests ;\
		echo "cd qmmm_EXTERN/QMMM_MD_ReaxFF/periodic && ./Run.benz_water_md.reaxff" ;\
		cd qmmm_EXTERN/QMMM_MD_ReaxFF/periodic && ./Run.benz_water_md.reaxff ;\
		/bin/true \ # pretend that we are not already in this dir ;\
		echo "cd qmmm_EXTERN/QMMM_MD_ReaxFF/nonperiodic && ./Run.benz_water_md.reaxff" ;\
		cd ../nonperiodic && ./Run.benz_water_md.reaxff ;\
	else \
		echo "Skipping REAXFF_PUREMD tests" ;\
	fi ;\
	)
	-cd qmmm_EXTERN/QMMM_Lio/water && ./Run.water
	-cd qmmm_EXTERN/QMMM_Lio/water && ./Run.td.water
	-cd qmmm_EXTERN/QMMM_Fireball/min && ./Run.min $(FBLIBS)
	-cd qmmm_EXTERN/QMMM_Fireball/md && ./Run.md $(FBLIBS)


test.sander.EXTERN.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_ADF_PIMD && ./Run.h2o.blyp_sz.pimd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_ADF_REMD && ./Run.h2o.blyp_sz.remd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_GAMESS_PIMD && ./Run.h2o.hf_sto-3g.pimd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_GAMESS_REMD && ./Run.h2o.hf_sto-3g.remd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_GAUSSIAN_PIMD && ./Run.h2o.hf_sto-3g.pimd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_GAUSSIAN_REMD && ./Run.h2o.hf_sto-3g.remd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_Q-Chem_PIMD && ./Run.h2o.hf_sto-3g.pimd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_TeraChem_PIMD && ./Run.h2o.hf_sto-3g.pimd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_TeraChem_PIMD && ./Run.h2o.hf_sto-3g.pimd mpi
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_TeraChem_REMD && ./Run.h2o.hf_sto-3g.remd
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/pure_QM_MD_TeraChem_REMD && ./Run.h2o.hf_sto-3g.remd mpi
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/adqmmm_na+28water_TeraChem && ./Run.adqmmm
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/QMMM_Fireball/min && ./Run.min $(FBLIBS)
	export TESTsander=$(BINDIR)/sander.MPI; cd qmmm_EXTERN/QMMM_Fireball/md && ./Run.md $(FBLIBS)



test.sander.DFTBPLUS:
	@(if [ "$(DFTBPLUS)" = 'yes' ]; then \
    cd qmmm_DFTBPLUS/QMMM_MD_DFTBPLUS && ./Run.aladip-dftb2 ;\
	fi ;\
	)
	@(if [ "$(DFTBPLUS)" = 'yes' ]; then \
    cd qmmm_DFTBPLUS/QMMM_MD_DFTBPLUS && ./Run.nma-spcfw-15-dftb2 ;\
	fi ;\
	)
	@(if [ "$(DFTBPLUS)" = 'yes' ]; then \
    cd qmmm_DFTBPLUS/pure_QM_MD_DFTBPLUS && ./Run.nma_md ;\
	fi ;\
	)

test.sander.DFTBPLUS.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.DFTBPLUS


test.sander.XTB:
	@(if [ "$(XTB)" = 'yes' ]; then \
    cd qmmm_XTB/QMMM_MD_XTB && ./Run.aladip-gfn2xtb ;\
	fi ;\
	)
	@(if [ "$(XTB)" = 'yes' ]; then \
    cd qmmm_XTB/QMMM_MD_XTB && ./Run.nma-spcfw-15-gfn2xtb ;\
	fi ;\
	)
	@(if [ "$(XTB)" = 'yes' ]; then \
    cd qmmm_XTB/pure_QM_MD_XTB && ./Run.nma_md ;\
	fi ;\
	)

test.sander.XTB.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.XTB


test.sander.DEEPMDKIT:
	@(if [ "$(DEEPMDKIT)" = 'yes' ]; then \
    cd qmmm_DPRC/QMMM_MD_MNDODDPRC && ./Run.dprc ;\
	fi ;\
	)

test.sander.DEEPMDKIT.MPI:
	export TESTsander=$(BINDIR)/sander.MPI; $(MAKE) -k test.sander.DEEPMDKIT


test.sander.QMMM.DLFIND:
	-cd qmmm_DLFIND/HDLC_LBFGS && ./Run.nma-spcfw-15-dftb2


test.sander.PIMD.partial:
	-cd PIMD/part_pimd_water && ./Run.pimd
	-cd PIMD/part_nmpimd_water && ./Run.nmpimd
	-cd PIMD/part_pimd_helium && ./Run.pimd
	-cd PIMD/part_nmpimd_helium && ./Run.nmpimd
	-cd PIMD/part_nmpimd_ntp && ./Run.nmpimd
	-cd PIMD/part_pimd_spcfw && ./Run.pimd
#	-cd PIMD/part_cmd_water/equilib && ./Run.cmdyn
#	-cd PIMD/part_cmd_water/start && ./Run.cmdyn
#	-cd PIMD/part_cmd_water/restart && ./Run.cmdyn
	-cd PIMD/part_rpmd_water && ./Run.rpmd
	-cd ti_mass/pent_LES_PIMD && ./Run.pentadiene

test.sander.PIMD.MPI.partial:
	export TESTsander=$(BINDIR)/sander.LES.MPI; $(MAKE) -k test.sander.PIMD.partial

test.sander.PIMD.MPI.full:
	cd PIMD/full_cmd_water/equilib && ./Run.full_cmd
	cd PIMD/full_cmd_water/start && ./Run.full_cmd
	cd PIMD/full_cmd_water/restart && ./Run.full_cmd
	cd PIMD/full_nmpimd_water && ./Run.full_pimd
	cd PIMD/full_pimd_ln_water && ./Run.full_pimd_ln
	cd PIMD/full_pimd_nhc_water && ./Run.full_pimd_nhc
	cd PIMD/full_pimd_ntp_water && ./Run.full_pimd_ntp
	cd PIMD/full_rpmd_water && ./Run.full_rpmd
	cd ti_mass/pentadiene && ./Run.pentadiene

test.parallel.sander.4procs:
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_gb_4rep && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_4rep_boltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_4rep_nonboltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/ala3_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/trpcage_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd h_rem && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd multid_remd && ./Run.multirem
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREM && ./Run.pHremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREMrst && ./Run.pHremdrst
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/EREM && ./Run.Eremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/EREMrst && ./Run.Eremdrst
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/Explicit_EREM && ./Run.Eremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd phtremd/explicit && ./Run.phtremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd phtremd/explicitRst && ./Run.phtremdRst

test.parallel.sander.8procs:
	-export TESTsander=$(BINDIR)/sander.MPI; cd ephtremd/explicit && ./Run.ephtremd

test.sander.REM:
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_gb_2rep && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_2rep_boltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_2rep_nonboltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_gb_4rep && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_4rep_boltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rrem_gb_4rep_nonboltzmann && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/ala3_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/trpcage_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_wat && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_wat_pv && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd hrem_wat_pv && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd rem_hybrid && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd h_rem && ./Run.rem
	-export TESTsander=$(BINDIR)/sander.MPI; cd multid_remd && ./Run.multirem
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/TempRem && ./Run.cnstph_remd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREM && ./Run.pHremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/pHREMrst && ./Run.pHremdrst
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnstph_remd/Explicit_pHREM && ./Run.pHremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/TempRem && ./Run.cnste_remd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/EREM && ./Run.Eremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/EREMrst && ./Run.Eremdrst
	-export TESTsander=$(BINDIR)/sander.MPI; cd cnste_remd/Explicit_EREM && ./Run.Eremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd phtremd/implicit && ./Run.phtremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd phtremd/explicit && ./Run.phtremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd phtremd/explicitRst && ./Run.phtremdRst
	-export TESTsander=$(BINDIR)/sander.MPI; cd ephtremd/implicit && ./Run.ephtremd
	-export TESTsander=$(BINDIR)/sander.MPI; cd ephtremd/explicit && ./Run.ephtremd

test.sander.OIN:
	-export TESTsander=$(BINDIR)/sander; cd sander_OIN && ./Run.sander.OIN

test.sander.OIN.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_OIN_MPI && ./Run.sander.OIN.MPI

test.sander.SINR:
	-export TESTsander=$(BINDIR)/sander; cd sinr && ./Run.sander.SINR

test.sander.SINR.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; cd sinr_MPI && ./Run.sander.SINR.MPI

test.sander.music:
	-export TESTsander=$(BINDIR)/sander; cd sander_music/ptsurf-12h2o && ./Run.music-energy
	-export TESTsander=$(BINDIR)/sander; cd sander_music/pt-water-gal17 && ./Run.md
	-export TESTsander=$(BINDIR)/sander; cd sander_music/pt-water-vsgal17 && ./Run.md
	-export TESTsander=$(BINDIR)/sander; cd sander_music/gal17-barostat && ./Run.md
	-export TESTsander=$(BINDIR)/sander; cd sander_music/gal17-electrostatics && ./Run.shiCoushoCor
	-export TESTsander=$(BINDIR)/sander; cd sander_music/gal17-electrostatics && ./Run.pme
	-export TESTsander=$(BINDIR)/sander; cd sander_music/gal17-electrostatics && ./Run.shiftC


test.sander.music.MPI:
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/pt-water-gal17 && ./Run.md
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/pt-water-vsgal17 && ./Run.md
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/gal17-TI && ./Run.ti
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/gal17-barostat && ./Run.md
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/gal17-electrostatics && ./Run.shiCoushoCor
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/gal17-electrostatics && ./Run.pme
	-export TESTsander=$(BINDIR)/sander.MPI; cd sander_music/gal17-electrostatics && ./Run.shiftC

test.parallel.4procs:
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_gb_2rep && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_wat && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_wat_pv && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd hrem_wat_pv && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/TempRem && ./Run.cnstph_remd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/TempRem && ./Run.cnste_remd

test.parallel.8procs:
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_gb_4rep && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd h_rem && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd multid_remd && ./Run.multirem
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/trpcage_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/pHREM && ./Run.pHremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/pHREMrst && ./Run.pHremdrst
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/EREM && ./Run.Eremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/EREMrst && ./Run.Eremdrst
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/Explicit_EREM && ./Run.Eremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phtremd/explicit && ./Run.phtremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phtremd/explicitRst && ./Run.phtremdRst

test.parallel.16procs:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd ephtremd/explicit && ./Run.ephtremd
	-export TESTsander=$(BINDIR)/pmemd.MPI; cd hrem_random_partner && ./Run.hremd

test.pmemd.REM:
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_gb_2rep && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_wat && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_wat_pv && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd hrem_wat_pv && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd rem_gb_4rep && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd h_rem && ./Run.rem
	-export TESTsander='$(BINDIR)/pmemd.MPI' && cd multid_remd && ./Run.multirem
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/trpcage_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rxsgld/gact_4rep && ./Run.rxsgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/pHREM && ./Run.pHremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/pHREMrst && ./Run.pHremdrst
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/TempRem && ./Run.cnstph_remd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph_remd/Explicit_pHREM && ./Run.pHremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/EREM && ./Run.Eremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/EREMrst && ./Run.Eremdrst
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/TempRem && ./Run.cnste_remd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste_remd/Explicit_EREM && ./Run.Eremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phtremd/implicit && ./Run.phtremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phtremd/explicit && ./Run.phtremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phtremd/explicitRst && ./Run.phtremdRst
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd ephtremd/implicit && ./Run.ephtremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd ephtremd/explicit && ./Run.ephtremd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phmd_remd/implicit/ && ./Run.phmdremd
	-export TESTsander=$(BINDIR)/pmemd.MPI; cd hrem_random_partner && ./Run.hremd

test.serial.sander.AMD:
	-cd amd && $(MAKE) -k test
	-cd scaledMD && $(MAKE) -k test

test.parallel.sander.AMD:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd amd && $(MAKE) -k test
	-export TESTsander='$(BINDIR)/sander.MPI'; cd scaledMD && $(MAKE) -k test

test.sander.RISM:
	-cd rism3d/ala && ./Run.ala
	-cd rism3d/ala && ./Run.ala.mdiis0
	-cd rism3d/ala && ./Run.ala.mdiis1
	-cd rism3d/ala && ./Run.ala.dist
	-cd rism3d/ala && ./Run.ala.dist.xyzv
	-cd rism3d/ala && ./Run.ala.hnc
	-cd rism3d/ala && ./Run.ala.list
	-cd rism3d/ala && ./Run.ala.imin5
	-cd rism3d/ala && ./Run.ala.resize.fast
	-cd rism3d/ala && ./Run.ala.tree.fast
	-cd rism3d/ala && ./Run.ala.nacl.fast
	-cd rism3d/ala && ./Run.ala.nacl.tree.fast
	-cd rism3d/ala && ./Run.ala.min.fast
	-cd rism3d/phosphate && ./Run.ph1
	-cd rism3d/phosphate && ./Run.ph1.pse3
	-cd rism3d/phosphate && ./Run.ph1-nacl
	-cd rism3d/phosphate && ./Run.ph1-nacl.pse3
	-cd rism3d/phosphate && ./Run.PH4+_triclinic.pme.center0
	-cd rism3d/phosphate && ./Run.PH4+_triclinic.pme.center1
	-cd rism3d/phosphate && ./Run.PH4+_triclinic.pme.center2
	-cd rism3d/1ahoa && ./Run.1ahoa.pme
	-cd rism3d/4lzt && ./Run.4lzt.pme

test.sander.RISM.dev: #test.sander.RISM
	-cd rism3d/ala && ./Run.ala.pse1
	-cd rism3d/ala && ./Run.ala.resize
	-cd rism3d/ala && ./Run.ala.tree
	-cd rism3d/ala && ./Run.ala.nacl
	-cd rism3d/ala && ./Run.ala.nacl.tree
	-cd rism3d/ala && ./Run.ala.min
	-cd rism3d/phosphate && ./Run.ph1-nacl.pse1
	-cd rism3d/phosphate && ./Run.ph1.pse1
	-cd rism3d/phosphate && ./Run.ph2
	-cd rism3d/phosphate && ./Run.ph10
	-cd rism3d/phosphate && ./Run.ph10-nacl
	-cd rism3d/phosphate && ./Run.ph20
	-cd rism3d/dev/ala && ./Run.ala.dist.hnc
	-cd rism3d/dev/ala && ./Run.ala.dist.pse3
	-cd rism3d/dev/ala && ./Run.ala.min.debug
	-cd rism3d/dev/dt/spc_spc && ./Run.all
	-cd rism3d/dev/dt/ala_spc && ./Run.all
	-cd rism3d/dev/dt/Na_spc && ./Run.all
#	-cd rism3d/dev/dt/Na_spc-NaCl && ./Run.all # missing xvv files
	-cd rism3d/dev/corrections/cyclohexane && ./Run.all
	-cd rism3d/dev/corrections/imidazoleH+ && ./Run.all

test.sander.RISM.MPI:
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.imin5
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.mdiis0
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.mdiis1
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.dist
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.dist.xyzv
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.hnc
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.min.fast
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.resize.fast
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.tree.fast
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.nacl.fast
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.nacl.tree.fast
	-export TESTsander='$(BINDIR)/sander.MPI' \
	        && cd rism3d/1ahoa && ./Run.1ahoa.pme
	-export TESTsander='$(BINDIR)/sander.MPI' \
	        && cd rism3d/4lzt && ./Run.4lzt.pme

test.sander.RISM.MPI.dev: #test.sander.RISM.dev
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.pse1
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.min
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd rism3d/ala && ./Run.ala.resize
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.tree
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.nacl
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/ala && ./Run.ala.nacl.tree
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/dev/ala && ./Run.ala.dist.hnc
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/dev/ala && ./Run.ala.dist.pse3
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/dev/ala && ./Run.ala.min.debug
	-export TESTsander='$(BINDIR)/sander.MPI' \
		&& cd rism3d/dev/dt/ala_spc && ./Run.all

test.sander.RISM.OIN:
	-cd sander_rism3d_asfe_oin && ./Run.ala

test.sander.RISM.OIN.MPI:
	-export TESTsander='$(BINDIR)/sander.MPI' \
	 	&& cd sander_rism3d_asfe_oin && ./Run.ala

test.sander.middle-scheme:
	-cd middle-scheme/MD_Unconstr_Langevin_water && ./Run.LGV_LF
	-cd middle-scheme/MD_Constr_Langevin_water && ./Run.LGV_LF
	-cd middle-scheme/MD_NPT_Constr_Langevin_water && ./Run.LGV_LF_NPT
	-cd middle-scheme/QMMM_Constr_ALA_Methol && ./Run.qmmm
	-cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme
	-cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme_NPT
	-cd middle-scheme/DNA7 && ./Run.DNA_middle_scheme
	-cd middle-scheme/ETH && ./Run.ETH_middle_scheme
	-cd middle-scheme/MeOHZnCl2 && ./Run.meohzncl2_middle_scheme_NPT

test.sander.middle-scheme.MPI:
	-cd middle-scheme/MD_Unconstr_Langevin_water && ./Run.LGV_LF.MPI
	-cd middle-scheme/MD_Constr_Langevin_water && ./Run.LGV_LF.MPI
	-cd middle-scheme/MD_NPT_Constr_Langevin_water && ./Run.LGV_LF_NPT
	-cd middle-scheme/QMMM_Constr_ALA_Methol && ./Run.qmmm.MPI
	-cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme_NPT
	-cd middle-scheme/DNA7 && ./Run.DNA_middle_scheme
	-cd middle-scheme/ETH && ./Run.ETH_middle_scheme
#	-cd middle-scheme/PIMD_Constr_Andersen_water && ./Run.ADS_LF
#	-cd middle-scheme/PIMD_Langevin_water && ./Run.LGV_LF
	-cd middle-scheme/REMD_Constr_ALA && ./Run.rem
#	-cd middle-scheme/PIMD_NPT_Langevin_water && ./Run.NPT_PIMD_middle_scheme

test.sander.crgreloc:
	-(cd crg_reloc/water && ./Run.water.min)
	-(cd crg_reloc/water && ./Run.water.md)

test.sander.crgreloc.MPI:
	-export TESTsander='$(BINDIR)/sander.MPI' && cd crg_reloc/water && ./Run.water.min
	-export TESTsander='$(BINDIR)/sander.MPI' && cd crg_reloc/water && ./Run.water.md

test.sander.APBS:
	export TESTsander='$(BINDIR)/sander.APBS'; cd iapbs_radi/ && ./Run.ion.min

test.serial.pmemd.middle-scheme:
	-export TESTsander='$(BINDIR)/pmemd'; cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd'; cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme_NPT
	-export TESTsander='$(BINDIR)/pmemd'; cd middle-scheme/DNA7 && ./Run.DNA_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd'; cd middle-scheme/ETH && ./Run.ETH_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd'; cd middle-scheme/MeOHZnCl2 && ./Run.meohzncl2_middle_scheme_NPT

test.serial.pmemd.amd:
	-export TESTsander='$(BINDIR)/pmemd'; cd gamd && $(MAKE) -k test OPT=pmemd
	-export TESTsander='$(BINDIR)/pmemd'; cd amd && $(MAKE) -k test OPT=pmemd
	-export TESTsander='$(BINDIR)/pmemd'; cd scaledMD && $(MAKE) -k test OPT=pmemd

test.serial.pmemd.basic:
	-export TESTsander='$(BINDIR)/pmemd'; cd nonper && ./Run.egb6
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.pure_wat
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.pure_wat_nmr_temp_reg
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.vrand
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.frcdmp
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat_oct && ./Run.pure_wat_oct
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.pure_wat_fswitch
	-export TESTsander='$(BINDIR)/pmemd'; cd 4096wat && ./Run.pure_wat_efield
	-export TESTsander='$(BINDIR)/pmemd'; cd alp && ./Run.alp
	-export TESTsander='$(BINDIR)/pmemd'; cd cytosine && ./Run.cytosine
	-export TESTsander='$(BINDIR)/pmemd'; cd dhfr && ./Run.dhfr
	-export TESTsander='$(BINDIR)/pmemd'; cd dhfr && ./Run.dhfr.min
	-export TESTsander='$(BINDIR)/pmemd'; cd dhfr && ./Run.dhfr.noshake
	-export TESTsander='$(BINDIR)/pmemd'; cd dhfr && ./Run.dhfr.bussi
	-export TESTsander='$(BINDIR)/pmemd'; cd dhfr && ./Run.dhfr_reweight
	-export TESTsander='$(BINDIR)/pmemd'; cd ff14ipq && ./Run.ff14ipq
	-export TESTsander='$(BINDIR)/pmemd'; cd variable_14 && ./Run.variable_14_ntb1
	-export TESTsander='$(BINDIR)/pmemd'; cd variable_14 && ./Run.variable_14_igb1
	-export TESTsander='$(BINDIR)/pmemd'; cd trx && ./Run.trx
	-export TESTsander='$(BINDIR)/pmemd'; cd trx && ./Run.trx.cpln.pmemd
	-export TESTsander='$(BINDIR)/pmemd'; cd gb_rna && ./Run.gbrna
	-export TESTsander='$(BINDIR)/pmemd'; cd gb_rna && ./Run.gbrna.min
	-export TESTsander='$(BINDIR)/pmemd'; cd gb_rna && ./Run.gbrna.ln
	-export TESTsander='$(BINDIR)/pmemd'; cd gbsa_tfe && ./Run.gbsa1_tfe
	-export TESTsander='$(BINDIR)/pmemd'; cd gbsa_tfe && ./Run.gbsa3_tfe
	-export TESTsander='$(BINDIR)/pmemd'; cd circ_dna && ./Run.circdna
	-export TESTsander='$(BINDIR)/pmemd'; cd gb2_trx && ./Run.trxox.nogbsa && ./Run.trxox.nogbsa prmtop_an
	-export TESTsander='$(BINDIR)/pmemd'; cd gb7_trx && ./Run.trxox_md
	-export TESTsander='$(BINDIR)/pmemd'; cd gb8_trx && ./Run.trxox
	-export TESTsander='$(BINDIR)/pmemd'; cd gb8_trx && ./Run.trxox_md && ./Run.trxox_md prmtop_an
	-export TESTsander='$(BINDIR)/pmemd'; cd mcwat && ./Run.mcwat
	-export TESTsander='$(BINDIR)/pmemd'; cd RAMD && ./Run.ramd
	-export TESTsander='$(BINDIR)/pmemd'; cd ff19SB && ./Run.pmemd
# gbneck2nu test. TODO: make better alignment for those lines
	-export TESTsander='$(BINDIR)/pmemd'; cd gbneck2nu/1hji && ./Run.1hji_md
	-export TESTsander='$(BINDIR)/pmemd'; cd gbneck2nu/modified_nu/3p4a/ && ./Run.3p4a
# end gbneck2nu test
	-export TESTsander='$(BINDIR)/pmemd'; cd alpb_trx && ./Run.trxox.nogbsa
#	-export TESTsander='$(BINDIR)/pmemd'; cd gb1_cox2 && ./Run.cox2
	-export TESTsander='$(BINDIR)/pmemd'; cd gbsa_xfin && ./Run.gbsa1
	-export TESTsander='$(BINDIR)/pmemd'; cd gbsa_xfin && ./Run.gbsa3
	-export TESTsander='$(BINDIR)/pmemd'; cd tip4p && ./Run.tip4p
	-export TESTsander='$(BINDIR)/pmemd'; cd tip4p && ./Run.tip4p_mcbar
	-export TESTsander='$(BINDIR)/pmemd'; cd tip4p && ./Run.tip4p_nve
	-export TESTsander='$(BINDIR)/pmemd'; cd tip5p && ./Run.tip5p
	-export TESTsander='$(BINDIR)/pmemd'; cd tip5p && ./Run.tip5p_nve
# constant pH test
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstph/implicit && ./Run.cnstph
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstph/explicit && ./Run.cnstph
	-export TESTsander='$(BINDIR)/pmemd'; cd phmd/implicit && ./Run.phmd
# constant E test
	-export TESTsander='$(BINDIR)/pmemd'; cd cnste/implicit && ./Run.cnste
	-export TESTsander='$(BINDIR)/pmemd'; cd cnste/explicit && ./Run.cnste
# constant pH,E test
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstphe/implicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstphe/explicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstphe_merged/implicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd'; cd cnstphe_merged/explicit && ./Run.cnstphe
#CHARMM TESTS
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.min
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.md
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr_cmap && ./Run.dhfr_charmm.md
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.min
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.md
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.min
	-export TESTsander='$(BINDIR)/pmemd'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.md
#IPS TESTS
	-export TESTsander='$(BINDIR)/pmemd'; cd gact_ips && ./Run.ips
# Constant surface tension (csurften > 0)
	-export TESTsander='$(BINDIR)/pmemd'; cd csurften && ./Run.csurften_z-dir
# Lennard-Jones 12-6-4 potential
	-export TESTsander='$(BINDIR)/pmemd'; cd lj_12-6-4 && ./Run.12-6-4
# Semi-isotropic pressure coupling (csurften > 0 AND ntp = 3)
	-export TESTsander='$(BINDIR)/pmemd'; cd csurften && ./Run.csurften_z-dir_npt_3
#    NMR Opt Test Cases
	-export TESTsander='$(BINDIR)/pmemd'; cd nmropt && $(MAKE) pmemd_compat
	-export TESTsander='$(BINDIR)/pmemd'; cd rdc && ./Run.nmr
# NetCDF Traj/Restart tests
	-export TESTsander='$(BINDIR)/pmemd'; cd netcdf && $(MAKE) -k test OPT=$(NETCDF)
#    Directional pressure scaling (baroscalingdir > 0)
	-export TESTsander='$(BINDIR)/pmemd'; cd baroscalingdir && ./Run.baroscalingdir_z-dir
#    Xray
	@(if [ -n "$(MKL)" ]; then \
          $(MAKE) test.serial.pmemd.xray ;\
	fi ;\
	)
# Velocity write
	-export TESTsander='$(BINDIR)/pmemd'; cd velocity_write && ./Run.vel1
	-export TESTsander='$(BINDIR)/pmemd'; cd velocity_write && ./Run.vel2
# Custom virtual sites
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/tip4p && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/tip4p && ./Run.npt
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/tip5p && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/tip5p && ./Run.npt
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/Methanol && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/Methanol && ./Run.npt
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/BromoBenzene && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/BromoBenzene && ./Run.npt
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/DimethylEther && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/DimethylEther && ./Run.npt
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/BenzenePi && ./Run.ec
	-export TESTsander='$(BINDIR)/pmemd'; cd virtual_sites/BenzenePi && ./Run.npt

test.serial.pmemd.xray:
	-export TESTsander='$(BINDIR)/pmemd'; cd xray/2wcu && ./Run.2wcu
	-export TESTsander='$(BINDIR)/pmemd'; cd xray/480d && ./Run.480d

test.serial.pmemd.TI:
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/gasphase && ./Run.gasphase
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/campTI && ./Run.campTI
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/pheMTI && ./Run.0
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/pheMTI && ./Run.1
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/pheMTI && ./Run.lambda0
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/pheMTI && ./Run.lambda1
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/sodium && ./Run.sodium
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/ti_ggcc && ./Run.test1
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/ti_ggcc && ./Run.test2
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/softcore && ./Run_sc
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/softcore/tishake2vsite && ./Run.tishake2vsite
	-export TESTsander='$(BINDIR)/pmemd'; cd pmemdTI/softcore/tishake2vsite && ./Run.tishake2vsite_vacuum

#2 million atom tests are not run by default because they need >3GB Memory
test.serial.big:
	-cd 2_million_atom && ./Run.2mil.min
	-cd 2_million_atom && ./Run.2mil.md
	-cd 2_million_atom && ./Run.2mil.rst.md

test.parallel.big:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd 2_million_atom && ./Run.2mil.min
	-export TESTsander='$(BINDIR)/sander.MPI'; cd 2_million_atom && ./Run.2mil.md
	-export TESTsander='$(BINDIR)/sander.MPI'; cd 2_million_atom && ./Run.2mil.rst.md

test.serial.pmemd.big:
	-export TESTsander='$(BINDIR)/pmemd'; cd 2_million_atom && ./Run.2mil.min
	-export TESTsander='$(BINDIR)/pmemd'; cd 2_million_atom && ./Run.2mil.md
	-export TESTsander='$(BINDIR)/pmemd'; cd 2_million_atom && ./Run.2mil.rst.md

test.serial.sander.sgld:
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgld
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgldfp
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgldg
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgmdg
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgldbd2
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgldbd3
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgldbd4
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgmdbd2
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgmdbd3
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gact && ./Run.sgmdbd4
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgld
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgldfp
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgldg
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgmdg
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgldbd3
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgldbd4
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd3
	-export TESTsander='$(BINDIR)/sander'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd4

test.parallel.sander.sgld:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgld
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgldfp
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgldg
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgmdg
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgldbd2
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgldbd3
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgldbd4
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgmdbd2
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgmdbd3
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gact && ./Run.sgmdbd4
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgld
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldfp
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldg
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdg
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldbd3
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldbd4
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd3
	-export TESTsander='$(BINDIR)/sander.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd4

test.serial.pmemd.sgld:
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgld
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgldfp
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgldg
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgmdg
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgldbd2
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgldbd3
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgldbd4
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgmdbd2
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgmdbd3
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gact && ./Run.sgmdbd4
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgld
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgldfp
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgldg
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgmdg
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgldbd3
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgldbd4
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd3
	-export TESTsander='$(BINDIR)/pmemd'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd4

test.parallel.pmemd.sgld:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgldfp
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgldg
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgmdg
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgldbd2
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgldbd3
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgldbd4
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgmdbd2
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgmdbd3
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gact && ./Run.sgmdbd4
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgld
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldfp
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldg
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdg
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldbd3
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgldbd4
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd3
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd sgld/gb_rna && ./Run.gbrna.sgmdbd4

test.parallel.pmemd.big:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 2_million_atom && ./Run.2mil.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 2_million_atom && ./Run.2mil.md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 2_million_atom && ./Run.2mil.rst.md

test.parallel.pmemd.middle-scheme:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme_midpoint
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/4096wat && ./Run.pure_wat_middle_scheme_NPT
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/DNA7 && ./Run.DNA_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/ETH && ./Run.ETH_middle_scheme
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/MeOHZnCl2 && ./Run.meohzncl2_middle_scheme_NPT
	#-export TESTsander='$(BINDIR)/pmemd.MPI'; cd middle-scheme/ETH && ./Run.ETH_middle_scheme_midpoint
	

test.parallel.pmemd.amd:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gamd && $(MAKE) -k test OPT=pmemd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd amd && $(MAKE) -k test OPT=pmemd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd scaledMD && $(MAKE) -k test OPT=pmemd

test.parallel.pmemd.mbar:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd mbar_MPI && ./Run.sh

test.parallel.pmemd.basic:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd nonper && ./Run.egb6
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.pure_wat
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.pure_wat_fswitch
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.pure_wat_efield
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.pure_wat_nmr_temp_reg
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.vrand
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.frcdmp
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat_oct && ./Run.pure_wat_oct
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd alp && ./Run.alp
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cytosine && ./Run.cytosine
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd dhfr && ./Run.dhfr
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd dhfr && ./Run.dhfr.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd dhfr && ./Run.dhfr.noshake
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd ff14ipq && ./Run.ff14ipq
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd variable_14 && ./Run.variable_14_ntb1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd trx && ./Run.trx
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd trx && ./Run.trx.cpln.pmemd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb_rna && ./Run.gbrna
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb_rna && ./Run.gbrna.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb_rna && ./Run.gbrna.ln
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gbsa_tfe && ./Run.gbsa1_tfe
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gbsa_tfe && ./Run.gbsa3_tfe	
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd circ_dna && ./Run.circdna
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb2_trx && ./Run.trxox.nogbsa
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb7_trx && ./Run.trxox_md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb8_trx && ./Run.trxox
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb8_trx && ./Run.trxox_md && ./Run.trxox_md prmtop_an
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gbneck2nu/1hji && ./Run.1hji_md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd alpb_trx && ./Run.trxox.nogbsa
#	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gb1_cox2 && ./Run.cox2
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gbsa_xfin && ./Run.gbsa1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gbsa_xfin && ./Run.gbsa3
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd tip4p && ./Run.tip4p
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd tip4p && ./Run.tip4p_mcbar
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd tip4p && ./Run.tip4p_nve
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd tip5p && ./Run.tip5p
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd tip5p && ./Run.tip5p_nve
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd ff19SB && ./Run.pmemd
# constant pH test
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph/implicit && ./Run.cnstph
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstph/explicit && ./Run.cnstph
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd phmd/implicit && ./Run.phmd
# constant E test
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste/implicit && ./Run.cnste
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnste/explicit && ./Run.cnste
# constant pH,E test
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstphe/implicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstphe/explicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstphe_merged/implicit && ./Run.cnstphe
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd cnstphe_merged/explicit && ./Run.cnstphe
#CHARMM TESTS
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr && ./Run.dhfr_charmm.md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr_cmap && ./Run.dhfr_charmm.md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm_noshake.md
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.min
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd chamber/md_engine/dhfr_cmap_pbc && ./Run.dhfr_cmap_pbc_charmm.md
#IPS TESTS
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd gact_ips && ./Run.ips
# Constant surface tension (csurften > 0)
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd csurften && ./Run.csurften_z-dir
# Lennard-Jones 12-6-4 potential
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd lj_12-6-4 && ./Run.12-6-4
# Semi-isotropic pressure coupling (csurften > 0 AND ntp = 3)
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd csurften && ./Run.csurften_z-dir_npt_3
#    NMR Opt Test Cases
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd nmropt && $(MAKE) pmemd_compat
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd rdc && ./Run.nmr
# NetCDF Traj/Restart tests
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd netcdf && $(MAKE) -k test OPT=$(NETCDF)
# MIDPOINT TEST CASES
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd 4096wat && ./Run.pure_wat_midpoint
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd dhfr && ./Run.dhfr_midpoint
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd dhfr && ./Run.dhfr.noshake_midpoint
# Velocity write
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd velocity_write && ./Run.vel1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd velocity_write && ./Run.vel2

#EMIL TI TESTS
test.parallel.emil:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd emil/emil_sander_gbsa && ./Run.emil $(EMIL)

test.parallel.emil.pmemd:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd emil/emil_pmemd_gbsa && ./Run.emil $(EMIL)
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd emil/emil_pmemd_tip3p && ./Run.emil $(EMIL)

test.serial.emil:
	-export TESTsander='$(BINDIR)/sander'; unset DO_PARALLEL; cd emil/emil_sander_gbsa && ./Run.emil $(EMIL)

test.serial.emil.pmemd:
	-export TESTsander='$(BINDIR)/pmemd';  unset DO_PARALLEL; cd emil/emil_pmemd_gbsa && ./Run.emil $(EMIL)
	-export TESTsander='$(BINDIR)/pmemd';  unset DO_PARALLEL; cd emil/emil_pmemd_tip3p && ./Run.emil $(EMIL)

#KMMD TESTS
test.serial.pmemd.kmmd:
	-export TESTsander='$(BINDIR)/pmemd'; unset DO_PARALLEL; cd kmmd/kmmd_pmemd    && ./Run.kmmd
	-export TESTsander='$(BINDIR)/pmemd'; unset DO_PARALLEL; cd kmmd/kmmd_pmemd_gb && ./Run.kmmd

test.serial.sander.kmmd:
	-export TESTsander='$(BINDIR)/sander'; unset DO_PARALLEL; cd ../AmberTools/test/kmmd/kmmd_sander    && ./Run.kmmd
	-export TESTsander='$(BINDIR)/sander'; unset DO_PARALLEL; cd ../AmberTools/test/kmmd/kmmd_sander_gb && ./Run.kmmd

test.parallel.pmemd.kmmd:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd kmmd/kmmd_pmemd    && ./Run.kmmd
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd kmmd/kmmd_pmemd_gb && ./Run.kmmd

test.parallel.sander.kmmd:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd ../AmberTools/test/kmmd/kmmd_sander    && ./Run.kmmd
	-export TESTsander='$(BINDIR)/sander.MPI'; cd ../AmberTools/test/kmmd/kmmd_sander_gb && ./Run.kmmd


#TI TESTS
test.parallel.pmemd.TI:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/campTI && ./Run.campTI
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/pheMTI && ./Run.0
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/pheMTI && ./Run.1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/pheMTI && ./Run.lambda0
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/pheMTI && ./Run.lambda1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/sodium && ./Run.sodium
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/ti_ggcc && ./Run.test1
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/ti_ggcc && ./Run.test2
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd pmemdTI/softcore && ./Run_sc

# API tests
test.serial.sanderapi:
	-cd sanderapi && $(MAKE) test
	-cd sanderlesapi && $(MAKE) test

#emap TESTS
test.serial.sander.emap:
	-export TESTsander='$(BINDIR)/sander'; cd emap/ && ./Run.emap
	-export TESTsander='$(BINDIR)/sander'; cd emap/ && ./Run.emap_boundary
	-export TESTsander='$(BINDIR)/sander'; cd emap2/ && ./Run.emap2

test.parallel.sander.emap:
	-export TESTsander='$(BINDIR)/sander.MPI'; cd emap/ && ./Run.emap
	-export TESTsander='$(BINDIR)/sander.MPI'; cd emap/ && ./Run.emap_boundary

test.serial.pmemd.emap:
	-export TESTsander='$(BINDIR)/pmemd'; cd emap/ && ./Run.emap
	-export TESTsander='$(BINDIR)/pmemd'; cd emap/ && ./Run.emap_boundary

test.parallel.pmemd.emap:
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd emap/ && ./Run.emap
	-export TESTsander='$(BINDIR)/pmemd.MPI'; cd emap/ && ./Run.emap_boundary

test.pmemd.midpoint:
	cd midpoint && $(MAKE) -k test.pmemd.midpoint

test.pmemd.cuda:
	cd cuda && $(MAKE) -k test.pmemd.cuda PREC_MODEL=$(PREC_MODEL)

test.pmemd.cuda.MPI:
	cd cuda && $(MAKE) -k test.pmemd.cuda.MPI PREC_MODEL=$(PREC_MODEL)

test.pmemd.hip:
	cd hip && $(MAKE) -k test.pmemd.hip PREC_MODEL=$(PREC_MODEL)

test.pmemd.hip.MPI:
	cd hip && $(MAKE) -k test.pmemd.hip.MPI PREC_MODEL=$(PREC_MODEL)

test.pmemd.cuda.sgld:
	cd cuda && $(MAKE) -k test.pmemd.cuda.sgld PREC_MODEL=$(PREC_MODEL)

test.pmemd.cuda.MPI.sgld:
	cd cuda && $(MAKE) -k test.pmemd.cuda.sgld PREC_MODEL=$(PREC_MODEL)

test.pmemd.cuda.MPI.rxsgld:
	cd cuda && $(MAKE) -k test.pmemd.cuda.rxsgld PREC_MODEL=$(PREC_MODEL)

test.serial.sander.nfe:
	-cd nfe && ./run-serial.sh

test.parallel.sander.nfe:
	-cd nfe && ./run-parallel.sh

test.serial.pmemd.nfe:
	-cd nfe && ./run-pmemd-serial.sh

test.parallel.pmemd.nfe:
	-cd nfe && ./run-pmemd-parallel.sh

test.nmode:
	-cd nmode && ./Run.ala-dipeptide
	-cd nmode && ./Run.ala-dipeptide_rgroup
	-cd newton_raph && ./Run.newton_raph

test.serial.fetoolkit: test.serial.ndfes test.serial.edgembar

test.serial.fetoolkit.nopython: test.serial.ndfes

test.serial.ndfes:
	-cd ndfes && ./Run.mbar
	-cd ndfes && ./Run.wtp

test.serial.edgembar:
	-cd edgembar && ./Run.edgembar $(PYTHON)

test.pbsa:
	-cd sander_pbsa_dmp    && ./Run.dmp.min
	-cd sander_pbsa_ipb2   && ./Run.110D.min
	-cd sander_pbsa_delphi && ./Run.1az6.min
	-cd sander_pbsa_lpb    && ./Run.lsolver.min
	-cd sander_pbsa_radi   && ./Run.ion.min
	-cd sander_pbsa_tsr    && ./Run.tsrb.min
	-cd sander_pbsa_frc    && ./test
	-cd sander_pbsa_decres && ./Run.pbsa_decres
	-cd sander_pbsa_decpw  && ./Run.pbsa_decpw
	-cd sander_pbsa_ligand && ./Run
	-cd sander_pbsa_imin5  && ./Run.min

test.netcdf:
	-(cd ../AmberTools/src/netcdf-4.3.0 && $(MAKE) check)
	-cd trajene_netcdf && ./Run.trajene $(NETCDF)
	-cd netcdf && $(MAKE) -k test OPT=$(NETCDF)

test.neb:
	-cd neb-testcases/neb_gb_partial && ./Run.neb_gb_partial
	-cd neb-testcases/neb_gb_full && ./Run.neb_gb_full
	-cd neb-testcases/neb_explicit && ./Run.neb_explicit

test.pmemd.neb:
	-cd neb-testcases/neb_gb_partial && ./Run.neb_gb_partial_pmemd
	-cd neb-testcases/neb_gb_full    && ./Run.neb_gb_full_pmemd
	-cd neb-testcases/neb_explicit   && ./Run.neb_explicit_pmemd

test.gem.pmemd.yes:
# 	-cd 2048_wat_gem && ./Run.2048_wat_nvt_gem.pmemd.gemstar
# 	-cd 2048_wat_gem && ./Run.2048_wat_MCbar_gem.pmemd.gemstar
# 	-cd 2048_wat_gem && ./Run.2048_wat_nvt_gem.pmemd.gem
# 	-cd 2048_wat_gem && ./Run.2048_wat_MCbar_gem.pmemd.gem
	-cd amoeba_formbox && ./Run.amoeba_formbox.pmemd.gem
	-cd amoeba_IL && ./Run.amoeba_IL.pmemd.gem
	-cd amoeba_jac3 && ./Run.jac_amba_beeman_MCbar.pmemd.gem
	-cd amoeba_jac3 && ./Run.jac_amba_beeman_nvt.pmemd.gem
	-cd amoeba_jac3 && ./Run.jac_amba_beeman_virial.pmemd.gem
	-cd amoeba_jac3 && ./Run.jac_amba_verlet_nvt.pmemd.gem
	-cd amoeba_gb1 && ./Run.amoeba_gb1.pmemd.gem
	-cd amoeba_wat1 && ./Run.amoeba_wat1.pmemd.gem
	-cd amoeba_wat2 && ./Run.amoeba_wat2.ntpverlet.pmemd.gem
	-cd amoeba_wat2 && ./Run.amoeba_wat2.pmemd.gem

test.gem.pmemd.no:
	@echo "Skipping gem.pmemd tests"

test.gem.pmemd.MPI.yes:

# 	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd 2048_wat_gem && ./Run.2048_wat_nvt_gem.pmemd.gemstar
# 	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd 2048_wat_gem && ./Run.2048_wat_MCbar_gem.pmemd.gemstar
# 	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd 2048_wat_gem && ./Run.2048_wat_nvt_gem.pmemd.gem
# 	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd 2048_wat_gem && ./Run.2048_wat_MCbar_gem.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_formbox && ./Run.amoeba_formbox.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_IL && ./Run.amoeba_IL.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_jac3 && ./Run.jac_amba_beeman_MCbar.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_jac3 && ./Run.jac_amba_beeman_nvt.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_jac3 && ./Run.jac_amba_beeman_virial.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_jac3 && ./Run.jac_amba_verlet_nvt.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_gb1 && ./Run.amoeba_gb1.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_wat1 && ./Run.amoeba_wat1.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_wat2 && ./Run.amoeba_wat2.ntpverlet.pmemd.gem
	-export TESTsander='${AMBERHOME}/bin/gem.pmemd.MPI'; cd amoeba_wat2 && ./Run.amoeba_wat2.pmemd.gem

test.gem.pmemd.MPI.no:
	@echo "Skipping gem.pmemd.MPI tests"

#===========================================================================

finished.serial:
	@echo ""
	@echo "Finished serial test suite for Amber ${AMBER_VERSION} at `date`."
	@echo ""

finished.parallel:
	@echo ""
	@echo "Finished parallel test suite for Amber ${AMBER_VERSION} at `date`."
	@echo "Tests ran with DO_PARALLEL=\"${DO_PARALLEL}\"."
	@echo "Some tests require 4 or 8 threads to run, while some will not"
	@echo "run with more than 2.  Please run further parallel tests with the"
	@echo "appropriate number of processors. See $(AMBERHOME)/test/README."
	@echo ""

finished.cuda.serial:
	@echo ""
	@echo "Finished serial CUDA test suite for Amber ${AMBER_VERSION} at `date`."
	@echo ""

finished.cuda.parallel:
	@echo ""
	@echo "Finished parallel CUDA test suite for Amber ${AMBER_VERSION} at `date`."
	@echo "Tests ran with DO_PARALLEL=\"${DO_PARALLEL}\"."
	@echo ""

finished.hip.serial:
	@echo ""
	@echo "Finished HIP test suite for Amber ${AMBER_VERSION} at `date`."
	@echo ""

clean:
	-./test_amber_clean.sh

check:
	(find . -name "*.dif" ! -size 0c -print | \
	while read dif ;\
	do \
	    echo $$dif ;\
	    cat $$dif ;\
	    echo ;\
	done ;\
	)

#===========================================================================
