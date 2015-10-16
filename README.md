# Python Compiler Infrastructure

The Pytsi -initiative's goal is to provide a C compiler that is easy to set up, understand and maintain.

So far it parses trigraphs and tokenizes. It also has a cool probe that can be imported:

    ~/pytci$ python gcc_probe.py /opt/gcw0-toolchain/usr/bin/mipsel-gcw0-linux-uclibc-gcc
    search paths: ['/usr/local/lib', '/lib', '/usr/lib']
    "..." includes: []
    <...> includes: ['/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/include', '/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/include-fixed', '/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/../../../../mipsel-gcw0-linux-uclibc/include', '/opt/gcw0-toolchain/usr/mipsel-gcw0-linux-uclibc/sysroot/usr/include']
    program interpreter: /lib/ld-uClibc.so.0

I programmed Pytsi to run on Python 2.7.10 because [PEP 0492](https://www.python.org/dev/peps/pep-0492/) is one big clusterfuck. The effort to complicate python compiler should be directed towards standardizing greenlets instead.

## License

MIT allows full interoperability and code sharing with other really interesting projects.
