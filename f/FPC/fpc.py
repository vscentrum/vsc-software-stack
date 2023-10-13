##
# Copyright 2009-2023 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
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
