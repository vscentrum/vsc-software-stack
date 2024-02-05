# Installing Matlab

## Getting the installation files

The installation files for any new Matlab installations need to be requested to the person responsible for anything Matlab related. At the time of writing this is Frank Van Puyvelde. Ask him to download the latest release from Matlab, and he will download it to his vsc-account. He will pass you the location, where you should find the following files:

- R<version>.Linux.iso
- fik-matlab-concurrent.txt: the general product key
- fik-matlab-parallel-r<version>.txt: the product key for Parallel Server

The above names might vary somewhat in reality, but you should adopt the above naming schemes. Place these files in `/apps/leuven/sources/m/MATLAB/R<version>`.


## Creating and running the easybuild file

Minor changes are needed here. Next to changing the version, you should also adapt the `key` variable to the new key: this is the key listed in the 'fik-matlab-concurrent.txt' file. After this, just start the easybuild installation as usual.

## Adding Parallel Server

It is not possible to add the installation of the Parallel Server package to the Easybuild file. For this reason you will need to add this manually:

- Open a NX session
- mount the iso image to a directory of your choice: `sudo mount -o loop /apps/leuven/sources/m/MATLAB/R<version>/R<version>_Linux.iso </your/mount/path>
- From the directory you have mounted the iso image in: `./install`
- A GUI will appear. In the right top corner select 'Advanced options - I have a File Installation Key'
- Accept the licentse agreement
- Enter the Parallel Server file installation key: this is the key in fik-matlab-parallel-r<version>.txt
- Add the path to the license file: `/apps/leuven/sources/m/MATLAB/matlab_license_concurrent_kuleuven.dat`
- Select the destination folder: this should be your Matlab installation directory: `/apps/leuven/<OS>/<node_arch>/<toolchain>/software/MATLAB/<version>` 
- If everything went ok, Matlab should detect the already installed packages, and only MATLAB Parallel Server should be selected in the following menu
- Install
