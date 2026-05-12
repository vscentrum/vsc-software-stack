import os, re

from easybuild.framework.easyconfig import CUSTOM, MANDATORY
from easybuild.framework.extensioneasyblock import ExtensionEasyBlock
from easybuild.easyblocks.generic.perlmodule import PerlModule
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.modules import get_software_root
from easybuild.tools.run import run_shell_cmd


class EB_PsN(PerlModule):
    @staticmethod
    def extra_options():
        """Easyconfig parameters specific to PsN modules."""
        extra_vars = {
            'perllib': [None, "PsN requires 'perllib' parameter", MANDATORY],
            'nm_versions': [None, "Lines to add to [nm_versions] in psn.conf", CUSTOM],
        }
        return ExtensionEasyBlock.extra_options(extra_vars)

    def install_perl_module(self):
        # rlibdir = self.installdir
        # cmd = 'R_LIBS_SITE=%s:${R_LIBS_SITE} perl setup.pl' % rlibdir
        cmd = 'perl setup.pl'

        bindir = os.path.join(self.installdir, 'bin')
        libdir = os.path.join(self.installdir, self.cfg['perllib'])

        perlroot = get_software_root('Perl')
        if perlroot is None:
            raise EasyBuildError("Perl is a required dependency of PsN")
        perlbin = os.path.join(perlroot, 'bin', 'perl')
        perllib = os.path.join(perlroot, self.cfg['perllib'])

        # qanda = {
        #     'PsN Utilities installation directory [/usr/local/bin]:': bindir,
        #     'Path to perl binary used to run Utilities [%s]:' % perlbin: '',
        #     'PsN Core and Toolkit installation directory [%s]:' % perllib: libdir,
        #     'Would you like this script to check Perl modules [y/n]?': 'y',
        #     'Continue installing PsN (installing is possible even if modules are missing)[y/n]?': 'y',
        #     'Would you like to install the PsNR R package? [y/n]': 'y',
        #     'Would you like to install the pharmpy python package? [y/n]': 'n',
        #     'Would you like to install the PsN test library? [y/n]': 'y',
        #     'PsN test library installation directory [%s]:' % libdir: '',
        #     'Would you like help to create a configuration file? [y/n]': 'n',
        #     'Press ENTER to exit the installation program.': '',
        # }
        
        print(f'### BINDIR: {bindir}')
        # /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/bin
        print(f'### PERLBIN: {perlbin}')
        # /apps/gent/RHEL9/cascadelake-ib/software/Perl/5.38.2-GCCcore-13.3.0/bin/perl
        print(f'### LIBDIR: {libdir}')
        # /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2
        
        # Questions:
        # $ perl setup.pl
                # This is the PsN installer. I will install PsN version 5.5.0.
                # You need to answer a few questions. If a default value is presented
                # you may accept it by pressing ENTER.

                # Hi vsc47063, you don't look like root. Please note that you need root privileges to install PsN systemwide.
                # PsN Utilities installation directory [/usr/local/bin]: -> bindir
                
                # Path to perl binary used to run Utilities [/apps/gent/RHEL9/cascadelake-ib/software/Perl/5.38.2-GCCcore-13.3.0/bin/perl]: -> perlbin
                
                # PsN Core and Toolkit installation directory [/apps/gent/RHEL9/cascadelake-ib/software/Perl/5.38.2-GCCcore-13.3.0/lib/perl5/site_perl/5.38.2]: -> libdir
                
                # The next step is to check Perl module dependencies.
                # If a module is missing, you must install it, e.g. from CPAN,
                # http://www.cpan.org/modules/index.html
                # before PsN can be run.

                # Would you like this script to check Perl modules [y/n]? -> y
                
                # Testing required modules:
                # Module Statistics::Distributions ok
                # Module File::Copy::Recursive ok
                # Module File::HomeDir ok
                # Module Math::SigFigs ok
                # Module Capture::Tiny ok
                # Module Math::Random::Free ok
                # Module Math::MatrixReal ok
                # Module Mouse ok
                # Module MouseX::Params::Validate ok
                # Module YAML ok

                # Done testing required modules.

                # Testing recommended but not required modules...
                # Module Archive::Zip ok
                # Tests done.

                # Continue installing PsN (installing is possible even if modules are missing)[y/n]? -> y

                # Directory /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2/PsN_5_5_0 already exists.
                # PsN 5.5.0 is already (partially) installed. Would you like to continue anyway [y/n] ? -> y
                
                # This version (5.5.0) looks like the same or an older installed
                # version (5.5.0) of PsN. Would you like to make
                # this version (5.5.0) the default? [y/n] -> y

                # The R package PsNR and its dependencies are needed for the rplots functionality and the qa tool in PsN.
                # The PsN installer can automatically install these using renv to make sure that all versions
                # of R packages have been tested together. A separate R library will be created inside the PsN
                # installation directory. You need to have R installed for this installation.


                # Would you like to install the PsNR R package? [y/n] -> y
                # -> now it starts downloading and installing exact deps version - already installed are not used -> log-install-psn1
                
                # The Python package 'pharmpy' is needed by PsN and you would need to have python installed on your system
                # If you let the installer install pharmpy it will be installed in a virtual environment together with its dependencies inside the PsN installation
                # You would need to have python installed for this installation

                # Would you like to install the pharmpy python package? [y/n] -> y -> log-install-psn2
                
                # Would you like to install the PsN test library? [y/n] -> y
                # PsN test library installation directory [/scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2]: -> Enter                                
                # PsN test library installed successfully in [/scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2/PsN_test_5_5_0].
                # Please read the 'testing' chapter of the developers_guide.pdf for information on how to run the tests


                # Now you must edit /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2/PsN_5_5_0/psn.conf
                # so that PsN can find your NONMEM installations.
                # You can get help to create a bare-bones configuration file that will work
                # when running PsN locally. If you are running PsN on a cluster and/or want
                # to set personalized defaults and/or will run PsN with NMQual,
                # you can manually add the relevant options to the file afterwards.
                # Would you like help to create a configuration file? [y/n] -> n
                # Please note that if you have a psn.conf file in your home directory,
                # the settings in that file will override the settings in
                # /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2/PsN_5_5_0/psn.conf

                # Installation partially complete. You still have to add NONMEM settings to psn.conf before you can run PsN.
                # A psn.conf to edit is found in
                # /scratch/gent/vo/001/gvo00117/easybuild/RHEL9/cascadelake-ampere-ib/software/PsN/5.5.0-foss-2024a/lib/perl5/site_perl/5.38.2/PsN_5_5_0
                # Detailed instructions are found in psn_configuration.pdf

                # Press ENTER to exit the installation program.

        qanda = {
            re.escape('PsN Utilities installation directory [/usr/local/bin]:'): bindir,
            re.escape('Path to perl binary used to run Utilities [%s]:' % perlbin): '',
            re.escape('PsN Core and Toolkit installation directory [%s]:' % perllib): libdir,
            re.escape('Would you like this script to check Perl modules [y/n]?'): 'y',
            re.escape('Continue installing PsN (installing is possible even if modules are missing)[y/n]?'): 'y',
            re.escape('Would you like to install the PsNR R package? [y/n]'): 'y',
            re.escape('Would you like to install the pharmpy python package? [y/n]'): 'n',
            re.escape('Would you like to install the PsN test library? [y/n]'): 'y',
            re.escape('PsN test library installation directory [%s]:' % libdir): '',
            re.escape('Would you like help to create a configuration file? [y/n]'): 'n',
            re.escape('Press ENTER to exit the installation program.'): '',
        }

        # maxhits = 4000  # to give enough time to pharmpy installation

        # qa_patterns = list(qanda.items())

        run_shell_cmd(
            cmd,
            qa_patterns=list(qanda.items()),
            qa_timeout=300,
        )
        # run_cmd_qa(cmd, qanda, maxhits=maxhits, log_all=True, simple=True)
        # run_shell_cmd(cmd, qanda, maxhits=maxhits, log_all=True, simple=True)

        # Add selected NONMEM versions to [nm_versions] section in PsN config file
        if self.cfg['nm_versions'] is not None:
            lines = r'\n'.join(self.cfg['nm_versions'])
            PsN_X_Y_Z = '_'.join([self.name] + self.version.split('.'))
            psnconf = os.path.join(libdir, PsN_X_Y_Z, 'psn.conf')
            cmd = "sed -i '/\[nm_versions\]/a %s' %s" % (lines, psnconf)
            run_shell_cmd(cmd)