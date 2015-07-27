#! /usr/bin/env python2
import os
import sys
import re
import shutil
from glob import glob
from optparse import OptionParser
from datetime import datetime

def recursive_remove(dir):
    dir = '/'.join(dir.split('/')[0:-1])
    if len(os.listdir(dir)) == 0:
        os.rmdir(dir)
        recursive_remove(dir)
    return

def clean_dir(dir):
    for root, dirs, files in os.walk(dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
    
if __name__ == '__main__':

    parser = OptionParser()

    #command line options
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

    parser.add_option("-c", "--commit",
                      action="store",
		      type="string",
                      dest="commit",
                      default=False,
                      help="A URL to a mercurial repo where the binaries will be pushed to.")

    (options, args) = parser.parse_args()

    if not options.path:
        parser.error("You must specify a path \n\nExample: python binaries.py -p \"./FolderName\"")

    #we've been given a mercurial repo (hopefully)...    
    if "https" in options.path or "ssh" in options.path or "http" in options.path:
        options.path = options.path.strip('/')
        
        #extract the username for subsequent clones...
        mercurial_username = re.split('([a-zA-Z0-9]*@)',options.path)[1]
        os.system("hg clone "+options.path)

        #ammend the path as we now have the files locally        
        options.path = "./"+str(options.path.split('/')[-1])

        #look for any embedded libs in the subdir and grab those as well        
        for file in glob(options.path+"/*.lib"):
            with open(file) as f:
                url = f.readlines()[0]
                
                #strip version at the end of the url
                url = re.split('(/#.*\\n)',url)[0] 
                index = url.find("developer")

                #insert our username
                url = url[:index]+mercurial_username+url[index:]

                #begin clone
                os.system("hg clone "+url+" "+options.path+'/'+url.split('/')[-1])

    build_destination = "./build"

    if options.build_destination:
        build_destination = options.build_destination

    #the file extensions to look for    
    file_exts = ["cpp","c","hex","sct","h","s","ar"]

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
        clean_dir(build_destination)
        

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

                    #if the user has specified we ignore it - we don't want to include the header files
                    #we add them to a list so they are removed in the clean up phase
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
                    if ext == "cpp" or ext == "s" or ext == "ar":
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
            print "Command: "+"armcc -c -W --no_strict --cpu Cortex-M0 --apcs=interwork --cpp -O2 -I"+build_destination+"/*.ar -I"+' -I'.join(linker_dirs)+" "+" ".join([build_destination+"/"+compile_file_cpp.split('/')[-1] for compile_file_cpp in compile_files_cpp])+" --gnu --no_rtti -I C:\Keil\ARM\RV31\INC -I C:\Keil\ARM\CMSIS\Include -DTARGET_NRF51822 -DTARGET_M0 -DTARGET_CORTEX_M -DTARGET_NORDIC -DTARGET_NRF51822_MKIT -DTARGET_MCU_NRF51822 -DTARGET_MCU_NORDIC_16K -DTOOLCHAIN_ARM_STD -DTOOLCHAIN_ARM -D__CORTEX_M0 -DARM_MATH_CM0 -DMBED_BUILD_TIMESTAMP=\"1435840731.68\" -D__MBED__=\"1\" -DNRF51 -D__ASSERT_MSG -o \""+build_destination+"/*.o\"" + "\n\n" 

        #compile C source
        if len(compile_files_c) > 0:
            if os.system("armcc -c -W --no_strict --cpu Cortex-M0 --apcs=interwork --c99 -O2 -I"+build_destination+"/*.ar -I"+' -I'.join(linker_dirs)+" "+" ".join([build_destination+"/"+compile_file_c.split('/')[-1] for compile_file_c in compile_files_c])+" --gnu --no_rtti -I C:\Keil\ARM\RV31\INC -I C:\Keil\ARM\CMSIS\Include -DTARGET_NRF51822 -DTARGET_M0 -DTARGET_CORTEX_M -DTARGET_NORDIC -DTARGET_NRF51822_MKIT -DTARGET_MCU_NRF51822 -DTARGET_MCU_NORDIC_16K -DTOOLCHAIN_ARM_STD -DTOOLCHAIN_ARM -D__CORTEX_M0 -DARM_MATH_CM0 -DMBED_BUILD_TIMESTAMP=\"1435840731.68\" -D__MBED__=\"1\" -DNRF51 -D__ASSERT_MSG -o \""+build_destination+"/*.o\"  "):
                print "check output, and try again"
                exit(1)
        
        #compile cpp source
        if os.system("armcc -c -W --no_strict --cpu Cortex-M0 --apcs=interwork --cpp -O2 -I"+build_destination+"/*.ar -I"+' -I'.join(linker_dirs)+" "+" ".join([build_destination+"/"+compile_file_cpp.split('/')[-1] for compile_file_cpp in compile_files_cpp])+" --gnu --no_rtti -I C:\Keil\ARM\RV31\INC -I C:\Keil\ARM\CMSIS\Include -DTARGET_NRF51822 -DTARGET_M0 -DTARGET_CORTEX_M -DTARGET_NORDIC -DTARGET_NRF51822_MKIT -DTARGET_MCU_NRF51822 -DTARGET_MCU_NORDIC_16K -DTOOLCHAIN_ARM_STD -DTOOLCHAIN_ARM -D__CORTEX_M0 -DARM_MATH_CM0 -DMBED_BUILD_TIMESTAMP=\"1435840731.68\" -D__MBED__=\"1\" -DNRF51 -D__ASSERT_MSG -o \""+build_destination+"/*.o\"  "):
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
        
    #move the ar files to the build folder     
    for file in glob("./*.ar"):
        if shutil.move(file,build_destination):
            print "Couldn't move .ar files! Are you an administrator?"
            exit(1)
    
    if options.commit:
        options.commit = options.commit.strip('/')

        repo_dir = './'+options.commit.split('/')[-1]

        clean_dir(repo_dir)

        #clone before commit
        os.system("hg clone "+options.commit)

        copy_path = repo_dir + build_destination.replace('./','/')

        if os.path.exists(copy_path):
            clean_dir(copy_path)
            os.rmdir(copy_path)

        shutil.copytree(build_destination,copy_path)

        #do some hg trickery         
        os.chdir(repo_dir)
        os.system("hg forget *")
        os.system("hg add *")
        os.system("hg commit -m \"Generated binaries at "+str(datetime.now())+"\"")
        os.system("hg push")
            
        
        
