import slicer

extensionName = 'NNInteractive'

em = slicer.app.extensionsManagerModel()
em.interactive = False  # prevent display of popups

restart = True

if not em.installExtensionFromServer(extensionName, restart):
    raise ValueError(f"Failed to install {extensionName} extension")

pip_packages = [
    "requests_toolbelt==1.0.0",
    "imageio==2.37.2",
    "lazy-loader==0.4",
    "networkx==3.2.1",
    "scikit-image==0.24.0",
    "tifffile==2024.8.30",
]

for pkg in pip_packages:
    slicer.util.pip_install(pkg)
