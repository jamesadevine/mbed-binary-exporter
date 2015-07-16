#! /usr/bin/env python2
import os
import sys
import shutil
from glob import glob
from optparse import OptionParser

def recursive_remove(dir):
    dir = '/'.join(dir.split('/')[0:-1])
    #if len(dir.split('/')) == 1:
        #return
    if len(os.listdir(dir)) == 0:
        os.rmdir(dir)
        recursive_remove(dir)
    return
        

if __name__ == '__main__':

    # Parse Options
    parser = OptionParser()

    # Extra libraries
    parser.add_option("-v", "--verbose",
                      action="store_true",
                      dest="verbose",
                      default=False,
                      help="Verbose diagnostic output")
					
    parser.add_option("-p", "--path",
                      action="store",
		      type="string",
                      dest="path",
                      default=False,
                      help="The relative path to the files you want to build")

    parser.add_option("-d", "--destination",
                      action="store",
		      type="string",
                      dest="build_destination",
                      default=False,
                      help="The relative path to the folder where you would like the resulting files to be placed. Defaults to ./build")

    parser.add_option("-i", "--ignore",
                      action="store",
		      type="string",
                      dest="ignore",
                      default=False,
                      help="Ignore specific folders in the target directory. Accepts a csv string of folder names.")
					
    parser.add_option("-f", "--folders",
                      action="store",
		      type="string",
                      dest="folder",
                      default=False,
                      help="Build specific folders in the target directory. Accepts a csv string of folder names.")

    (options, args) = parser.parse_args()

    if not options.path:
        parser.error("You must specify a path \n\nExample: python binaries.py -p \"./FolderName\"")

    build_destination = "./build"

    if options.build_destination:
        build_destination = options.build_destination

    #the file extensions to look for    
    file_exts = ["cpp","c","hex","sct","h","s"]

    #we never want the mercurial folder...
    always_ignore = ['.hg']
    
    ignore_folders = []

    #turn the csv string into a list of folders    
    if options.ignore:

        #combine the lists
        ignore_folders = always_ignore + options.ignore.split(',')
        
        #strip any whitespace
        ignore_folders = [folder.replace(' ','') for folder in ignore_folders]
        
    if options.verbose:
        print "Ignoring folders: " + str(ignore_folders) + "\n\n"

    #get immediate folders    
    sub_folders= next(os.walk(options.path))[1]

    #filter the ignored folders    
    sub_folders = [folder for folder in sub_folders if folder not in ignore_folders]

    if options.verbose:
        print "Generating binary versions of: " + str(sub_folders) + "\n\n"

    header_files = []

    if not os.path.exists(build_destination):
        #make directory if none exists
        os.mkdir(build_destination)
    else:
        #clean the build directory otherwise
        if options.verbose:
            print "Cleaning: " + build_destination + "\n\n"
        
        for root, dirs, files in os.walk(build_destination):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    linker_dirs = []
    header_files = []
    remove_files = []
    
    #get all header file directories    
    for root, folders, files in os.walk(options.path):

        for folder in folders:
                if folder in always_ignore:
                    folders.remove(folder)
        
        for file in files:
            ext = file.split(".")

            #if this file has no extension, skip                
            if(len(ext) < 2):
                continue

            #get only the extension                
            ext = ext[1]

            if(ext in file_exts):
                directory = root.replace('\\','/')
                if ext is "h":
                    header_files.append(directory+"/"+file)
                    temp_dir = build_destination+"/"+'/'.join(directory.split('/')[3:])
                    if  len(list(set(ignore_folders) & set(directory.split('/')))) > 0 and temp_dir+'/'+file not in remove_files:
                        remove_files.append(temp_dir+'/'+file)
 
                    if temp_dir not in linker_dirs:
                        linker_dirs.append(temp_dir)

    if options.verbose:
        print "Finished finding header files\n\n"
        print "Copying header files\n\n"
                        
    #copy the header files
    for header_file in header_files:
        header_dir = build_destination + "/" + '/'.join(header_file.split('/')[3:]).replace(header_file.split('/')[-1],'')
        
        if not os.path.exists(header_dir):
            os.makedirs(header_dir)
        shutil.copy(header_file,header_dir)

    if options.verbose:
        print "Finished copying header files\n\n"

    
    
    #iterate the filtered folders
    for build_folder in sub_folders:

        if options.verbose:
            print "Processing folder: "+build_folder+"\n\n"
        
        compile_files_c = []
        compile_files_cpp = []
        
        for root, folders, files in os.walk(options.path+"/"+build_folder):

            #filter out folders that we never want (mercurial folders)            
            for folder in folders:
                if folder in always_ignore:
                    folders.remove(folder)

            for file in files:
                ext = file.split(".")

                #if this file has no extension, skip                
                if(len(ext) < 2):
                    continue

                #get only the extension                
                ext = ext[1]

                #check if we need to compile it                
                if(ext in file_exts):
                    directory = root.replace('\\','/')
                    if ext == "c":
                        compile_files_c.append(directory.replace("./",'')+"/"+file)
                    if ext == "cpp" or ext == "s":
                        compile_files_cpp.append(directory.replace("./",'')+"/"+file)

        #copy c files ready for compilation to the build folder
        for compile_file_c in compile_files_c:
            shutil.copy(compile_file_c,build_destination)

        #copy cpp files ready for compilation to the build folder
        for compile_file_cpp in compile_files_cpp:
            shutil.copy(compile_file_cpp,build_destination)

        #reverse linker directories 
        linker_dirs = list(reversed(linker_dirs))
        
        if options.verbose:
            print "Compile string C: "+' '.join(compile_files_c) + "\n\n"
            print "Compile string CPP: "+' '.join(compile_files_cpp) + "\n\n"
            print "Include string: -I"+' -I'.join(linker_dirs) + "\n\n"

        #compile C source
        if len(compile_files_c) > 0:
            if os.system("armcc -c -W --no_strict --cpu Cortex-M0 --apcs=interwork --c99 -O2 -I"+' -I'.join(linker_dirs)+" "+" ".join([build_destination+"/"+compile_file_c.split('/')[-1] for compile_file_c in compile_files_c])+" --gnu --no_rtti -I C:\Keil\ARM\RV31\INC -I C:\Keil\ARM\CMSIS\Include -DTARGET_NRF51822 -DTARGET_M0 -DTARGET_CORTEX_M -DTARGET_NORDIC -DTARGET_NRF51822_MKIT -DTARGET_MCU_NRF51822 -DTARGET_MCU_NORDIC_16K -DTOOLCHAIN_ARM_STD -DTOOLCHAIN_ARM -D__CORTEX_M0 -DARM_MATH_CM0 -DMBED_BUILD_TIMESTAMP=\"1435840731.68\" -D__MBED__=\"1\" -DNRF51 -D__ASSERT_MSG -o \""+build_destination+"/*.o\"  "):
                print "check output, and try again"
                exit(1)
        
        #compile cpp source
        if os.system("armcc -c -W --no_strict --cpu Cortex-M0 --apcs=interwork --cpp -O2 -I"+' -I'.join(linker_dirs)+" "+" ".join([build_destination+"/"+compile_file_cpp.split('/')[-1] for compile_file_cpp in compile_files_cpp])+" --gnu --no_rtti -I C:\Keil\ARM\RV31\INC -I C:\Keil\ARM\CMSIS\Include -DTARGET_NRF51822 -DTARGET_M0 -DTARGET_CORTEX_M -DTARGET_NORDIC -DTARGET_NRF51822_MKIT -DTARGET_MCU_NRF51822 -DTARGET_MCU_NORDIC_16K -DTOOLCHAIN_ARM_STD -DTOOLCHAIN_ARM -D__CORTEX_M0 -DARM_MATH_CM0 -DMBED_BUILD_TIMESTAMP=\"1435840731.68\" -D__MBED__=\"1\" -DNRF51 -D__ASSERT_MSG -o \""+build_destination+"/*.o\"  "):
            print "check output, and try again"
            exit(1)

        #merge into an ar
        if os.system("armar --create "+build_folder+".ar *.o"):
            print "armar failed, check output and try again"
            exit(1)

        #remove *.o
        for file in glob("./*.o"):
            if os.remove(file):
                print "Couldn't delete output files! Are you an administrator?"
                exit(1)

    #cleanup
    for file in glob(build_destination+"/*.c") + glob(build_destination+"/*.cpp") + glob(build_destination+"/*.s") + remove_files:
        if os.remove(file):
            print "Couldn't delete src files! Are you an administrator?"
            exit(1)
        recursive_remove(file)

    #move the ar files to the build     
    for file in glob("./*.ar"):
        if shutil.move(file,build_destination):
            print "Couldn't delete src files! Are you an administrator?"
            exit(1)
        
        
