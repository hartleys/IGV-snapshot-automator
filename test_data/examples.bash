#!/bin/bash

#module unload igvSnap
#module load igvSnap/0.1.47

#A basic image using the IGV defaults:

igvSnap \
          --resolutionFactor "1" \
          --wd "640" \
          --region "chr1:714000-714400" \
          --fmt png \
          --viewAsPairs \
          --outDir "./exampleResults/" \
          --outPrefix "exampleTest.basic." \
          "test_alignments.bam"

#The same snapshot, but as a high-resolution, publication-quality png (roughly equivalent 600dpi), and with a region of interest marked:

igvSnap \
          --resolutionFactor "8.3" \
          --wd "1000" \
          --region "chr1:714000-714400" \
          --roi "chr1:714067-714070" \
          --fmt png \
          --viewAsPairs \
          --outDir "./exampleResults/" \
          --outPrefix "exampleTest.600dpi." \
          "test_alignments.bam"

