# Preprocessing scripts

These scripts make various adjustments to the input ELAN files in order to

- arrange and rename the ELAN tiers in a way to facilitate ELAN > flextext export (which is done manually from ELAN, can be run on multiple files at once)
- make global replacements of specific transcription symbols, glosses, etc. if needed (esp. for merging with existing lexicon in FLEx)
- (after ELAN > flextext export) extract punctuation in separate \<word\> items

The four scripts work in this sequence:

The first three transform ELAN files (.eaf) into ELAN files. They take as input a folder with ELAN files and save all the results into the output folder. (The filenames do not change, so the folders MUST be different, otherwise the source files would be overwritten.) 
- eaf2eaf-preprocessing-1-tiers.xsl
- eaf2eaf-preprocessing-2-replace.xsl
- eaf2eaf-preprocessing-3-sentences.xsl

At this point, the user should export all the ELAN files into the flextext format (File > Export multiple files as... > Flextext file).

The last script takes as input a folder with flextext files and writes the result into another folder. Similarly, the folder names should be different because the individual file names are the same in the output.
- flex2flex_FE-preprocessing-4-ts_punct.xsl

The replacement script (eaf2eaf_FE-preprocessing-2-replace.xsl) reads lists of replacements to make from xml files (replacements\*.xml).

Note: The version in this folder was used to import the Tundra Enets collection. 
The version in folder v1-ForestEnets used for Forest Enets had more complex replacements. 
