import configparser
import slicer

config = configparser.ConfigParser()
config.optionxform = str  # make options case sensitive

configpath = f'slicer.org/Slicer-{slicer.app.revision}.ini'
config.read(configpath)

modulepath = 'fastnn/slicer_plugin/fast_nnInteractive'

paths = config['Modules'].get('AdditionalPaths')
config.remove_option('Modules', 'AdditionalPaths')
config.set('Modules', 'AdditionalPaths', ', '.join([paths, modulepath]))

with open(configpath, mode='w', encoding='utf-8') as f:
    config.write(f)

pip_packages = [
    # extra packages in addition to the ones required for NNInteractive
    "matplotlib",
]

for pkg in pip_packages:
    slicer.util.pip_install(pkg)
