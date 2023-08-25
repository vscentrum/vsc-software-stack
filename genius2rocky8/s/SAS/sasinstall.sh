#!/bin/sh
#information used to specify the installation path
_TOOLCHAIN_VERSION_=2018a
_SAS_VERSION_=9.4TS1M4
_SAS_INSTALLATION_FOLDER_=/apps/leuven/${VSC_OS_LOCAL}/${VSC_ARCH_LOCAL}${VSC_ARCH_SUFFIX}/$_TOOLCHAIN_VERSION_/software/SAS/$_SAS_VERSION_
#loation of the SAS installation files
_SAS_SOURCE_FILES=/apps/leuven/sources/s/SAS/KUL_EAS_FOR_KUL_ON_LINUX_64BIT
#location of the SAS installation data, this includes the license file
#and the template file used as a reponse during a silent install
_SAS_INSTALLATION_DATA_FOLDER=/apps/leuven/sources/s/SAS/SID
_SAS_INSTALLATION_RESPONSE_FILE=sas94_properties_template.response
#_SAS_INSTALLATION_FOLDER_=/data/leuven/sys/x0051749/software/tmp
_SAS_LICENSE_FILE_=SAS94_9CW9Q5_50601860_LINUX_X86-64.txt

#checing if the response file is there
#remove an existing generated response file
if [ ! -f "$_SAS_INSTALLATION_DATA_FOLDER/$_SAS_INSTALLATION_RESPONSE_FILE" ]; then
    echo "ERROR: $_SAS_INSTALLATION_DATA_FOLDER/$_SAS_INSTALLATION_RESPONSE_FILE does not exist"
fi

if [ -f "$_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response" ]; then
    echo "$_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response exists. Deleting it."
    rm $_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response
fi

#generate the installation response file with update information for the installation PATH and license file
/bin/sed  -e "s|_SAS_INSTALLATION_FOLDER_|$_SAS_INSTALLATION_FOLDER_|"  -e "s|_SAS_LICENSE_FILE_| $_SAS_INSTALLATION_DATA_FOLDER/$_SAS_LICENSE_FILE_|" < $_SAS_INSTALLATION_RESPONSE_FILE > $_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response
if [ -f "$_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response" ]; then
    echo "$_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response generated"
fi

#start the installation in a sileten mode without interactive prompts
echo "starting to install SAS"
echo "$_SAS_SOURCE_FILES/setup.sh -quiet -responsefile $_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response"
$_SAS_SOURCE_FILES/setup.sh -quiet -responsefile $_SAS_INSTALLATION_DATA_FOLDER/sas94_generated_properties.response

