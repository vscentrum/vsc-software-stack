# Installation instructions Matlab

These instructions should be the same for all MATLAB versions. If future versions allow command line installations, this
README should become obsolete.

Matlab requires a manual installation with a GUI, as the command line options that Matlab provides do not seem to work.
The easiest method is connecting to NX, and start a session on the appropriate installation node (do not forget to allow X-forwarding).

## Getting the source code
If you need the source code of a certain Matlab version, you should ask Frank Van Puyvelde. Next to the source code,
you will need a file installation key for Matlab itself, also a file installation key for Matlab Parallel Server and a license file.
Frank is aware of this, and normally he should provide all of these already. Examples of the full set of files can be found in
/apps/leuven/sources/m/MATLAB. If you install a new version, place the source files here as well.

## Installation of Matlab 
Once you have all the files, you can start the installation process. First of all you will have to mount the iso that is provided:

```bash
sudo mount -o loop <iso_name>.iso <mount_location>
```

Then, cd into the mount directory and start the install gui::

```bash
cd <mount_location>
./install
```

A GUI should pop up. You will be asked to provide an email address, but instead you should click 'advanced options' on top, and
select 'I have a File Installation Key'. Accept the term and agreements, and then provide the key that has been given to you.

In the next step, you should provide the path to the license file you received. 

Then, provide the install location. This should be in ```/apps/leuven/<OS_name>/<node_architecture>/<toolchain>/software/MATLAB```.

You can select all packages for the installation. Follow the next two steps, and that's it!

## Installation of Matlab Parallel Server
Matlab Parallel Server allows users to use multiple nodes on a cluster. This is licensed separately, meaning it also has a separate
key. Normally you should have received this key as well.

To install Parallel Server, just conduct the same steps as above, the difference being that you need to provide the Parallel Server
key instead of the general one. You should notice in the package list that only Matlab Parallel Server is selected. 
