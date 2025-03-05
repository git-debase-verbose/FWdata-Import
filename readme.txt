// repeated from an email to flex-list@googlegroups.com

0. Our use case is this:
We have a large collection of texts glossed in Toolbox, now imported into ELAN.
On the other hand, we have a FLEx project for the same language, initially independent, with other text glossed in a slightly different way. The goal was to merge both in FLEx keeping glosses in both parts but making them follow the current FLEx project consistently.

So in addition to 'just' importing glosses into FLEx, we are also doing some replacements to get the same transcription conventions, glosses, POS labels and speaker codes as we have in the existing FLEx project.
Other users may not have this problem; it will be easier to import everything as is.
However, you do need to have an existing FLEx project before starting with the import. Crucially, you will need to know FLEx codes for all the tiers and writing systems you will be importing.

In our case, we had two glossing lines already in Toolbox, with English and Russian glosses. The importing script is checking if a given morph with the given POS and glosses already exists in the FLEx lexicon.
If you only have one glossing line, it will be simpler (less to check). If you have more than two, the script will need to be adapted to import and check more than two glosses.

1. Preprocessing stage
At this stage, we get from ELAN files to flextext files with all the necessary tier and writing system codes.
We're actually using a series of four XSLT scripts (using XSLT 3.0 with XPath 3.1, which I process with Saxon 9.9 PE via Oxygen; however the free edition of Saxon, SaxonC-HE or SaxonJ-HE, should do perfectly well).
(i) systematic rearrangement and renaming of the ELAN tiers, replacements in speaker codes
(ii) replacements in transcription (tx, mb), POS labels (ps: parts of speech and morphological slots, like "n", "n>v", "n:case"), and glosses (ge, also gr in our case)
(iii) capitalize first word in a sentence, add full stop in the end of a sentence
>> At this moment, the ELAN files are ready for export into flextext. Done in ELAN with "Export multiple files" command.
(iv) tweaking the flextext: extracting punctuation from inside a word into a separate word with type="punct", adding the complete text of a sentence as a phrase/item element

My guess is that most users will not necessarily need (i)-(iii) and just start with export from ELAN. All the tiers and writing systems codes can be specified in the export dialog window, although it can take some clicks.
But (iv) is probably necessary to get punctuation treated the right way.

2. Import stage
The importer script is written in Python (by my colleague Aleksandr Riaposov, not by myself so I won't be so detailed as for the preprocessing step). Any recent version of Python 3 should be ok.
It should be possible to run the XSLT scripts from within Python and thus avoid a separate preprocessing step for the user if starting from (iv), but we haven't yet tried to.

This is also not a single script but a collection of Python scripts. They analyze and modify the *.fwdata file directly.
That is, one must naturally make a backup and close FLEx, then preferably copy the *.fwdata file from the ProgramData/SIL/Fieldworks/Projects folder elsewhere and run the scripts.

First, the scripts analyze the database to make lists of existing objects of all kinds (morphs, wordforms, analyses, texts, speakers, etc.).
Then, they proceed to add new texts to the *.fwdata file.
In every text, every wordform is checked against the existing ones. If there is already a wordform with the same analysis, just a link to the existing object is added. Otherwise, a new wordform is created.
Same for other types of objects, e.g. morphs: each morph is checked against the lexicon. If there exists already a morph with the same form (either main form or alternate form (allomorph)), same part of speech and same glosses, then just a link to it is added. Otherwise, a new lexical entry is created. Homograph numbers are adjusted if necessary, but these should better be reassigned after the import by launching the corresponding utility.
All the newly added objects are appended to the end of the *.fwdata file.

When the scripts are done, the modified *.fwdata should be copied in place of the old one.
Naturally, there is a risk that something will get broken, so you must have a backup to revert to the stage before running the scripts. Until now, we didn't have any serious issues with the modified project file *after* the scripts have completed successfully (i.e. without stopping with an error message). Some built-in FLEx utilities should probably be run to merge duplicate wordforms and analyses and reassign homographs, for instance.