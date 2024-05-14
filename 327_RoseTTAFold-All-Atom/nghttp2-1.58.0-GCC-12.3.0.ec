# Author: J. Sassmannshausen (Imperial College London/UK)

easyblock = 'CMakeMake'

name = 'nghttp2'
version = '1.58.0'

homepage = 'https://github.com/nghttp2/nghttp2'
description = """
This is an implementation of the Hypertext Transfer Protocol version 2 in C.

The framing layer of HTTP/2 is implemented as a reusable C library. 
On top of that, we have implemented an HTTP/2 client, server and proxy. 
We have also developed load test and benchmarking tools for HTTP/2.

An HPACK encoder and decoder are available as a public API."""

toolchain = {'name': 'GCC', 'version': '12.3.0'}
toolchainopts = {'pic': True}

github_account = 'nghttp2'
source_urls = [GITHUB_SOURCE]
sources = ['v%(version)s.tar.gz']

builddependencies = [
    ('binutils', '2.40'),
    ('pkgconf', '1.9.5'),
    ('CMake', '3.26.3'),
    #('CUnit', '2.1-3'), #not for 12.3.0
    ('Boost', '1.82.0'),
]

dependencies = [
    ('OpenSSL', '1.1', '', SYSTEM),
    #('nghttp3', '0.6.0'), #not for 12.3.0
    ('Python', '3.11.3'),
    ('libxml2', '2.11.4'),
    #('Jansson', '2.14'), #not for 12.3.0
    #('jemalloc', '5.3.0'), #not for 12.3.0
    #('ngtcp2', '0.7.0'), #not for 12.3.0
    ('libevent', '2.1.12'),
    ('libev', '4.33'),
    ('c-ares', '1.19.1'),
]

runtest = 'check'

sanity_check_paths = {
    'files': ['lib/libnghttp2.%s' % SHLIB_EXT],
    'dirs': ['include/nghttp2', 'share'],
}

moduleclass = 'lib'
