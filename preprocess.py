import os
import xml.etree.ElementTree as ET

def run_precheck(directory, targetws, glossws):
    # Check if the flextext files are properly formatted
    # targetws - the main writing system
    # glossws - the first writing system for glosses

    # 1. Every <morph> element must have at least children:
    #   a) <item lang="%TARGETWS%" type="cf">
    #   b) <item lang="%GLOSSWS%" type="gls">
    #   c) <item lang="%GLOSSWS%" type="msa">
    #
    #   where %TARGETWS% and %GLOSSWS% are the respective writing systems.
    #
    # 2. These <item> elements should have some text content
    #
    # 3. All <item> children of <word> elements should have text content

    result = dict()
    result["errors"] = False
    result["noflextext"] = True

    with open("flextextcheck.log", "w") as logfile:
        filelist = getFilenames(directory)
        for f in filelist:
            if f.name.lower().endswith(".flextext"):

                result["noflextext"] = False

                tree = ET.parse(f.path)
                root = tree.getroot()

                # Check morphs

                morphXPath = ".//morph"
                morphs = root.findall(morphXPath)

                msaXPath = f'./item[@type="msa"][@lang="{glossws}"]'
                glsXPath = f'./item[@type="gls"][@lang="{glossws}"]'
                cfXPath = f'./item[@type="cf"][@lang="{targetws}"]'

                for m in morphs:
                    glsElems = m.findall(glsXPath)
                    if len(glsElems) == 0:
                        print(f'{f.name}: No item with type="gls" and lang="{glossws}" found, morph guid: {m.get("guid")}', file=logfile)
                        result["errors"] = True
                    for gls in glsElems:
                        if gls.text is not None:
                            continue
                        else:
                            print(f'{f.name}: Item with type="gls" and lang="{glossws}" has no text content, morph guid: {m.get("guid")}', file=logfile)
                            result["errors"] = True

                    msaElems = m.findall(msaXPath)
                    if len(msaElems) == 0:
                        print(f'{f.name}: No item with type="msa" and lang="{glossws}" found, morph guid: {m.get("guid")}', file=logfile)
                        result["errors"] = True
                    for msa in msaElems:
                        if msa.text is not None:
                            continue
                        else:
                            print(f'{f.name}: Item with type="msa" and lang="{glossws}" has no text content, morph guid: {m.get("guid")}', file=logfile)
                            result["errors"] = True

                    cfElems = m.findall(cfXPath)
                    if len(cfElems) == 0:
                        print(f'{f.name}: No item with type="cf" and lang="{targetws}"  found, morph guid: {m.get("guid")}', file=logfile)
                        result["errors"] = True
                    for cf in cfElems:
                        if cf.text is not None:
                            continue
                        else:
                            print(f'{f.name}: Item with type="cf" and lang="{targetws}" has no text content, morph guid: {m.get("guid")}', file=logfile)
                            result["errors"] = True

                # Check words

                wordXPath = ".//word/item"
                words = root.findall(wordXPath)

                for w in words:
                    if w.text is not None:
                        continue
                    else:
                        #print(f'{f.name}: Item with type="{w.get('type')}" has no text content, word guid: {w.get("guid")}', file=logfile)
                        result["errors"] = True

    return result
            
def getFilenames(path):
    for i in os.scandir(path):
        if i.is_dir(follow_symlinks=False):
            yield from getFilenames(i.path)
        elif i.is_file() and i.name.endswith('flextext'):
            yield i
        else:
            continue
