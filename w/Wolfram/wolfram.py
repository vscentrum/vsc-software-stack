"""
EasyBuild support for building and installing Wolfram, implemented as an easyblock

@author: Kenneth Hoste (Ghent University)
"""

from easybuild.tools import LooseVersion
import glob
import os

from easybuild.easyblocks.generic.binary import Binary
from easybuild.framework.easyconfig import CUSTOM
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.run import run_cmd_qa


class EB_Wolfram(Binary):
    """Support for building/installing Wolfram."""

    @staticmethod
    def extra_options():
        """Additional easyconfig parameters custom to Wolfram."""
        extra_vars = {
            'activation_key': [None, "Activation key (expected format: 0000-0000-AAAAA)", CUSTOM],
        }
        return Binary.extra_options(extra_vars)

    def configure_step(self):
        """No configuration for Wolfram."""
        # ensure a license server is specified
        if self.cfg['license_server'] is None:
            raise EasyBuildError("No license server specified.")

    def build_step(self):
        """No build step for Wolfram."""
        pass

    def install_step(self):
        """Install Wolfram using install script."""

        # make sure $DISPLAY is not set (to avoid that installer uses GUI)
        orig_display = os.environ.pop('DISPLAY', None)

        install_script_glob = '%s_%s*_LIN.sh' % (self.name, self.version)

        matches = glob.glob(install_script_glob)
        if len(matches) == 1:
            install_script = matches[0]
            cmd = self.cfg['preinstallopts'] + './' + install_script
            shortver = '.'.join(self.version.split('.')[:2])
            qa_install_path = os.path.join('/usr', 'local', 'Wolfram', self.name, shortver)
            qa = {
                r"Enter the installation directory, or press ENTER to select %s: >" % qa_install_path: self.installdir,
                r"Create directory (y/n)? >": 'y',
                r"Should the installer attempt to make this change (y/n)? >": 'n',
                r"or press ENTER to select /usr/local/bin: >": os.path.join(self.installdir, "bin"),
            }
            no_qa = [
                r"Now installing.*\n\n.*\[.*\].*",
            ]
            run_cmd_qa(cmd, qa, no_qa=no_qa, log_all=True, simple=True, maxhits=200)
        else:
            raise EasyBuildError("Failed to isolate install script using '%s': %s", install_script_glob, matches)

        # add license server configuration file
        # some relevant documentation at http://reference.wolfram.com/mathematica/tutorial/ConfigurationFiles.html
        mathpass_path = os.path.join(self.installdir, 'Configuration', 'Licensing', 'mathpass')
        try:
            # append to file, to avoid overwriting anything that might be there
            f = open(mathpass_path, "a")
            f.write("!%s\n" % self.cfg['license_server'])
            f.close()
            f = open(mathpass_path, "r")
            mathpass_txt = f.read()
            f.close()
            self.log.info("Updated license file %s: %s" % (mathpass_path, mathpass_txt))
        except IOError as err:
            raise EasyBuildError("Failed to update %s with license server info: %s", mathpass_path, err)

        # restore $DISPLAY if required
        if orig_display is not None:
            os.environ['DISPLAY'] = orig_display

    def post_install_step(self):
        """Activate installation by using activation key, if provided."""
        if self.cfg['activation_key']:
            # activation key is printed by using '$ActivationKey' in Wolfram, so no reason to keep it 'secret'
            self.log.info("Activating installation using provided activation key '%s'." % self.cfg['activation_key'])
            qa = {
                r"(enter return to skip Web Activation):": self.cfg['activation_key'],
                r"In[1]:= ": 'Quit[]',
            }
            noqa = [
                '^%s %s .*' % (self.name, self.version),
                '^Copyright.*',
            ]
            run_cmd_qa(os.path.join(self.installdir, 'bin', 'math'), qa, no_qa=noqa)
        else:
            self.log.info("No activation key provided, so skipping activation of the installation.")

        super(EB_Wolfram, self).post_install_step()

    def sanity_check_step(self):
        """Custom sanity check for Wolfram."""
        custom_paths = {
            'files': ['bin/wolfram'],
            'dirs': ['AddOns', 'Configuration', 'Documentation', 'Executables', 'SystemFiles'],
        }
        if LooseVersion(self.version) >= LooseVersion("11.3.0"):
            custom_paths['files'].append('Executables/wolframscript')
        elif LooseVersion(self.version) >= LooseVersion("11.0.0"):
            custom_paths['files'].append('bin/wolframscript')

        custom_commands = ['wolfram --version']

        super(EB_Wolfram, self).sanity_check_step(custom_paths=custom_paths, custom_commands=custom_commands)

    def make_module_req_guess(self):
        """Add both 'bin' and 'Executables' directories to PATH."""

        guesses = super(EB_Wolfram, self).make_module_req_guess()

        guesses.update({'PATH': ['bin', 'Executables']})

        return guesses
