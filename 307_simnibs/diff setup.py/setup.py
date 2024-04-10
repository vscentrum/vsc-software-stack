from setuptools import setup, find_packages, Extension
import os
import sys
import glob
import shutil
import urllib
import tempfile
import zipfile
import tarfile
from setuptools.command.build_ext import build_ext
from setuptools import find_namespace_packages
from distutils.dep_util import newer_group
import numpy as np

    
####################################################
# add all scripts in the cli folder as 
# console_scripts or gui_scripts
####################################################

# IMPORTANT: For the postinstall script to also work
# ALL scripts should be in the simnibs/cli folder and have
# a if __name__ == '__main__' clause

script_names = [os.path.splitext(os.path.basename(s))[0]
                for s in glob.glob('simnibs/cli/*.py')]

console_scripts = []
for s in script_names:
    if s not in ['__init__', 'simnibs_gui']:
        console_scripts.append(f'{s}=simnibs.cli.{s}:main')
console_scripts.append(f'simnibs=simnibs.cli.run_simnibs:main')

gui_scripts = [
    'simnibs_gui=simnibs.cli.simnibs_gui:main',
]

''' 
C extensions

CGAL Compilation
-----------------

CGAL >= 5 is a header-only library, so we download it right before compiling.

Compilation requires:
GCC >= 6.3 or Apple Clang == 10.0.1 or MSVC >= 14.0
    conda install gcc_linux-64 gxx_linux-64 gfortran_linux-64
Boost >= 1.57

Boost can be instaled with
    Ubuntu: sudo apt install libboost-all-dev
    MacOS: brew install boost
    Windows: conda install boost
    Boost is also header-only, so we only need it during compile time

For more info, refer to https://doc.cgal.org/latest/Manual/thirdparty.html

'''

# Information for CGAL
CGAL_version = '5.4'
CGAL_headers = os.path.join(os.getenv('EBROOTCGAL'), 'include')
cgal_mesh_macros = [
    ('CGAL_MESH_3_NO_DEPRECATED_SURFACE_INDEX', None),
    ('CGAL_MESH_3_NO_DEPRECATED_C3T3_ITERATORS', None),
    ('CGAL_CONCURRENT_MESH_3', None),
    ('CGAL_EIGEN3_ENABLED', None),
    ('CGAL_USE_ZLIB', 1),
    ('CGAL_LINKED_WITH_TBB', None)
]

# Information for eigen library
eigen_version = '3.3.7'
eigen_headers = os.path.join(os.getenv('EBROOTEIGEN'), 'include')

# Information for Intel TBB download
tbb_version = '2020.1'
tbb_headers = os.path.join(os.getenv('EBROOTTBB'), 'include')

tbb_libs = [
    os.path.join(os.getenv('EBROOTTBB'), 'lib', 'libtbb.so'),
    os.path.join(os.getenv('EBROOTTBB'), 'lib', 'libtbb.so.2'),
    os.path.join(os.getenv('EBROOTTBB'), 'lib', 'libtbbmalloc.so'),
    os.path.join(os.getenv('EBROOTTBB'), 'lib', 'libtbbmalloc.so.2'),
]

#### Setup compilation arguments

petsc_libs = ['petsc']
petsc_include = [
    np.get_include(),
    'simnibs/external/include/linux/petsc'
]
petsc_dirs = ['simnibs/external/lib/linux']
petsc_runtime = ['$ORIGIN/../external/lib/linux']
petsc_extra_link_args = None

cgal_libs = ['mpfr', 'gmp', 'z', 'tbb', 'tbbmalloc', 'pthread']
cgal_include = [
    np.get_include(),
    CGAL_headers,
    eigen_headers,
    tbb_headers,
    'simnibs/external/include/linux/mpfr',
    'simnibs/external/include/linux/gmp'
]
cgal_dirs = ['simnibs/external/lib/linux']
cgal_runtime = ['$ORIGIN/../../external/lib/linux']
# Add -Os -flto for much smaller binaries
cgal_compile_args = [
    '-Os', '-flto',
    '-frounding-math',
    '-std=gnu++14',
    '-w',  # removes warnings as errors
    '-fcompare-debug-second',  # removes notes as errors
]
cgal_mesh_macros += [('NOMINMAX', None)]
cgal_link_args = None

cython_msh = Extension(
    'simnibs.mesh_tools.cython_msh',
    ["simnibs/mesh_tools/cython_msh.pyx"],
    include_dirs=[np.get_include()],
    extra_compile_args=['-w'],
)
marching_cubes_lewiner_cy = Extension(
    'simnibs.segmentation._marching_cubes_lewiner_cy',
    ["simnibs/segmentation/_marching_cubes_lewiner_cy.pyx"],
    include_dirs=[np.get_include()],
    extra_compile_args=['-w'],
)
cat_c_utils = Extension(
    'simnibs.segmentation._cat_c_utils',
    ["simnibs/segmentation/_cat_c_utils.pyx", "simnibs/segmentation/cat_c_utils/genus0.c"],
    include_dirs=[np.get_include(), 'simnibs/segmentation/cat_c_utils'],
    extra_compile_args=['-w', '-std=gnu99'],
)
thickness = Extension(
    'simnibs.segmentation._thickness',
    ["simnibs/segmentation/_thickness.pyx"],
    include_dirs=[np.get_include()],
    extra_compile_args=['-w'],
)
petsc_solver = Extension(
    'simnibs.simulation.petsc_solver',
    sources=["simnibs/simulation/petsc_solver.pyx"],
    depends=["simnibs/simulation/_solver.c"],
    include_dirs=petsc_include,
    library_dirs=petsc_dirs,
    libraries=petsc_libs,
    runtime_library_dirs=petsc_runtime,
    extra_link_args=petsc_extra_link_args,
    extra_compile_args=['-w'],
)
# I separated the CGAL functions into several files for two reasons
# 1. Reduce memory consumption during compilation in Linux
# 2. Fix some compilation problems in Windows
create_mesh_surf = Extension(
    'simnibs.mesh_tools.cgal.create_mesh_surf',
    sources=["simnibs/mesh_tools/cgal/create_mesh_surf.pyx"],
    depends=["simnibs/mesh_tools/cgal/_mesh_surfaces.cpp"],
    language='c++',
    include_dirs=cgal_include,
    libraries=cgal_libs,
    library_dirs=cgal_dirs,
    runtime_library_dirs=cgal_runtime,
    extra_compile_args=cgal_compile_args,
    extra_link_args=cgal_link_args,
    define_macros=cgal_mesh_macros
)
create_mesh_vol = Extension(
    'simnibs.mesh_tools.cgal.create_mesh_vol',
    sources=["simnibs/mesh_tools/cgal/create_mesh_vol.pyx"],
    depends=["simnibs/mesh_tools/cgal/_mesh_volumes.cpp"],
    language='c++',
    include_dirs=cgal_include,
    libraries=cgal_libs,
    library_dirs=cgal_dirs,
    runtime_library_dirs=cgal_runtime,
    extra_compile_args=cgal_compile_args,
    extra_link_args=cgal_link_args,
    define_macros=cgal_mesh_macros
)
cgal_misc = Extension(
    'simnibs.mesh_tools.cgal.cgal_misc',
    sources=["simnibs/mesh_tools/cgal/cgal_misc.pyx"],
    depends=["simnibs/mesh_tools/cgal/_cgal_intersect.cpp"],
    language='c++',
    include_dirs=cgal_include,
    libraries=cgal_libs,
    library_dirs=cgal_dirs,
    runtime_library_dirs=cgal_runtime,
    extra_compile_args=cgal_compile_args,
    extra_link_args=cgal_link_args,
)

extensions = [
    cython_msh,
    marching_cubes_lewiner_cy,
    cat_c_utils,
    thickness,
    petsc_solver,
    create_mesh_surf,
    create_mesh_vol,
    cgal_misc
]

def install_lib(libs, build_path):
    folder_name = 'linux'
    for l in libs:
        shutil.copy(
            l, f'simnibs/external/lib/{folder_name}',
            follow_symlinks=False
        )
        if build_path:
            shutil.copy(
                l, f'{build_path}simnibs/external/lib/{folder_name}',
                follow_symlinks=False
            )


class build_ext_(build_ext):
    '''
    Build the extension, download some dependencies and remove stuff from other OS
    '''
    def run(self):
        from Cython.Build import cythonize
        ## Cythonize
        self.extension = cythonize(self.extensions)
        changed_meshing = (
            newer_group(
                create_mesh_surf.sources + create_mesh_surf.depends,
                self.get_ext_fullpath(create_mesh_surf.name),
                'newer'
            ) or
            newer_group(
                create_mesh_vol.sources + create_mesh_vol.depends,
                self.get_ext_fullpath(create_mesh_vol.name),
                'newer'
            ) or
            newer_group(
                cgal_misc.sources + cgal_misc.depends,
                self.get_ext_fullpath(cgal_misc.name),
                'newer'
            )
        )
        if self.force or changed_meshing:
            if self.inplace:
                build_lib = ""
            else:
                build_lib = self.build_lib + "/"
            install_lib(tbb_libs, build_lib)

        # Compile
        build_ext.run(self)

setup(
    name='simnibs',
    version="4.0.1",
    description='www.simnibs.org',
    author='SimNIBS developers',
    author_email='support@simnibs.org',
    packages=find_namespace_packages(),
    license='GPL3',
    ext_modules=extensions,
    include_package_data=True,
    cmdclass={
        'build_ext': build_ext_
        },
    entry_points={
        'console_scripts': console_scripts,
        'gui_scripts': gui_scripts
    },
    install_requires=[
        'numpy>=1.16',
        'scipy>=1.2',
        'h5py>=2.9',
        'nibabel>=2.3',
        'packaging',
        'requests',
        'charm-gems',
        'fmm3dpy'
    ],
    extras_require={
        'GUI': ['pyqt5', 'pyopengl']
    },
    setup_requires=[
        'numpy>=1.16',
        'cython'
    ],
    tests_require=['pytest', 'mock'],
    zip_safe=False
)
