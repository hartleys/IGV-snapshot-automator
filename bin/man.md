reading param: --markdown
## NAME
    igvSnap - Simple wrapper for IGV-snapshot-automator tool (v0.1.0)

## DESCRIPTION
>  ...  
>  ...  
>    
## SYNTAX
    igvSnap [options] bamfile.bam  
      
## OPTIONS
    --help: displays syntax and help info.  
    --man: synonym for --help.  
    --bedFile <filename.bed>: The bedfile to use, listing the desired   
          regions. This can be combined with the --region parameter.  
    --region chr1:10000-20000: Explicitly list a region to plot. Note,   
          the region can optionally be preceded with the region ID using the   
          format: regionID:chr1:1000-2000. This parameter can be set more   
          than once, in which case separate snapshots will be generated for   
          each region.  
    --roi chr1:10000-20000: One or more regions of interest to mark on   
          the track. If this is set more than once, then one region of   
          interest will be assigned to each region parameter, in one to one   
          order.  
    --viewAsPairs: view bam file reads using the viewaspairs mode.  
    --outDir <output/dir/>: The directory to put output images.   
          Defaults to the current directory  
    --outPrefix <fileSuffix>: A suffix to append to each output image   
          filename.  
    --outSuffix <fileSuffix>: A suffix to append to each output image   
          filename.  
    --trackFile <trackFile.bam/bed/vcf/etc>: Additional track files to   
          include.  
    --ht <ht>: The maxHeight param for IGV.  
    --wd <wd>: The width of the output image(s), in pixels. (default   
          1920)  
    --resolutionFactor 1.0: The resolution multiplication factor. This   
          can be used to increase the resolution without shrinking the   
          elements. Roughly 4.17 is equivalent to 300dpi.  
    --onlySnap <batchfile.bat>: Instead of creating a new batch file   
          and running it, just use the supplied headlessIGV batch file.  
    --noSnap: Instead of creating a new batch file and running it, just   
          create the batch file and stop.  
    --additionalInitCommand: Add an additional IGV batch file command   
          to the beginning of the batch file. This can be specified more than   
          once.  
    --fmt png/svg/jpg: The image file format you want. Can be png, svg,   
          or jpg. Default: png.  
    --python path/to/python: The path to the python executable you want   
          to use. Defaults to just 'python'. This is useful if you have both   
          python 2.7 and python 3+ installed.  
    --igvJar path/to/jarfile: The headlessIGV jarfile to use. It is   
          strongly recommended to use the version that comes with this   
          version of igvSnap, as different versions of igvSnap and   
          headlessIGV may not be compatible. Also note that you can NOT use a   
          standard IGV jarfile.  
            
