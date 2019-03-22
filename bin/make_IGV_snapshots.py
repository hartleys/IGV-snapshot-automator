#/usr/bin/env python

'''
This script will load IGV in a virtual X window, load all supplied input files
as tracks, and take snapshots at the coorindates listed in the BED formatted
region file.

If you don't have a copy of IGV, get it here:
http://data.broadinstitute.org/igv/projects/downloads/IGV_2.3.81.zip

example IGV batch script:

new
snapshotDirectory IGV_Snapshots
load test_alignments.bam
genome hg19
maxPanelHeight 500
goto chr1:713167-714758
snapshot chr1_713167_714758_h500.png
goto chr1:713500-714900
snapshot chr1_713500_714900_h500.png
exit
'''

# ~~~~ LOAD PACKAGES ~~~~~~ #
import sys
import os
import errno
import subprocess as sp
import argparse

# ~~~~ CUSTOM FUNCTIONS ~~~~~~ #
def my_debugger(vars):
    '''
    starts interactive Python terminal at location in script
    very handy for debugging
    call this function with
    my_debugger(globals().copy())
    anywhere in the body of the script, or
    my_debugger(locals().copy())
    within a script function
    '''
    import readline # optional, will allow Up/Down/History in the console
    import code
    # vars = globals().copy() # in python "global" variables are actually module-level
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

def file_exists(myfile, kill = False):
    '''
    Checks to make sure a file exists, optionally kills the script
    '''
    import os
    import sys
    if not os.path.isfile(myfile):
        print("ERROR: File '{}' does not exist!".format(myfile))
        if kill == True:
            print("Exiting...")
            sys.exit()

def subprocess_cmd(command):
    '''
    Runs a terminal command with stdout piping enabled
    '''
    import subprocess
    process = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    for line in process.stdout:
       print(">     "+str(line));
    
    #for line in iter(process.stdout.readline, ''):
    #    sys.stdout.write(line)
    #for c in iter(lambda: process.stdout.read(1), b:'');
    #   print(">     "+c);
    #proc_stdout = process.communicate()[0].strip()
    #print(proc_stdout)

def make_chrom_region_list_from_regions(regions):
    '''
    Creates a list of tuples representing the regions from the BED file;
    [(chrom, start, stop), ...]
    '''
    region_list = []

    for rr in regions:
        rrs = rr.split(":");
        if(len(rrs) > 2):
           cspan = rrs[2].split("-");
           region_list.append((rrs[0],rrs[1],cspan[0],cspan[1]));
        else:
           cspan = rrs[1].split("-");
           region_list.append((rrs[0],cspan[0],cspan[1]));
    return(region_list)


def make_chrom_region_list(region_file, nf4_mode= False):
    '''
    Creates a list of tuples representing the regions from the BED file;
    [(chrom, start, stop), ...]
    '''
    region_list = []
    with open(region_file) as f:
        for line in f:
            if nf4_mode == True:
                if len(line.split()) >= 4:
                    chrom, start, stop, name = line.split()[0:4]
                    region_list.append((chrom, start, stop, name))
            else:
                if len(line.split()) >= 3:
                    chrom, start, stop = line.split()[0:3]
                    region_list.append((chrom, start, stop))
                elif len(line.split()) == 2:
                    chrom, start = line.split()
                    region_list.append((chrom, start, start))
    return(region_list)

def make_IGV_chrom_loc(region):
    '''
    return a chrom location string in IGV format
    region is a tuple with at least 3 entries
    '''
    chrom, start, stop = region[0:3]
    return('{}:{}-{}'.format(chrom, start, stop))

def make_snapshot_filename(region, height, suffix = None, imgfmt="png"):
    '''
    formats a filename for the IGV snapshot
    region is a tuple with at least 3 entries; if a 4th entry exists, use it as the filename
    '''
    if len(region) >= 4:
        chrom, start, stop, name = region[0:4]
        return('{}'.format(name)) # '{}.png'.format(name) # don't include file extension! user must do this ahead of time!
    elif len(region) == 3:
        chrom, start, stop = region
        if suffix == None:
            return('{}_{}_{}_h{}.{}'.format(chrom, start, stop, height, imgfmt))
        elif suffix != None:
            return('{}_{}_{}_h{}{}.{}'.format(chrom, start, stop, height, str(suffix), imgfmt))

def mkdir_p(path, return_path=False):
    '''
    recursively create a directory and all parent dirs in its path
    '''
    import sys
    import os
    import errno

    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    if return_path:
        return path

def get_open_X_server():
    '''
    Search for an open Xvfb port to render into
    '''
    x_serv_command= '''
for serv_num in $(seq 1 1000); do
    if ! (xdpyinfo -display :${serv_num})&>/dev/null; then
        echo "$serv_num" && break
    fi
done
'''
    import subprocess as sp
    # run the command, capture the output
    process = sp.Popen(x_serv_command,stdout=sp.PIPE, shell=True)
    x_serv_port = int(process.communicate()[0].strip())
    return(x_serv_port)

def initialize_file(string, output_file):
    '''
    Write a string to the file in 'write' mode, overwriting any contents
    '''
    with open(output_file, "w") as myfile:
        myfile.write(string + '\n')

def append_string(string, output_file):
    '''
    Append a string to a file
    '''
    with open(output_file, "a") as myfile:
        myfile.write(string + '\n')

def check_for_bai(bam_file):
    '''
    Check to make sure a 'file.bam.bai' file is present in the same dir as the 'file.bam' file
    '''
    file_exists(bam_file + '.bai', kill = True)

def verify_input_files_list(files_list):
    '''
    Check to make sure input files meet criteria
    Add more criteria as issues are found
    '''
    for file in files_list:
        if file.endswith(".bam"):
            check_for_bai(file)

def start_batchscript(input_files, IGV_batchscript_file, IGV_snapshot_dir, genome_version, image_height, wd = "1920", resolutionFactor = "1.0",additionalInitCommand=[]):
    '''
    Initialize the batchscript file and write setup information to it
    '''
    # ~~~~ WRITE BATCHSCRIPT SETUP INFO ~~~~~~ #
    print("\nWriting IGV batch script to file:\n{}\n".format(IGV_batchscript_file))
    # write the first line to the file; this overwrites the contents!
    initialize_file("new", IGV_batchscript_file)
    # add the genome version
    append_string("genome " + genome_version, IGV_batchscript_file)
    # add the snapshot dir
    append_string("snapshotDirectory " + IGV_snapshot_dir, IGV_batchscript_file)
    append_string("resolutionFactor "+resolutionFactor, IGV_batchscript_file);
    # add all of the input files to load as tracks
    for file in input_files:
        append_string("load " + file, IGV_batchscript_file)
    if additionalInitCommand:
       for aic in additionalInitCommand:
           append_string(aic, IGV_batchscript_file);
    
    # add the track height
    append_string("maxPanelHeight " + image_height, IGV_batchscript_file)
    append_string("panelWidth " + wd, IGV_batchscript_file)

def write_batchscript_regions(region_file, IGV_batchscript_file, image_height, suffix, 
                              nf4_mode, group_by_strand=False,imgfmt="png",regions = [],outPrefix=None,roi=[],viewaspairs=False):
    '''
    Write the batchscript regions
    '''
    # get the snapshot regions from the BED file
    print("\nGetting regions from BED file...\n")
    if region_file:
        print("Parsing regions file: "+str(region_file)+"\n");
        region_list = make_chrom_region_list(region_file, nf4_mode)
        print('Read {} regions'.format(len(region_list)))
        # ~~~~ WRITE BATCHSCRIPT CHROM LOC INFO ~~~~~~ #
        # iterate over all the regions to take snapshots of
        for region in region_list:
            # chrom, start, stop = region
            # convert region into IGV script format
            print("plotting region: "+"-".join(region))
            IGV_loc = make_IGV_chrom_loc(region)
            # create filename for output snapshot image_height
            snapshot_filename = make_snapshot_filename(region, image_height, suffix = suffix,imgfmt=imgfmt)
            # write to the batchscript
            append_string("goto " + IGV_loc, IGV_batchscript_file)
            # if user specifies, group reads by read strand
            if group_by_strand:
                append_string("group strand", IGV_batchscript_file)
            if viewaspairs:
                print("viewaspairs TRUE");
                append_string("viewaspairs true", IGV_batchscript_file)
            else:
                print("viewaspairs FALSE");
            append_string("snapshot " +outPrefix+ snapshot_filename, IGV_batchscript_file)
    else:
       print("no regions bed file\n");
    if regions:
       print("Parsing regions: "+str(regions)+"\n");
       region_list = make_chrom_region_list_from_regions(regions);
       ii = 0;
       # ~~~~ WRITE BATCHSCRIPT CHROM LOC INFO ~~~~~~ #
       # iterate over all the regions to take snapshots of
       for region in region_list:
           # chrom, start, stop = region
           # convert region into IGV script format
           IGV_loc = make_IGV_chrom_loc(region)
           # create filename for output snapshot image_height
           print("plotting region: "+"-".join(region))
           snapshot_filename = make_snapshot_filename(region, image_height, suffix = suffix,imgfmt=imgfmt)
           # write to the batchscript
           append_string("goto " + IGV_loc, IGV_batchscript_file)
           # if user specifies, group reads by read strand
           if group_by_strand:
               append_string("group strand", IGV_batchscript_file)
           if viewaspairs:
               print("viewaspairs TRUE");
               append_string("viewaspairs true", IGV_batchscript_file)
           else:
               print("viewaspairs FALSE");
           if roi:
               rr = roi[ii]
               append_string("region " +rr, IGV_batchscript_file)
           append_string("snapshot " +outPrefix+ snapshot_filename, IGV_batchscript_file)
           ii = ii + 1;
    else:
       print("no regions parameter\n");

def write_IGV_script(input_files, region_file, IGV_batchscript_file, IGV_snapshot_dir, genome_version, 
                     image_height, suffix = None, nf4_mode = False, group_by_strand=False, imgfmt="png",
                     regions = [],outPrefix=None,roi=[],viewaspairs=False,wd="1920",resolutionFactor="1.0",
                     additionalInitCommand=[]):
    '''
    write out a batchscrpt for IGV
    '''
    start_batchscript(input_files, IGV_batchscript_file, IGV_snapshot_dir, genome_version, image_height, wd =wd,resolutionFactor=resolutionFactor,additionalInitCommand=additionalInitCommand)
    print("write_IGV_script: region_file=\""+str(region_file)+"\"");
    write_batchscript_regions(region_file, IGV_batchscript_file, image_height, suffix, 
                              nf4_mode, group_by_strand=group_by_strand,imgfmt=imgfmt,
                              regions=regions,outPrefix=outPrefix,roi=roi,viewaspairs=viewaspairs)
    append_string("exit", IGV_batchscript_file)

def run_IGV_script(igv_script, igv_jar, memMB):
    '''
    Run an IGV batch script
    '''
    print("run_IGV_script...");
    import datetime
    ## print("trying to find open X server...");
    ## # get the X11 Xvfb port number
    ## x_serv_port = get_open_X_server()
    ## print('\nOpen Xvfb port found on:\n{}\n'.format(x_serv_port))
    
    
    # build the system command to run IGV
    # igv_command = "(Xvfb :{} &) && DISPLAY=:{} java -Xmx{}m -jar {} -b {} && killall Xvfb".format(x_serv_port, x_serv_port, memMB, igv_jar, igv_script)
    igv_command = "xvfb-run --auto-servernum --server-num=1 java -Xmx{}m -jar {} -b {}".format(memMB, igv_jar, igv_script)
    print('\nIGV command is:\n{}\n'.format(igv_command))
    # get current time; command can take a while to finish
    startTime = datetime.datetime.now()
    print("\nCurrent time is:\n{}\n".format(startTime))
    # run the IGV command
    print("\nRunning the IGV command...")
    subprocess_cmd(igv_command)
    elapsed_time = datetime.datetime.now() - startTime
    print("\nIGV finished; elapsed time is:\n{}\n".format(elapsed_time))



def main(input_files, region_file = 'regions.bed', genome = 'hg19',
         image_height = '500', outdir = 'IGV_Snapshots',
         igv_jar_bin = "bin/IGV_2.3.81/igv.jar", igv_mem = "4000",
         no_snap = False, suffix = None, nf4_mode = False, onlysnap = False,
         group_by_strand=False,
         imgfmt = "png", regions = None,outPrefix=None,roi=None,viewaspairs=False,wd="1920",
         resolutionFactor="1.0",
         additionalInitCommand = []):
    '''
    Main control function for the script
    '''
    if onlysnap != False:
        print("Onlysnap 1");
        batchscript_file = str(onlysnap)
        file_exists(batchscript_file, kill = True)
        print("Onlysnap 2");
        run_IGV_script(igv_script = batchscript_file, igv_jar = igv_jar_bin, memMB = igv_mem)
        return()
    
    # default IGV batch script output location
    batchscript_file = os.path.join(outdir, outPrefix+"IGV_snapshots.bat")
    
    # make sure the regions file exists
    if region_file:
       file_exists(region_file, kill = True)
    
    # make sure the IGV jar exists
    file_exists(igv_jar_bin, kill = True)
    
    # check the input files to make sure they are valid
    verify_input_files_list(input_files)
    
    print('\n~~~ IGV SNAPSHOT AUTOMATOR ~~~\n')
    print("genome: "+str(genome));
    print('Reference genome:\n{}\n'.format(genome))
    print("test?")
    print('Track height:\n{}\n'.format(image_height))
    print('IGV binary file:\n{}\n'.format(igv_jar_bin))
    print('Output directory will be:\n{}\n'.format(outdir))
    print('Batchscript file will be:\n{}\n'.format(batchscript_file))
    print("viewaspairs = "+str(viewaspairs))
    
    if region_file:
       print('Region file:\n{}\n'.format(region_file))
    else:
       print('no region bed file')
    print('Region list:\n{}\n'.format(regions))
    
    print('Input files to snapshot:\n')
    for file in input_files:
        print(file)
        file_exists(file, kill = True)
    
    # make the output directory
    print('\nMaking the output directory...')
    mkdir_p(outdir)
    
    # write the IGV batch script
    write_IGV_script(input_files = input_files, region_file = region_file,
                     IGV_batchscript_file = batchscript_file,
                     IGV_snapshot_dir = outdir, genome_version = genome,
                     image_height = image_height, suffix = suffix,
                     nf4_mode = nf4_mode, group_by_strand=group_by_strand, 
                     imgfmt=imgfmt, regions=regions,outPrefix=outPrefix,roi=roi,viewaspairs=viewaspairs,wd=wd,
                     resolutionFactor=resolutionFactor,
                     additionalInitCommand=additionalInitCommand)

    # make sure the batch script file exists
    file_exists(batchscript_file, kill = True)
    
    # run the IGV batch script
    if no_snap == False:
        run_IGV_script(igv_script = batchscript_file, igv_jar = igv_jar_bin, memMB = igv_mem)

def run():
    '''
    Parse script args to run the script
    '''
    # ~~~~ Setup ~~~~~~ #
    print("initializing...");
    installBaseDir=os.path.dirname(os.path.realpath(__file__));
    print("installBaseDir="+installBaseDir)
    
    
    # ~~~~ GET SCRIPT ARGS ~~~~~~ #
    parser = argparse.ArgumentParser(description='IGV snapshot automator')
    # required positional args
    parser.add_argument("input_files", nargs='+', help="pathes to the files to create snapshots from e.g. .bam, .bigwig, etc.") # , nargs='?'
    
    # optional flags
    parser.add_argument("--bedFile", default = None, type = str, dest = 'region_file', metavar = 'regions', help="BED file with regions to create snapshots over")
    parser.add_argument("--genome", default = 'hg19', type = str, dest = 'genome', metavar = 'genome', help="Name of the reference genome, Defaults to hg19")
    parser.add_argument("--ht", default = '500', type = str, dest = 'image_height', metavar = 'image height', help="Height for the IGV tracks")
    parser.add_argument("--outDir", default = 'IGV_Snapshots', type = str, dest = 'outdir', metavar = 'output directory', help="Output directory for snapshots")
    parser.add_argument("--igvJar", default = installBaseDir+"/bin/IGV_2.3.81/igv.jar", type = str, dest = 'igv_jar_bin', metavar = 'IGV bin path', help="Path to the IGV jar binary to run")
    parser.add_argument("--mem", default = "4000", type = str, dest = 'igv_mem', metavar = 'IGV memory (MB)', help="Amount of memory to allocate to IGV, in Megabytes (MB)")
    parser.add_argument("--noSnap", default = False, action='store_true', dest = 'no_snap', help="Don't make snapshots, only write batchscript and exit")
    parser.add_argument("--suffix", default = None, dest = 'suffix', help="Filename suffix to place before '.png' in the snapshots")
    parser.add_argument("--nf4", default = False, action='store_true', dest = 'nf4_mode', help="'Name field 4' mode; uses the value in the fourth field of the regions file as the filename for each region snapshot")
    parser.add_argument("--onlySnap", default = False, dest = 'onlysnap', help="Path to batchscript file to run in IGV. Performs no error checking or other input evaluation, only runs IGV on the batchscript and exits.")
    parser.add_argument("--imgFmt", default = "png", dest = 'imgfmt', help="The image format file extension. png, jpg, and svg are allowed.")

    parser.add_argument("--regions",  action='append', type = str, dest = 'regions', help="Explicitly defined regions to be plotted.")
    parser.add_argument("--roi",      action='append', type = str, dest = 'roi', help="...")
    parser.add_argument("--additionalInitCommand",      action='append', type = str, dest = 'additionalInitCommand', help="...")

    parser.add_argument("--outPrefix", default = "", type = str, dest = 'outPrefix', help="Prefix string for all output data...")
    parser.add_argument("--wd", default = "1920", type = str, dest = 'wd', help="...")
    parser.add_argument("--viewAsPairs", default = False, action='store_true', dest = 'viewaspairs', help="...")
    parser.add_argument("--resolutionFactor", default = '1.0', type = str, dest = 'resolutionFactor', metavar = 'resolution expansion factor', help="Resolution expansion factor for snapshot images. Higher values will produce higher resolution images without shrinking the elements.")

    #viewaspairs

    parser.add_argument("--groupByStrand", default=False,
                        dest="group_by_strand", action='store_true',
                        help="Group reads by forward/reverse strand.")

    args = parser.parse_args()
    
    input_files = args.input_files
    region_file = args.region_file
    genome = args.genome
    image_height = args.image_height
    outdir = args.outdir
    igv_jar_bin = args.igv_jar_bin
    igv_mem = args.igv_mem
    no_snap = args.no_snap
    suffix = args.suffix
    nf4_mode = args.nf4_mode
    onlysnap = args.onlysnap
    group_by_strand = args.group_by_strand
    imgfmt = args.imgfmt;
    regions = args.regions;
    outPrefix = args.outPrefix;
    roi = args.roi
    viewaspairs = args.viewaspairs
    wd = args.wd
    resolutionFactor=args.resolutionFactor
    additionalInitCommand=args.additionalInitCommand
    
    print("genome: "+str(genome));
    print("viewaspairs: "+str(viewaspairs));

    main(input_files = input_files, region_file = region_file, genome = genome,
         image_height = image_height, outdir = outdir, igv_jar_bin = igv_jar_bin,
         igv_mem = igv_mem, no_snap = no_snap, suffix = suffix,
         nf4_mode = nf4_mode, onlysnap = onlysnap,
         group_by_strand=group_by_strand,
         imgfmt=imgfmt, regions = regions,outPrefix=outPrefix,roi=roi,viewaspairs=viewaspairs,wd=wd,resolutionFactor=resolutionFactor,
         additionalInitCommand=additionalInitCommand)



if __name__ == "__main__":
    run()