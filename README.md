# mbed-binary-exporter
Exports any mbed program as a binary

##About
This script navigates through sub directories and compiles each subdirectory into separate .ar files for mbed.org. It also handles the inclusion of header files and the end result is a single folder containing your binaries, and the required headers.

##Executing
To execute a binary build follow these steps:
1. Download your program from mbed.org in zip format. 
2. Unzip and move the folder into the root directory of where you have placed the script
3. Run `binaries.py`, here's an example command:

```
python binaries.py -p ./ProgramFolder -i folder-you-dont-want-to-compile-1,folder-you-dont-want-to-compile-2
```

##Command Line Options

* -v (--verbose) - Verbose output from the script

* -p (--path) - The directory containing the folders to turn into binaries

* -d (--destination) - The destination to place the built files

* -i (--ignore) - A CSV string of folders to ignore during the compilation stage. This does not ommit the folders from the scanning and inclusion of headers.

* -f (--folders) - A CSV string of specific folders to compile **Currently not implemented**

##Future work
* Mercurial integration
* Ensure .s files are included properly in the binaries
