#!/bin/bash
#
#   @(#)
#   @(#) CREX: Shell script for the creation of a reference executable.
#   @(#)       Since version 2.0 extended to MPI parallelization.
#   @(#)       Since version 3.0 ported to Bourne-Again-Shell (bash).
#   @(#)
#   @(#) Version 1.1 (05.09.95, Matthias Krack)
#   @(#) Version 1.2 (07.05.96, Matthias Krack)
#   @(#) Version 1.3 (28.01.97, Matthias Krack)
#   @(#) Version 1.4 (05.06.97, Matthias Krack)
#   @(#) Version 1.5 (10.01.98, Matthias Krack)
#   @(#) Version 1.6 (19.09.00, Andreas M. Koster)
#   @(#) Version 1.7 (07.03.02, Andreas M. Koster)
#   @(#) Version 1.8 (19.05.02, Andreas M. Koster)
#   @(#) Version 1.9 (20.10.04, Andreas M. Koster)
#   @(#)
#   @(#) Version 2.0 (21.11.04, Andreas M. Koster)
#   @(#) Version 2.1 (01.12.04, Florian Janetzko)
#   @(#) Version 2.2 (22.05.05, Florian Janetzko)
#   @(#) Version 2.3 (08.06.05, Andreas M. Koster)
#   @(#) Version 2.4 (30.06.05, Florian Janetzko)
#   @(#)
#   @(#) Version 3.0 (29.10.05, Florian Janetzko)
#   @(#) Version 3.1 (17.03.21, Alex Domingo)
#
### Command options ###
#
#   $1: crex options (-c, +c, -p, -r)
#   $2: compilation type (dbg, dpg, ext, mpi, opt, pro, std)
#
    shopt -s extglob nullglob
    set +o noclobber
#
### Load the name of this procedure ###
#
    PROC=${0##*/}
#
### Initialization ###
#
    INCSEP=' '
#
    typeset -i number totnum
#
### Aliasing of commands ###
#
    alias cp="\cp"
    alias dc="\dc"
    alias echo="\echo"
    alias find="\find"
    alias grep="\grep"
    alias mkdir="\mkdir"
    alias mv="\mv"
    alias rm="\rm"
    alias touch="\touch"
#
### No localization ###
#
    LANG=C
    LC_MESSAGES=C
#
### Macro definitions ###
#
    function ifprint
    {
      if [[ $PRINTLEVEL = "full" ]]; then echo -e $1; fi
    }
    function question
    {
      echo -e "\n $1? [$2]: \c";
    }
#
    function clean
    {
      if [[ -d $TMPOBJ ]]; then
        mv $TMPOBJ/*.[ho] $REFOBJ 2>/dev/null
        rm -rf $TMPOBJ
      fi
      if [[ -n $REFOBJ ]]; then
        find $REFOBJ -size 0 -name "*.[ho]" -exec rm {} \;
      fi
      if [[ -f $tmpfile ]]; then rm -f $tmpfile; fi
      if [[ -f $refinc ]]; then rm -f $refinc; fi
      if [[ -f $refsrc ]]; then rm -f $refsrc; fi
      if [[ -f $refmpi ]]; then rm -f $refmpi; fi
      if [[ -f $tmpinc ]]; then rm -f $tmpinc; fi
      if [[ -f $tmpsrc ]]; then rm -f $tmpsrc; fi
      if [[ -f $tmplist ]]; then rm -f $tmplist; fi
      if [[ -n $EXCLUDE ]]; then
        for modul in $EXCLUDE; do
          extension=${modul##*.}
          Extension=$(echo $extension | tr a-z A-Z)
          modul=${modul%.$extension}.$Extension
          srcfile=$(find $REFSRC -name $modul -print)
          if [[ -f $srcfile ]]; then
            mv $srcfile ${srcfile%.$Extension}.$extension
          fi
        done
      fi
      if [[ -d $REFEXL ]]; then
        for file in $REFEXL/*/*.[fh]; do
          rm $file
        done
      fi
    }
#
    function exit_1
    {
      clean
      echo -e "\n Abnormal termination of $PROC.\n\n"
      exit 1
    }
#
    function iferrstat
    {
      if (( $? != 0 )); then
        if [[ -n $1 ]]; then
          echo -e "\n $PROC: An error has occurred executing the command\n\n $1\n"
        fi
        if [[ -n $2 ]]; then
          echo -e " $2\n"
        fi
        exit_1
      fi
    }
#
    function getvar
    {
      while read var arg; do
       if [[ $var = $1 ]]; then
         eval $2='$arg'
         return 0
       fi
      done <$datafile
      return 1
    }
#
    function getextlib
    { 
      while read var arg; do
        if [[ ${var:0:3} = "EL:" ]]; then
          if [[ -z $arg ]]; then
            echo -e "\n $PROC: No value given for option $var."
            exit_1
          fi
          eval local ne=\$$1
          ne=$((ne+1))
          local ol=$((${#var}-3))
          local eln=$( echo ${var:3:$ol}|tr '[:upper:]' '[:lower:]')
#         eval $3=$arg\" \"\$$3
          eval $3=\"$arg \"\$$3
          eval $2\[$ne\]=$eln
          eval $1=$ne
        fi 
      done <$datafile
      return 1
    }
#
    function max
    {
      typeset -i maxvalue=0 value status=1
      for value in $*; do
        if (( $value >= $maxvalue )); then
          maxvalue=$value
          status=0
        fi
      done
      echo -e $maxvalue
      return $status
    }
    function getos
    {
      while read var arg; do
        case $1 in ($var) eval $2='$arg'
                               return 0;;
        esac
      done <$databasedat
      return 1
    }
    function getsysplat
    {
      eval var='$1'
      var=${var##PLATFORM }
      eval $2='${var##*SYSTEM }'
      eval $3='${var%%SYSTEM*}'
    }
    function getversion
    {
      eval var='$1'
      eval date=$(echo $var | cut -f2 -d" ")
      eval var=$(echo $var | cut -f1 -d" ")
      if [[ $date = $var ]]; then
        eval $5=''
      else
        eval $5="\($date\)"
      fi
      typeset -i part
      for (( part=1; part < 4; part=part+1)); do
        versnum[$part]=$(echo $var | cut -f$part -d ".")
      done
      versnum[4]=$(echo $var | cut -f4 -d ".")
      eval $2='$(echo ${versnum[1]}.${versnum[2]})'
      if [[ -n ${versnum[4]} ]]; then
        eval $3='${versnum[3]}'
        eval $4='${versnum[4]}'
      elif [[ -n ${versnum[3]} ]]; then
        if [[ $(expr index "${versnum[3]}" "1234567890") -eq 1 ]]; then
          eval $3='${versnum[3]}'
          eval $4=''
        else
          eval $3=''
          eval $4='${versnum[3]}'
        fi
      fi
    }
#
### Trap user interrupt and clean the current directory ###
#
    trap 'echo -e "\n\n The procedure $PROC was interrupted.\n\n"; \
          clean; \
          exit 2' 1 2 3
#
### Set root directory for reference program version ###
#
    if [[ -n $CREX_ROOT ]]; then
      ROOTDIR=$CREX_ROOT
    else
      ROOTDIR=/usr/local
    fi
#
### Load the name of the program to create ###
#
    if [[ -n $CREX_PROG ]]; then
      PROG=$CREX_PROG
    else
      PROG=deMon
    fi
#
### Load the number of the default program version ###
#
#    read VERSION <$ROOTDIR/$PROG/.default-version
#
### Get version, revision and compiler ###
#
    getversion "$VERSION" VERSION REVISION FTN DATE
#
    echo -e "\n Creation of a master executable for $PROG:\n"
    echo -e " Program version: $VERSION"
    if [[ -n $REVISION ]]; then
      echo -e " Revision       : $REVISION $DATE"
    elif [[ -n $DATE ]]; then
      echo -e " Date           : $DATE"
    fi
#
    if [[ -n $REVISION ]]; then
      VERSION=$(echo "$VERSION.$REVISION")
    fi
#
### Set an alternate compiler ###
#
    FTN0=$FTN
#
    if [[ -n "$CREX_FTN" ]]; then
      FTN=$CREX_FTN
    fi
#
### Load informations for system identification ###
#
    ostype=$(uname -s)
    osversion=$(uname -v)
    osrelease=$(uname -r)
    machine=$(uname -m)
#
    platform="${ostype}-${osversion}-${osrelease}-${machine}"
#
### Load information for CPU identification on Linux ###
#
    if [[ $ostype = "Linux" ]]; then
      cputype=$(grep "model name" /proc/cpuinfo | cut -f2 -d":" | cut -f2 -d" ")
      cputype=$(echo $cputype | cut -f1 -d" ")
      platform="${ostype}-${cputype}-${osrelease}-${machine}"
    fi
#
### Select compiler on Linux ###
#
    if [[ -z $FTN && $ostype = "Linux" ]]; then
      while true; do
        echo -e "\n Select compiler (Linux only).\n"
        echo -e "   1. Portland Group pgf90"
        echo -e "   2. Intel Fortran 90"
        echo -e "   3. xlf (IBM)"
        echo -e "   4. GNU Fortran 90 (gfortran)"
        echo -e "\n Enter a number: \c"
        read compiler
        case $compiler in
          (+([0-9])) number=$compiler;;
                 (*) if [[ -n $compiler ]]; then
                       echo -e "\n $PROC: $compiler is not a number"
                     fi
                     continue;;
        esac
        if (( $number == 1 )); then
          FTN="pgf90"
          echo $VERSION.$FTN $DATE >$ROOTDIR/$PROG/.default-version
          break
        elif (( $number == 2 )); then
          FTN="ifort"
          echo $VERSION.$FTN $DATE >$ROOTDIR/$PROG/.default-version
          break
        elif (( $number == 3 )); then
          FTN="xlf"
          echo $VERSION.$FTN $DATE >$ROOTDIR/$PROG/.default-version
          break
        elif (( $number == 4 )); then
          FTN="gfortran"
          echo $VERSION.$FTN $DATE >$ROOTDIR/$PROG/.default-version
          break
        fi
      done 
#
      FTN0=$FTN
#
    elif [[ $ostype = "Linux" ]]; then
      echo -e "\n $FTN Fortran Compiler is used"
    fi
#
### Define full path to database.dat file ###
#
    databasedat=$ROOTDIR/database/database.dat
    if [[ ! -e $databasedat ]]; then
      echo -e "\n $PROC: The file $databasedat does not exist.\n"
    fi
#
### Get platform and system information ###
#
    getos $platform os
#
    if [[ $? = 0 ]]; then
      getsysplat "$os" SYSTEM PLATFORM
      echo -e "\n Platform identified."
      echo -e "\n Platform code: ${PLATFORM}"
      echo -e "\n ${PROC} system code: ${SYSTEM}"
      if [[ $ostype = "Linux" ]]; then
        echo -e "\n Compiler code: ${FTN}"
      fi
    else
      echo -e "\n Platform not identified."
      echo -e "\n Platform code: unknown"
      echo -e "\n ${PROC} system code: unknown"
      echo -e "\n Operating system ${platform} is unknown."
      echo -e " Using the default database file database.new"
      question "Do you want to continue?" "y/n"
      read answer
#
      answer=${answer##+(" ")} 
      answer=$(expr substr "$answer" 1 1)
#
      if [[ $answer != [yY] ]]; then
        exit 1;
      fi
      PLATFORM='database.new'
    fi
#
### Stop if only platform information is requested
#
    case $1 in
      (-info|-i) exit 0;
    esac
#
### Read optional arguments ###
#
    CHECK=no
    FULL_RECOMPILATION=no
    if [[ $CREX_PRINTLEVEL = "full" ]]; then
      PRINTLEVEL=full
    else
      PRINTLEVEL=standard
    fi
#
    while true; do
      case $1 in
            (-check|-c) CHECK=true; shift; continue;;
            (+check|+c) CHECK=false; shift; continue;;
        (-printfull|-p) PRINTLEVEL=full; shift; continue;;
        (-recompile|-r) FULL_RECOMPILATION=true; shift; continue;;
                    (*) break;;
      esac
    done
#
### Define the type of executable ###
#
    if [[ ! $PLATFORM = "database.new" ]]; then
      if [[ -z $1 ]]; then
        while true; do
          echo -e "\n Choose a compilation type:\n"
          echo -e "   1. Debug compilation"
          echo -e "   2. Standard compilation"
          echo -e "   3. Optimization compilation"
          echo -e "   4. Parallel MPI compilation"
          echo -e "   5. Parallel debug compilation"
          echo -e "   6. Parallel compilation for profiling"
          echo -e "   7. Parallel compilation with extensions"
          echo -e "\n Select a number: \c"
          read number
          case $number in
            (1) EXT=dbg; break;;
            (2) EXT=std; break;;
            (3) EXT=opt; break;;
            (4) EXT=mpi; break;;
            (5) EXT=dpg; break;;
            (6) EXT=pro; break;;
            (7) EXT=ext; break;;
            (*) echo -e "\n Invalid compilation type. Try again."; continue;;
          esac
        done
      else
        EXT=$1
      fi
    else
      EXT="unknown"
    fi
#
    case $EXT in
         (debug|dbg|d) EXT=dbg
                       echo -e "\n\n Debug compilation selected ($EXT).\n";;
      (standard|std|s) EXT=std
                       echo -e "\n\n Standard compilation selected ($EXT).\n";;
      (optimize|opt|o) EXT=opt
                       echo -e "\n\n Optimization compilation selected ($EXT).\n";;
      (parallel|mpi|m) EXT=mpi
                       echo -e "\n\n Parallel MPI compilation selected ($EXT).\n";;
        (pdebug|dpg|p) EXT=dpg
                       echo -e "\n\n Parallel debug compilation selected ($EXT).\n";;
     (profiler|pro|pf) EXT=pro
                       echo -e "\n\n Parallel profiling compilation selected ($EXT).\n";;
      (extended|ext|e) EXT=ext
                       echo -e "\n\n Parallel+extensions compilation selected ($EXT).\n";;
             (unknown) EXT=std
                       echo -e "\n\n Unknown compilation type. Generating standard verion.\n";;
                   (*) echo -e "\n $PROC: Unknown compilation type $EXT.\n"
                       exit_1;;
    esac
#
### Path to the program version ###
#
    REFDIR=$ROOTDIR
#
    if [[ ! -d $REFDIR ]]; then
      echo -e "$PROC: The directory $REFDIR does not exist."
      exit_1
    fi
#
### Path to the source files ###
#
    REFSRC=$REFDIR/source
#
    if [[ ! -d $REFSRC ]]; then
      echo -e "$PROC: The directory $REFSRC does not exist."
      exit_1
    fi
#
### Path to the directory with the include files ###
#
    REFINC=$REFDIR/include
#
    if [[ ! -d $REFINC ]]; then
      echo -e "$PROC: The directory $REFINC does not exist."
      exit_1
    fi
#
### Path to the directory for external libraries ###
#
    REFEXL=$REFDIR/extlib
#
    if [[ ! -d $REFEXL ]]; then
      echo -e "$PROC: The directory $REFEXL does not exist."
      echo -e "$PROC: The directory $REFEXL will be created."
      mkdir -p $REFEXL
    fi
#
### Path to the object files ###
#
    REFOBJ=$REFDIR/object.$EXT.$FTN
#
    if [[ ! -d $REFOBJ ]]; then
      mkdir $REFOBJ
      iferrstat "mkdir $REFOBJ"
      chmod 755 $REFOBJ
      iferrstat "chmod 755 $REFOBJ"
      FULL_RECOMPILATION=true
      if [[ x"$FTN0" == x"$FTN" ]]; then
        ln -sf $REFOBJ $REFDIR/object.$EXT
      fi
    else
      if [[ -s $REFOBJ/$PROG.$VERSION.$EXT ]]; then
        chmod 600 $REFOBJ/$PROG.$VERSION.$EXT
        iferrstat "chmod 600 $REFOBJ/$PROG.$VERSION.$EXT"
      fi
      find $REFOBJ -name "*.[ho]" -exec chmod 600 {} \;
    fi
#
### Path to the database directory ###
#
    REFDAT=$REFDIR/database
#
    if [[ ! -d $REFDAT ]]; then
      echo -e "$PROC: The directory $REFDAT does not exist."
      exit_1
    fi
#
### Define database files ###
#
    if [[ ! $PLATFORM = 'database.new' ]]; then
      if [[ -n $FTN ]]; then
        datafile=$REFDAT/$SYSTEM.$EXT.$FTN
      else
        datafile=$REFDAT/$SYSTEM.$EXT
      fi
    else
        datafile=$REFDAT/database.new
    fi
#
### Copy dummy part of external libaries ###
#
    export ELDUMNAM=dummy
    export ELACTNAM=active
    for exldir in $REFEXL/*
    do
      exldumdir=$exldir/$ELDUMNAM
      if [[ ! -d $exldumdir ]]; then
        echo -e "$PROC: The directory $exldumdir does not exist."
        exit_1
      fi
      numfiles=0
      for file in $exldumdir/*.[fh]; do
        cp $file $exldir
        numfiles=1
      done
      if [[ $numfiles -eq 0 ]]; then
        echo -e "$PROC: No source files in directory $exldumdir."
        exit_1
      fi
    done
#
### Load FORTRAN90 compiler name, compile flags and link flags ###
#
    echo -e "\n Loading compile and link information from database file:"
    echo -e "\n ${datafile}"
#
    if [[ -s $datafile ]]; then
      getvar FFLAGS FFLAGS
      iferrstat "getvar FFLAGS"
      getvar LFLAGS LFLAGS
      iferrstat "getvar LFLAGS"
      for library in $LIBS; do
        if [[ $library = -lessl ]]; then
          ESSLDIR=$(find $REFSRC -name essl -print)
        fi
      done
      getvar EXCLUDE EXCLUDE
      if [[ -n $EXCLUDE ]]; then
        echo -e "\n\n Substituted routines:\n"
        for modul in $EXCLUDE; do
          srcfile=$(find $REFSRC -name $modul -print)
          echo -e " ${srcfile}"
          extension=${srcfile##*.}
          Extension=$(echo $extension | tr a-z A-Z)
          if [[ -f $srcfile ]]; then
            mv $srcfile ${srcfile%.$extension}.$Extension
            if [[ -d $ESSLDIR ]]; then
              esslfile=${srcfile##*/}
              esslfile=$ESSLDIR/${esslfile%.$extension}.essl
              if [[ -s $esslfile ]]; then
                cp -p $esslfile $srcfile
              fi
            fi
          fi
        done
      fi
#
###   Get information for external libraries ###
#
      declare -a exlibinam
      nexlibs=0
      getextlib nexlibs exlibinam ELSPEC
#
    else
      echo -e "$PROC: The datafile $datafile does not exist."
      exit_1
    fi
#
### Copy source files for specified external libraries ###
#
    for iel in $(seq 1 $nexlibs); do
#
###   Check if a library corresponding to datafile option exist ###
# 
      exldir=$REFEXL/${exlibinam[$iel]}
      if [[ ! -d $exldir ]]; then
        echo -e "$PROC: The directory $exldir does not exist."
        exit_1
      fi
#
###   Check if a library for active source code exist ###
#
      exlactdir=$exldir/$ELACTNAM
      if [[ ! -d $exlactdir ]]; then
        echo -e "$PROC: The directory $exlactdir does not exist."
        exit_1
      fi
#
###   Copy files with active source code ###
#
      numfiles=0
      for file in $(find $exlactdir -name "*.[fh]" -print); do
        cp $file $exldir
        numfiles=1
      done
#
###   Check if there have been files copied ###
#
      if [[ $numfiles -eq 0 ]]; then
        echo -e "$PROC: No source files in directory $exlactdir."
        exit_1
      fi
    done
#
### Lock the program version ###
#
    touch $REFOBJ/.LOCKFILE
    chmod 644 $REFOBJ/.LOCKFILE
#
    echo -e "\n\n Locking program version $PROG.$VERSION.$EXT.\n"
#
### Create temporary directory for object files ###
#
    TMPOBJ=$REFDIR/object.$EXT.$$
#
    mkdir $TMPOBJ
    iferrstat "mkdir $TMPOBJ"
#
    chmod 755 $TMPOBJ
#
    cp -p $REFOBJ/.LOCKFILE $TMPOBJ
#
### Create a list of all reference include files ###
#
    refinc=$REFDIR/.refincfilelist
#
    echo -e "\n Creating list of all reference include files.\n"
#
    find $REFINC -name '*.h' -print >$refinc
    find $REFEXL -maxdepth 2 -name '*.h' -print >>$refinc
#
### Create a list of all reference source files ###
#
    refsrc=$REFDIR/.refsrcfilelist
#
    echo -e "\n Creating list of all reference source files.\n"
#
    find $REFSRC -name '*.[cf]' -print >$refsrc
    find $REFEXL -maxdepth 2 -name '*.f' -print >>$refsrc
#
### Temporary file with the list of the changed include files ###
#
    tmpinc=$REFDIR/.incfilelist.$$
    >$tmpinc
#
### Temporary file with the list of source files which must be compiled ###
#
    tmpsrc=$REFDIR/.srcfilelist.$$
    >$tmpsrc
#
### Temporary file with a list of files ###
#
    tmplist=$REFDIR/.filelist.$$
    >$tmplist
#
### Check for files with a strange extension ###
#
    if [[ -n $(find $REFINC ! -name "*.[hH]" ! -name "*.8x[48]" -type f -print) ]]; then
      echo -e "\n There are files with a strange extension in $REFINC:\n"
      find $REFINC ! -name "*.[hH]" ! -name "*.8x[48]" -type f -print
    fi
#
    if [[ -n $(find $REFSRC -name "*.[!CFcfessl8x88x4]*" -print) ]]; then
      echo -e "\n There are files with a strange extension in $REFSRC:\n"
      find $REFSRC -name "*.[!CFcfessl8x88x4]*" -print
    fi
#
### Check for multiple source files ###
#
    if [[ $CHECK = true ]]; then
      echo -e "\n Checking for multiple source files.\n\n"
      if [[ -s $refsrc ]]; then
        while read refsrcfile; do
          refmodul=${refsrcfile##*/}
          number=$(find $REFSRC -name $refmodul -print | wc -w)
          if (( $number > 1 )); then
            echo -e "\n\n Error checking source files.\n"
            echo -e " Multiple source file $refmodul.\n"
            echo -e "$(find $REFSRC -name $refmodul -print)\n"
            exit_1
          fi
        done <$refsrc
      fi
    fi
#
### Find platform depending source files ###
#
    rm -f $REFSRC/platform/*.[cf]
#
    if  [[ $machine == 'ppc64' ]]; then
      for refsrcfile in $REFSRC/platform/PPC64/*.[CF]; do
        refmodul=${refsrcfile##*/}
        refmodul=${refmodul%%.*}
        refext=$(echo ${refsrcfile##*.} | tr A-Z a-z)
        cp -p $refsrcfile $REFSRC/platform/$refmodul.$refext
      done
    else
      for refsrcfile in $REFSRC/platform/$ostype/*.[CF]; do
        refmodul=${refsrcfile##*/}
        refmodul=${refmodul%%.*}
        refext=$(echo ${refsrcfile##*.} | tr A-Z a-z)
        cp -p $refsrcfile $REFSRC/platform/$refmodul.$refext
      done
    fi
#
### Copy MPI depending files ###
#
#   if [[ $EXT = "mpi" || $EXT = "dpg" || $EXT = "pro" || $EXT = "ext" ]]; then
    if [[ $EXT =~ ^(mpi|dpg|pro|ext)$ ]]; then
      getvar MPIBIT MPIBIT
      if [[ -n $MPIBIT ]]; then
        MPIBIT=$(echo $MPIBIT | tr A-Z a-z)
      else
        MPIBIT="8x4"
      fi
      MPIDIR="parallel/$MPIBIT"
    else
      MPIDIR="serial"
      MPIBIT="[FH]"
    fi
#
    for refsrcfile in $REFSRC/mpi/system/$MPIDIR/*.$MPIBIT;do
      refmodul=${refsrcfile##*/}
      refmodul=${refmodul%%.*}
      cp -p $refsrcfile $REFSRC/mpi/system/$refmodul.f
    done
#
    ls $REFINC/$MPIDIR/*.$MPIBIT 2>/dev/null 1>&2 && \
    (for refincfile in $REFINC/$MPIDIR/*.$MPIBIT;do
      refmodul=${refincfile##*/}
      refmodul=${refmodul%%.*}
      cp -p $refincfile $REFINC/$MPIDIR/../$refmodul.H
    done)
#
    for refincfile in $REFINC/${MPIDIR%%/*}/*.[H];do
      refmodul=${refincfile##*/}
      refmodul=${refmodul%%.*}
      refext=$(echo ${refincfile##*.} | tr A-Z a-z)
      cp -p $refincfile $REFINC/$refmodul.$refext
    done
#
### Create a list of MPI depending files ###
#
    refmpi=$REFDIR/.refmpifilelist
#
    echo -e "\n Creating list of all MPI depending files.\n"
#
    find $REFINC -name "*.H" -print | grep ${MPIDIR%%/*} >$refmpi
    find $REFSRC -name "*.$MPIBIT" -print | grep $MPIDIR >>$refmpi
#
### Build compilation file list ###
#
    if [[ $FULL_RECOMPILATION = true ]]; then
#
      echo -e "\n Full recompilation."
      find $REFOBJ -name "*.[ho]" -exec rm -f {} \;
      cp $refinc $tmpinc
      cp $refsrc $tmpsrc
      if [[ -s $tmpinc ]]; then
        cat $tmpinc | xargs -i cp {} $REFOBJ
      fi
#
    else
#
### Check include files ###
#
      echo -e "\n Checking include files in $REFINC.\n"
#
### Collect source files containing a changed include file ###
#
      if [[ -s $refinc ]]; then
        while read incfile; do
          incmodul=${incfile##*/}
          objfile=$REFOBJ/$incmodul
          if [[ ! $objfile -ot $incfile ]]; then
            echo -e " $incmodul is unchanged.\n"
            cp $incfile $TMPOBJ
          else
            echo -e " $incmodul was changed.\n"
            echo -e " Adding all reference source files including\c"
            echo -e " $incmodul to compile list.\n"
            echo $incfile >>$tmpinc
            if [[ -s $refsrc ]]; then
              cat $refsrc | xargs grep -il "INCLUDE *'$incmodul'" >>$tmplist
              if [[ -s $tmplist ]]; then
                while read refsrcfile; do
                  refmodul=${refsrcfile##*/}
                  ifprint " $refmodul includes $incmodul.\c"
                  if [[ -z $(grep -F "$refsrcfile" $tmpsrc) ]]; then
                    echo -e " Adding $refmodul to compile list."
                    echo $refsrcfile >>$tmpsrc
                  else
                    ifprint " But $refmodul is already in the compile list."
                  fi
                done <$tmplist
              fi
            fi
          fi
          echo
        done <$refinc
      fi
#
### Check all source files ###
#
      echo -e "\n Checking source files in $REFSRC.\n"
#
      if [[ -s $refsrc ]]; then
        while read refsrcfile; do
          refmodul=${refsrcfile##*/}
          objfile=$REFOBJ/${refmodul%.[cf]}.o
          if [[ ! $objfile -ot $refsrcfile ]]; then
            ifprint " $refmodul is up-to-date. Saving object file."
            mv $objfile $TMPOBJ/${refmodul%.[cf]}.o
          else
            echo -e " $refmodul is NOT up-to-date.\c"
            if [[ -z $(grep -F "$refsrcfile" $tmpsrc) ]]; then
              echo -e " Adding $refmodul to compile list."
              echo $refsrcfile >>$tmpsrc
            else
              echo -e " But $refmodul is already in the compile list."
            fi
          fi
        done <$refsrc
      fi
#
### Substitute the old by the new object file directory ###
#
      if [[ $PWD = $REFOBJ ]]; then
        cd $REFDIR
      fi
#
      rm -rf $REFOBJ
      mv $TMPOBJ $REFOBJ
#
    fi
#
### Compile the source files listed in $tmpsrc ###
#
    if [[ -s $tmpsrc ]]; then
#
      echo -e "\n\n Starting compilation.\n"
#
      echo -e "\n Compile flags: -c $FFLAGS"
#
      echo -e "\n Include directory: $REFINC"
      for exldir in $(find $REFEXL -mindepth 1 -maxdepth 1 -type d -print); do
        if [[ ! -z $(find $exldir -maxdepth 1 -name "*.h" -print -quit) ]]; then
          echo -e "                    $exldir"
          REFEXLINCOPT=$REFEXLINCOPT" -I"$exldir
        fi
      done
      echo -e " "
#
      cd $REFOBJ
#
      wc -l $tmpsrc >$tmplist
      read totnum dummy <$tmplist
      number=0
#
      while read srcfile; do
#
        number=number+1
#
        modul=${srcfile##*/}
#
        echo -e " Compiling $modul ($number of ${totnum})."
#
        getvar $modul MOD_FFLAGS
#
        if (( $? == 0 )); then
          echo -e " Modified compile flags for $modul: -c $MOD_FFLAGS"
          $F90 -c $MOD_FFLAGS$INCSEP-I$REFINC $CPPFLAGS $REFEXLINCOPT $srcfile
        else
          $F90 -c $FFLAGS $ELSPEC$INCSEP-I$REFINC $CPPFLAGS $REFEXLINCOPT $srcfile
        fi
#
        if (( $? != 0 )); then
          echo -e "\n\n Error occured compiling $modul.\n"
          extension=${modul##*.}
          objfile=${modul%.$extension}.o
          rm $REFOBJ/$objfile 2>/dev/null
          echo -e " $objfile removed.\n"
          cd - >/dev/null
          exit_1
        fi
#
      done <$tmpsrc
#
      echo -e "\n $number source files successfully compiled."
#
      cd - >/dev/null
#
    fi
#
### Pseudocompilation of the changed include files ###
#
    if [[ -s $tmpinc ]]; then
      cat $tmpinc | xargs -i cp {} $REFOBJ
    fi
#
### Link the object files ###
#
    echo -e "\n\n Linking object files.\n"
#
    cd $REFOBJ
#
    echo -e " $F90 $LFLAGS $INCSEP-I$REFINC $CPPFLAGS $LDFLAGS -o $REFOBJ/$PROG.$VERSION.$EXT *.o $LIBSCALAPACK_MT $LIBS $ELSPEC\n"
#
    $F90 $LFLAGS $INCSEP-I$REFINC $CPPFLAGS $LDFLAGS -o $REFOBJ/$PROG.$VERSION.$EXT *.o $LIBSCALAPACK_MT $LIBS $ELSPEC
#
    if (( $? != 0 )); then
      cd - >/dev/null
      echo -e "\n\n Error occured linking $PROG.$VERSION.$EXT.\n"
      exit_1
    fi
#
    cd - >/dev/null
#
    echo -e "\n Executable program $REFOBJ/$PROG.$VERSION.$EXT created.\n"
#
### Set permits ###
#
    uid=$(whoami)
    gid=$(groups | cut -d" " -f1)
#
    chown $uid:$gid $ROOTDIR/$PROG
    chmod 755 $ROOTDIR/$PROG
#
    chown $uid:$gid $ROOTDIR/$PROG/.default-version
    chmod 644 $ROOTDIR/$PROG/.default-version
#
    if [[ -s $ROOTDIR/$PROG/INSTALL ]]; then
      chown $uid:$gid $ROOTDIR/$PROG/INSTALL
      chmod 644 $ROOTDIR/$PROG/INSTALL
    fi
#
    if [[ -s $ROOTDIR/$PROG/CREX ]]; then
      chown $uid:$gid $ROOTDIR/$PROG/CREX
      chmod 744 $ROOTDIR/$PROG/CREX
    fi
#
    if [[ -s $ROOTDIR/$PROG/crex ]]; then
      chown $uid:$gid $ROOTDIR/$PROG/crex
      chmod 755 $ROOTDIR/$PROG/crex
    fi
#
    if [[ -s $ROOTDIR/$PROG/q96 ]]; then
      chown $uid:$gid $ROOTDIR/$PROG/q96
      chmod 755 $ROOTDIR/$PROG/q96
    fi
#
    chown -R $uid:$gid $REFDIR
    chmod 755 $REFDIR
#
    find $REFDIR -type d -exec chmod 755 {} \;
    find $REFDIR -type f -exec chmod 644 {} \;
    find $REFDIR -name "$PROG.$VERSION.*" -exec chmod 755 {} \;
#
### Save current include, source and MPI file list ###
#
    mv $refinc $refsrc $refmpi $REFOBJ
#
### Remove temporary files ###
#
    echo -e " \n Unlocking program version $PROG.$VERSION.$EXT.\n"
#
    rm -f $REFOBJ/.LOCKFILE
#
### Memorize the last change of the reference program version ###
#
    touch $REFOBJ/.Changed
    chmod 644 $REFOBJ/.Changed
#
### Remove temporary files ###
#
    clean
#
### End of procedure ###
#
    echo -e "\n Normal termination of $PROC.\n\n"
