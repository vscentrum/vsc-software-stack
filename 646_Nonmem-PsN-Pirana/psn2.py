import os
import re
import shutil

from easybuild.framework.easyconfig import CUSTOM
from easybuild.framework.extensioneasyblock import ExtensionEasyBlock
from easybuild.tools.build_log import EasyBuildError


class EB_PsN(ExtensionEasyBlock):
    """Easyblock for installing PsN without running upstream setup.pl."""

    @staticmethod
    def extra_options(extra_vars=None):
        extra_vars = ExtensionEasyBlock.extra_options(extra_vars)
        extra_vars.update({
            'perllib': [None, 'Perl library subdirectory to install PsN into', CUSTOM],
            'nm_versions': [None, 'List of PsN nm_versions entries, e.g. default=nmfe76,7.6', CUSTOM],
        })
        return extra_vars

    def configure_step(self):
        pass

    def build_step(self):
        pass

    def install_step(self):
        perllib = self.cfg['perllib']
        nm_versions = self.cfg['nm_versions'] or []

        if not perllib:
            raise EasyBuildError("Missing required easyconfig parameter 'perllib'")
        if not nm_versions:
            raise EasyBuildError("Missing required easyconfig parameter 'nm_versions'")

        srcdir = os.getcwd()
        bindir = os.path.join(self.installdir, 'bin')
        libbase = os.path.join(self.installdir, perllib)
        psn_ver = self.version.replace('.', '_')
        psndir = os.path.join(libbase, 'PsN_%s' % psn_ver)

        perl = shutil.which('perl')
        if not perl:
            raise EasyBuildError("Could not find perl in PATH")

        os.makedirs(bindir, exist_ok=True)
        os.makedirs(libbase, exist_ok=True)

        lib_src = os.path.join(srcdir, 'lib')
        if not os.path.isdir(lib_src):
            raise EasyBuildError("Could not find PsN lib directory: %s", lib_src)

        if os.path.exists(psndir):
            shutil.rmtree(psndir)
        shutil.copytree(lib_src, psndir)

        utilities = [
            'bootstrap', 'cdd', 'execute', 'llp', 'scm', 'sumo', 'sse',
            'update_inits', 'update', 'npc', 'vpc', 'pind', 'nonpb',
            'extended_grid', 'psn', 'psn_options', 'psn_clean', 'runrecord',
            'mcmp', 'lasso', 'mimp', 'xv_scm', 'parallel_retries', 'boot_scm',
            'gls', 'simeval', 'frem', 'randtest', 'linearize', 'crossval',
            'pvar', 'nca', 'proseval', 'sir', 'rawresults', 'precond',
            'covmat', 'nmoutput2so', 'benchmark', 'npfit', 'resmod',
            'cddsimeval', 'qa', 'transform', 'boot_randtest', 'monitor',
            'scmplus', 'scmreport', 'm1find', 'pack',
        ]

        for util in utilities:
            self._install_utility(util, perl, psndir, bindir)

        self._create_psn_conf(psndir, perl, nm_versions)

    def _install_utility(self, util, perl, psndir, bindir):
        src = os.path.join(os.getcwd(), 'bin', util)
        if not os.path.isfile(src):
            raise EasyBuildError("Could not find PsN utility script: %s", src)

        versioned = os.path.join(bindir, '%s-%s' % (util, self.version))
        unversioned = os.path.join(bindir, util)

        with open(src, 'r') as fh:
            content = fh.read()

        marker = '# Everything above this line will be replaced #'
        if marker not in content:
            raise EasyBuildError("Marker line not found in %s", src)

        body = content.split(marker, 1)[1]
        header = '\n'.join([
            '#!%s' % perl,
            "use lib '%s';" % psndir,
            '',
            '# Everything above this line was entered by the EasyBuild PsN easyblock #',
        ])

        with open(versioned, 'w') as fh:
            fh.write(header + body)

        os.chmod(versioned, 0o755)

        if os.path.lexists(unversioned):
            os.remove(unversioned)
        os.symlink(versioned, unversioned)

    def _create_psn_conf(self, psndir, perl, nm_versions):
        template = os.path.join(psndir, 'psn.conf_template')
        conf = os.path.join(psndir, 'psn.conf')

        if not os.path.isfile(template):
            raise EasyBuildError("Could not find PsN config template: %s", template)

        with open(template, 'r') as fh:
            txt = fh.read()

        txt = self._set_global_key(txt, 'perl', perl)

        rbin = shutil.which('R')
        if rbin:
            txt = self._set_global_key(txt, 'R', rbin)

        nm_lines = []
        for entry in nm_versions:
            if '=' not in entry:
                raise EasyBuildError("Invalid nm_versions entry '%s'; expected name=cmd,version", entry)
            nm_lines.append(entry)

        txt = self._replace_section(txt, 'nm_versions', nm_lines)

        with open(conf, 'w') as fh:
            fh.write(txt)

    def _set_global_key(self, txt, key, value):
        pattern = r'(?m)^%s\s*=.*$' % re.escape(key)
        repl = '%s=%s' % (key, value)
        if re.search(pattern, txt):
            return re.sub(pattern, repl, txt, count=1)
        return repl + '\n' + txt

    def _replace_section(self, txt, section, lines):
        replacement = '[%s]\n%s\n\n' % (section, '\n'.join(lines))
        pattern = r'(?ms)^\[%s\]\s*\n.*?(?=^\[|\Z)' % re.escape(section)
        if re.search(pattern, txt):
            return re.sub(pattern, replacement, txt, count=1)
        if not txt.endswith('\n'):
            txt += '\n'
        return txt + '\n' + replacement