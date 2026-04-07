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
        print(f'### PERLBIN: {perlbin}')
        print(f'### LIBDIR: {libdir}')
        
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