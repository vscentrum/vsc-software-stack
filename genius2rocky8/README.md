# Migration of Genius to Rocky8

In 2023 the OS of the Genius cluster was updated to Rocky8. For the
convenience of our users, previously installed apps were reinstalled as much
as possible. Especially for the older toolchain generation 2018a this required
a lot of changes to existing easyconfigs (to a lesser extent also for 2019b).
Since the 2018a toolchains were already deprecated at that moment, no effort
was made to get these into the official EasyBuild repository but instead
collected in this subdirectory. Most of these easyconfigs will *not* work on
older operating systems, they have only been tested to some extent on Rocky8.
They are provided without any guarantee about their usability.
