"""
EasyBuild support for FPC, implemented as an easyblock

@author: Steven Vandenbrande (KU Leuven)
"""
from easybuild.easyblocks.generic.binary import Binary
from easybuild.framework.easyblock import EasyBlock
from easybuild.tools.modules import get_software_root
from easybuild.tools.run import run_cmd_qa


class EB_FPC(Binary):
    """Support for installing FPC (Free Pascal Compiler)."""

    def extract_step(self):
        """Use default extraction procedure instead of the one for the Binary easyblock."""
        EasyBlock.extract_step(self)

    def install_step(self):
        """Install FPC using 'install.sh' script."""

        # Simple question-answer pairs
        qanda = {
            'Install documentation (Y/n) ?': 'Y',
            'Install demos (Y/n) ?': 'Y',

        }
        # Question-answer pairs with regular expressions
        std_qa = {
           r'Install prefix \(\/usr or \/usr\/local\)  \[[\S]*\] : ': self.installdir,
           r'Install demos in[\s\S]*': '',
        }
        
        run_cmd_qa('./install.sh', qanda, std_qa=std_qa, log_all=True, simple=True)
