# Python Compiler Infrastructure

The Pytsi -initiative's goal is to provide a C compiler that is easy to set up, understand and maintain.

So far it parses trigraphs, tokenizes and preprocesses. It also has a cool probe that can be imported:

    ~/pytci$ python gcc_probe.py /opt/gcw0-toolchain/usr/bin/mipsel-gcw0-linux-uclibc-gcc
    {
        "includes": [
            "/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/include", 
            "/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/include-fixed", 
            "/opt/gcw0-toolchain/usr/lib/gcc/mipsel-gcw0-linux-uclibc/4.9.1/../../../../mipsel-gcw0-linux-uclibc/include", 
            "/opt/gcw0-toolchain/usr/mipsel-gcw0-linux-uclibc/sysroot/usr/include"
        ], 
        "interpreter": "/lib/ld-uClibc.so.0", 
        "local_includes": [], 
        "search_paths": [
            "/usr/local/lib", 
            "/lib", 
            "/usr/lib"
        ]
    }

I programmed Pytci to run on Python 2.7.10 because [PEP 0492](https://www.python.org/dev/peps/pep-0492/) is one big clusterfuck. The effort to complicate python compiler should be directed towards standardizing greenlets instead.

Attempt was being made to get Pytci preprocess like existing compilers.

## Early benchmark

I compared macroexpansion of `gcc -E` and `python preprocess.py`. on `/usr/include/stdio.h`. Pytci preprocesses it only 25 times slower than `gcc`.

## Correctness

For a bulltest, I preprocessed a header with Pytci and compiled a "hello world" program against it. Lack of errors and messages proposes that there were mostly non-errorneous behavior.

## License

MIT allows full interoperability and code sharing with other really interesting projects.
