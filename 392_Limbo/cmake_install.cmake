1 # Install script for directory: /tmp/vsc47063/easybuild/build/libcmaesresibots/20180806-fix_flags_native/foss-
      1 2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be5370acf6c/python
      2 
      3 # Set the install prefix
      4 if(NOT DEFINED CMAKE_INSTALL_PREFIX)
      5   set(CMAKE_INSTALL_PREFIX "/scratch/gent/vo/001/gvo00117/easybuild/RHEL8/cascadelake-ampere-ib/software/libcm
      5 aes-resibots/20180806-fix_flags_native-foss-2023a-Limbo-2.1.0")
      6 endif()
      7 string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")
      8 
      9 # Set the install configuration name.
     10 if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
     11   if(BUILD_TYPE)
     12     string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
     13            CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
     14   else()
     15     set(CMAKE_INSTALL_CONFIG_NAME "Release")
     16   endif()
     17   message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
     18 endif()
     19 
     20 # Set the component getting installed.
     21 if(NOT CMAKE_INSTALL_COMPONENT)
     22   if(COMPONENT)
     23     message(STATUS "Install component: \"${COMPONENT}\"")
     24     set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
     25   else()
     26     set(CMAKE_INSTALL_COMPONENT)
     27   endif()
     28 endif()
     29 
     30 # Install shared libraries without execute permission?
     31 if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
     32   set(CMAKE_INSTALL_SO_NO_EXE "0")
     33 endif()
     34 
     35 # Is this installation the result of a crosscompile?
     36 if(NOT DEFINED CMAKE_CROSSCOMPILING)
     37   set(CMAKE_CROSSCOMPILING "FALSE")
     38 endif()
     39 
     40 # Set default install directory permissions.
     41 if(NOT DEFINED CMAKE_OBJDUMP)
     42   set(CMAKE_OBJDUMP "/apps/gent/RHEL8/cascadelake-ib/software/binutils/2.40-GCCcore-12.3.0/bin/objdump")
     43 endif()
     44 
     45 if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
     46   if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/buil     46 d/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be53     46 70acf6c/lib/python3.11/site-packages/lcmaes.so" AND
     47      NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybu     47 ild/build/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd32     47 4c13be5370acf6c/lib/python3.11/site-packages/lcmaes.so")
     48     file(RPATH_CHECK
     49          FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/bu     49 ild/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be     49 5370acf6c/lib/python3.11/site-packages/lcmaes.so"
     50          RPATH "/scratch/gent/vo/001/gvo00117/easybuild/RHEL8/cascadelake-ampere-ib/software/libcmaes-resibots     50 /20180806-fix_flags_native-foss-2023a-Limbo-2.1.0/lib")
     51   endif()
     52   file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/bu     52 ild/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be     52 5370acf6c/lib/python3.11/site-packages" TYPE MODULE FILES "/tmp/vsc47063/easybuild/build/libcmaesresibots/2018     52 0806-fix_flags_native/foss-2023a-Limbo-2.1.0/easybuild_obj/python/lcmaes.so")
     53   if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/buil     53 d/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be53     53 70acf6c/lib/python3.11/site-packages/lcmaes.so" AND
     54      NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybu     54 ild/build/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd32     54 4c13be5370acf6c/lib/python3.11/site-packages/lcmaes.so")
     55     file(RPATH_CHANGE
     56          FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/bu     56 ild/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be     56 5370acf6c/lib/python3.11/site-packages/lcmaes.so"
     57          OLD_RPATH "/tmp/vsc47063/easybuild/build/libcmaesresibots/20180806-fix_flags_native/foss-2023a-Limbo-     57 2.1.0/easybuild_obj/src::::::::::::::::::::::::::::::::::"
     58          NEW_RPATH "/scratch/gent/vo/001/gvo00117/easybuild/RHEL8/cascadelake-ampere-ib/software/libcmaes-resi     58 bots/20180806-fix_flags_native-foss-2023a-Limbo-2.1.0/lib")
     59     if(CMAKE_INSTALL_DO_STRIP)
     60       execute_process(COMMAND "/apps/gent/RHEL8/cascadelake-ib/software/binutils/2.40-GCCcore-12.3.0/bin/strip     60 " "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/../../../../../../../../../../../tmp/vsc47063/easybuild/build/libcmaes     60 resibots/20180806-fix_flags_native/foss-2023a-Limbo-2.1.0/libcmaes-3336d90d4c5c7b6602b9afd324c13be5370acf6c/li     60 b/python3.11/site-packages/lcmaes.so")
     61     endif()
     62   endif()
     63 endif()