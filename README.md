# mbed-binary-exporter
Exports any mbed program as a binary

##About
This script navigates through sub directories and compiles each subdirectory into separate .ar files for mbed.org. It also handles the inclusion of header files and the end result is a single folder containing your binaries, and the required headers.

###Features
* Mercurial integration
* Generation of .ar files
* Formatting headers relative to the .ar (no time spent rearranging header location)
* Uses armcc, so it is guaranteed to work on the online tool chain.

##Dependencies
Only one, which is that `armcc` is attached to your path variable. 

*P.S. If you are going to use the mercurial integration feature, you will obviously need hg in your path.*

##Executing
To execute a binary build follow these steps:

1. Download your program from mbed.org in zip format. 
2. Unzip and move the folder into the root directory of where you have placed the script
3. Run `binaries.py`, here's an example command:

```
python binaries.py -p ./ProgramFolder -i folder-you-dont-want-to-compile-1,folder-you-dont-want-to-compile-2
```

A mercurial example:

```
python binaries.py -p https://jamesadevine@developer.mbed.org/teams/Microbug/code/MicroBitSB2/ -i test,mbed-slim -c https://developer.mbed.org/users/jamesadevine/code/TestingBinaryMaker/ -v
```


##Command Line Options
* -h (--help) - information about the command line options.

* -v (--verbose) - Verbose output from the script.

* -p (--path) - The directory containing the folders to turn into binaries (or URL to an mbed mercurial repository).

* -d (--destination) - The destination to place the built files.

* -i (--ignore) - A CSV string of folders to ignore during the compilation stage. This does not ommit the folders from the scanning and inclusion of headers.

* -c (--commit) - A URL to a mercurial repo where the binaries will be pushed to after they have been generated.

* -f (--folders) - A CSV string of specific folders to compile **[Currently not implemented]**

