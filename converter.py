from datetime import date, datetime
import xml.etree.ElementTree as ET
import uuid
import re
import os
import json

class Converter:

    def __init__(self, xml, path, target, gloss, gloss2, check_guids=False, main_window=None):
        # Initiates the converter

        self.tlang = target
        self.glang1 = gloss
        self.glang2 = gloss2
        self.check_guids = check_guids
        self.main_window = main_window

        # The slicing is a bit hacky
        # str(datetime.now()) returns the date in the format YYYY-MM-DD HH:MM:SS.mmmmmm
        # FLEx wants the date to be formatted as YYYY-MM-DD HH:MM:SS.mmm
        self.curDate = str(datetime.now())[:-3]

        # Read databases from JSONs
        with open("parsed/PartOfSpeechData.json", encoding='utf-8') as posj:
            self.posData = json.load(posj)

        with open("parsed/WfiData.json", encoding='utf-8') as wfj:
            self.wfiData = json.load(wfj)

        with open("parsed/LexData.json", encoding='utf-8') as lj:
            self.lexData = json.load(lj)

        with open("parsed/MoMorphType.json", encoding='utf-8') as mmtj:
            self.morphTypeData = json.load(mmtj)

        with open("parsed/MoInflAffixSlotData.json", encoding='utf-8') as miasj:
            self.affixSlotData = json.load(miasj)

        with open("parsed/PunctuationFormData.json", encoding='utf-8') as pfj:
            self.punctuationFormData = json.load(pfj)

        with open("parsed/SpeakerData.json", encoding='utf-8') as spj:
            self.speakerData = json.load(spj)

        print(xml)
        fwdata = ET.parse(xml)
        self.FWroot = fwdata.getroot()


        # GUID handling
        # Note: turned off for performance reasons
        if check_guids:
            rtlist = self.FWroot.findall(".//rt")
            self.guidList = list()
            for rt in rtlist:
                self.guidList.append(rt.attrib["guid"])

            rtlist, rt = None, None #cleaning up

        # Check POS tags
        self.posChecker(self, path)

        # Start the conversion
        self.convertFiles(self, path)
        # TODO: still somewhat provisional name for the output
        fwdata.write(f'Converted-{os.path.basename(xml)}', encoding='utf-8', xml_declaration=True)

        print("Done converting!")

    def posChecker(self, path):
        unknownPOS = False
        unknownPOStags = set()

        filelist = self.getFilenames(self, path)
        posTagsFWdata = set()
        posTagsFWdata.add('***') # the common FLEx / Toolbox way to mark unkown POS, no need to add it to the database
        for entry in self.posData:
            posTagsFWdata.add(entry['pos'])

        for f in filelist:
            #print(f'Now checking {f.name}')
            tree = ET.parse(f.path)
            root = tree.getroot()

            allPOStags = root.findall(".//word/morphemes/morph/item[@type='msa']")
            for POS in allPOStags:
                if POS.text is not None:
                    # Check the stem POS only
                    if not re.search(r'^[-=].*|.*[-=]$', POS.text):
                        inflDeriv = re.search(r'^[^:>]+', POS.text)
                        mainPOS = inflDeriv.group(0) if inflDeriv else POS.text
                        if mainPOS.strip('-=') not in posTagsFWdata:
                            unknownPOS = True
                            unknownPOStags.add(mainPOS.strip('-='))

        if unknownPOS:
            self.main_window.pos_not_found_error(str(unknownPOStags))
            #error_message = f'Pars of speech {unknownPOStags} were not found in the database. Add them to the database and try again.'
            raise Exception(f'Pars of speech {str(unknownPOStags)} were not found in the database. Add them to the database and try again.').with_traceback(tracebackobj)


    def createGUID(self):
        if self.check_guids:
            while True:
                guid = str(uuid.uuid4())
                if guid not in self.guidList:
                    self.guidList.append(guid)
                    return guid
        else:
            return str(uuid.uuid4())

    # Check if a wordform exists in the database

    def checkWordform(self, word):
        wordform = word.find("./item").text
        morphemes = word.findall(".//morph")
        morphList = list()
        for m in morphemes:
            morph = m.find("./item[@type='cf']")
            try:
                morph = morph.text.strip("-=")
                glossEnXPath = "./item[@type='gls'][@lang='" + self.glang1 + "']"
                glossEn = m.find(glossEnXPath).text.strip("-=")
                glossRuXPath = "./item[@type='gls'][@lang='" + self.glang2 + "']"
                glossRu = gloss = m.find(glossRuXPath).text.strip("-=")
                morphList.append({ "morph": morph, "glossEn": glossEn, "glossRu": glossRu })
            except:
                # No matches with type='cf' - probably an unknown element
                return None

        wordformFound = False
        for wf in self.wfiData:
            if wf["WfiWordform"] == wordform:
                wordformFound = True
                dictWf = wf["WfiWordform-GUID"]
                if len(morphList) == len(wf["senses"]):
                    formCheck = True
                    for i in range(len(morphList)):
                        if morphList[i]["morph"] == wf["senses"][i]["Morph"]:

                            for lex in self.lexData:
                                for j in range(len(lex["forms"])):
                                    if lex["forms"][j]["Form"] == morphList[i]["morph"]:
                                        morph2checkEn = morphList[i]["glossEn"].strip("[]")
                                        morph2checkRu = morphList[i]["glossRu"].strip("[]")
                                        if morph2checkEn == lex["GlossEn"]:
                                            continue
                                        elif morph2checkRu == lex["GlossRu"]:
                                            continue
                                        else:
                                            formCheck = False
                        else:
                            formCheck = False

                    if formCheck:
                        return True, wf["WfiAnalysis-GUID"]

        if wordformFound:
            return False, dictWf
        else:
            return None

    # Check if a gloss-wordform pair exists in the database

    def checkGloss(self, gloss, morphform):
        for lex in self.lexData:
            lex2check = lex["GlossEn"].strip("[]")
            if lex2check == gloss:
                for i in range(len(lex["forms"])):
                    if lex["forms"][i]["Form"] == morphform:
                        return lex["forms"][i]["Form-GUID"], lex["MorphoSyntaxAnalysis-GUID"], lex["LexSense-GUID"]
            elif lex["GlossRu"] == gloss:
                for i in range(len(lex["forms"])):
                    if lex["forms"][i]["Form"] == morphform:
                        return lex["forms"][i]["Form-GUID"], lex["MorphoSyntaxAnalysis-GUID"], lex["LexSense-GUID"]

        return None

    # Check if an allomorph slot exists in the database

    def checkSlot(self, tag, pos):
        if ":" in tag:
            tag = tag.split(":")[1]
            tag = tag.strip("()") # ignore round brackets for cases such as v:(mrph)
        for mslot in self.affixSlotData:
            if mslot["slot"] == tag:
                if pos == mslot["posid"]:
                    return mslot["id"]

        return None

    # Create an affix slot entry

    def makeAffixSlot(self, value, guid, pos):
        if ":" in value:
            value = value.split(":")[1]
            value = value.strip("()") # ignore round brackets for cases such as v:(mrph)

        affixSlotRt = ET.Element("rt", attrib={"class": "MoInflAffixSlot", "guid": guid, "ownerguid": pos})

        slotName = ET.SubElement(affixSlotRt, "Name")
        slotNameAuni = ET.SubElement(slotName, "AUni", attrib={"ws": self.glang1})
        slotNameAuni.text = value

        # Always non-optional
        optional = ET.SubElement(affixSlotRt, "Optional", attrib={"val": "False"})

        self.affixSlotData.append({'slot': value, 'id': guid, 'posid': pos})
        self.FWroot.append(affixSlotRt)

        # Now add the new slot to the corresponding PartOfSpeech

        posElement = self.FWroot.find(f'.//rt[@guid="{pos}"]')
        affixSlots = posElement.find("./AffixSlots")
        if not affixSlots:
            affixSlots = ET.SubElement(posElement, "AffixSlots")
        ET.SubElement(affixSlots, "objsur", attrib={"guid": guid, "t": "o"})

    # Create a lexicon entry (alongside morph, morphoSyntaxAnalysis and sense entries)

    def makeLexEntry(self, word, guid, morph, msa, sense, pos, analysisguid):
        lexEntryRt = ET.Element("rt", attrib={"class": "LexEntry", "guid": guid})

        dateCreated = ET.SubElement(lexEntryRt, "DateCreated", attrib={"val": self.curDate})
        dateModified = ET.SubElement(lexEntryRt, "DateModified", attrib={"val": self.curDate})
        parsing = ET.SubElement(lexEntryRt, "DoNotUseForParsing", attrib={"val": "False"})

        # Count homographs
        wfiGlossGuid = None
        homoCounter = 0
        lastHomoGuid = None
        for lex in self.lexData:
            for i in range(len(lex["forms"])):
                if lex["forms"][i]["Form"] == word.find("./item[@type='cf']").text.strip("-="): 
                    homoCounter = homoCounter + 1
                    lastHomoGuid = lex["LexEntry-GUID"]
        if homoCounter > 0:
            if homoCounter == 1:
                # Change the HomographNumber from 0 to 1 in the data
                lastHomoXPath = "./rt[@guid='" + lastHomoGuid + "']/HomographNumber"
                lastHomoLexeme = self.FWroot.find(lastHomoXPath)
                if lastHomoLexeme.get("val") == "0":
                    lastHomoLexeme.set("val", "1")
                else:
                    print(lastHomoLexeme.get("val"))
                    print(word.find("./item[@type='cf']").text)
                    print("There might be an error with the homograph counter")

            homographNumber = ET.SubElement(lexEntryRt, "HomographNumber", attrib={"val": str(homoCounter + 1)})
        else:
            homographNumber = ET.SubElement(lexEntryRt, "HomographNumber", attrib={"val": str(0)})

        lexemeForm = ET.SubElement(lexEntryRt, "LexemeForm")
        lexemeSur = ET.SubElement(lexemeForm, "objsur", attrib={"guid": morph, "t": "o"})

        MSAs = ET.SubElement(lexEntryRt, "MorphoSyntaxAnalyses")
        lexemeSur = ET.SubElement(MSAs, "objsur", attrib={"guid": msa, "t": "o"})

        senses = ET.SubElement(lexEntryRt, "Senses")
        lexemeSur = ET.SubElement(senses, "objsur", attrib={"guid": sense, "t": "o"})

        self.FWroot.append(lexEntryRt)

        # Make a LexSense element

        lexSenseRt = ET.Element("rt", attrib={"class": "LexSense", "guid": sense, "ownerguid": guid})

        gloss = ET.SubElement(lexSenseRt, "Gloss")
        aUniEn = ET.SubElement(gloss, "AUni", attrib={"ws": self.glang1})
        aUniEnXPath = "./item[@type='gls'][@lang='" + self.glang1 + "']"
        aUniEn.text = word.find(aUniEnXPath).text.strip("-=")
        
        aUniRuXPath = "./item[@type='gls'][@lang='" + self.glang2 + "']"
        if word.find(aUniRuXPath) is not None:
            aUniRu = ET.SubElement(gloss, "AUni", attrib={"ws": self.glang2})
            aUniRu.text = word.find(aUniRuXPath).text.strip("-=")

        MSA = ET.SubElement(lexSenseRt, "MorphoSyntaxAnalysis")
        lexemeSur = ET.SubElement(MSA, "objsur", attrib={"guid": msa, "t": "r"})

        self.FWroot.append(lexSenseRt)

        # Check if it's a stem or an affix
        # Affixes start with hyphens (-)
        # Stems do not
        # TODO: that approach covers suffixes, but not prefixes and infixes
        txtCheckXPath = "./item[@type='cf'][@lang='" + self.tlang + "']"
        txtCheck = word.find(txtCheckXPath).text

        if not txtCheck.startswith("-") and not txtCheck.endswith("-"):
            # Then it's a stem
            morphType = "stem"

            # MoStemMsa

            moStemMsaRt = ET.Element("rt", attrib={"class": "MoStemMsa", "guid": msa, "ownerguid": guid})

            if pos:
                partOfSpeech = ET.SubElement(moStemMsaRt, "PartOfSpeech")
                posSur = ET.SubElement(partOfSpeech, "objsur", attrib={"guid": pos, "t": "r"})

            self.FWroot.append(moStemMsaRt)

            # MoStemAllomoprh

            moStemAllomorphRt = ET.Element("rt", attrib={"class": "MoStemAllomorph", "guid": morph, "ownerguid": guid})

            alloStem = ET.SubElement(moStemAllomorphRt, "Form")
            alloUniEn = ET.SubElement(alloStem, "AUni", attrib={"ws": self.tlang})
            alloUniEn.text = word.find("./item[@type='cf']").text

            isAbstract = ET.SubElement(moStemAllomorphRt, "IsAbstract", attrib={"val": "False"})

            morphTypeEl = ET.SubElement(moStemAllomorphRt, "MorphType")
            for mt in self.morphTypeData:
                if mt["abbr"] == morphType:
                    morphTypeGuid = mt["id"]
            if "morphTypeGuid" not in locals():
                print(word.find("./item[@type='cf']").text)
            morphTypeSur = ET.SubElement(morphTypeEl, "objsur", attrib={"guid": morphTypeGuid, "t": "r"})

            #DEBUG
            self.FWroot.append(moStemAllomorphRt)

        else:
            # Only infixes, suffixes and prefixes are supported
            if txtCheck.startswith("-") and txtCheck.endswith("-"):
                morphType = "infix"
            elif txtCheck.startswith("-"):
                morphType = "suffix"
            elif txtCheck.endswith("-"):
                morphType = "prefix"

            # MoAffixAllomorph

            moAffixAllomorphRt = ET.Element("rt", attrib={"class": "MoAffixAllomorph", "guid": morph, "ownerguid": guid})

            alloAffix = ET.SubElement(moAffixAllomorphRt, "Form")
            alloUniEn = ET.SubElement(alloAffix, "AUni", attrib={"ws": self.tlang})
            alloUniEn.text = word.find("./item[@type='cf']").text.strip("-=")

            isAbstract = ET.SubElement(moAffixAllomorphRt, "IsAbstract", attrib={"val": "False"})

            morphTypeEl = ET.SubElement(moAffixAllomorphRt, "MorphType")
            for mt in self.morphTypeData:
                if mt["abbr"] == morphType:
                    morphTypeGuid = mt["id"]
            morphTypeSur = ET.SubElement(morphTypeEl, "objsur", attrib={"guid": morphTypeGuid, "t": "r"})

            self.FWroot.append(moAffixAllomorphRt)

            # MoInflAffixMsa

            affMsa = word.find("./item[@type='msa']").text.strip("-=")

            if ">" in affMsa:
                # Then it's a derivational affix

                affs = affMsa.split(">")
                
                fromPosNotFound, toPosNotFound = False, False

                for i in self.posData:
                    if i["pos"] == affs[0]:
                        fromGuid = i["id"]
                        fromPosNotFound = True
                    if i["pos"] == affs[1]:
                        toGuid = i["id"]
                        toPosNotFound = True
                        
                if fromPosNotFound:
                    self.main_window.pos_not_found_error(affs[0])
                    print(f'{affs[0]} is not found in the database. Add it to the database and try again.')
                    
                if toPosNotFound:
                    self.main_window.pos_not_found_error(affs[1])
                    print(f'{affs[1]} is not found in the database. Add it to the database and try again.')

                moDerivAfflMsaRt = ET.Element("rt", attrib={"class": "MoDerivAffMsa", "guid": msa, "ownerguid": guid})

                fromPartOfSpeech = ET.SubElement(moDerivAfflMsaRt, "FromPartOfSpeech")
                fromPOSsur = ET.SubElement(fromPartOfSpeech, "objsur", attrib={"guid": fromGuid, "t": "r"})

                toPartOfSpeech = ET.SubElement(moDerivAfflMsaRt, "ToPartOfSpeech")
                toPOSsur = ET.SubElement(toPartOfSpeech, "objsur", attrib={"guid": toGuid, "t": "r"})

                self.FWroot.append(moDerivAfflMsaRt)

            else:
                # No '>' sign - then it's an inflectional affix

                moInflAffixMsaRt = ET.Element("rt", attrib={"class": "MoInflAffMsa", "guid": msa, "ownerguid": guid})

                if pos:
                    partOfSpeech = ET.SubElement(moInflAffixMsaRt, "PartOfSpeech")
                    posSur = ET.SubElement(partOfSpeech, "objsur", attrib={"guid": pos, "t": "r"})

                    # Checking if a morpheme slot exists
                    slotValue = word.find("./item[@type='msa']").text.strip("-=")
                    slotExists = self.checkSlot(self, slotValue, pos)

                    if slotExists:
                        slotGuid = slotExists
                    else:
                        slotGuid = self.createGUID(self)

                        # Call MakeAffixSlot
                        self.makeAffixSlot(self, slotValue, slotGuid, pos)

                    affixSlots = ET.SubElement(moInflAffixMsaRt, "Slots")
                    slotSur = ET.SubElement(affixSlots, "objsur", attrib={"guid": slotGuid, "t": "r"})

                self.FWroot.append(moInflAffixMsaRt)

        if "aUniRu" in locals().keys():
            self.lexData.append({'LexEntry-GUID': guid, 'GlossEn': aUniEn.text, 'GlossRu': aUniRu.text,'LexSense-GUID': sense, 'MorphoSyntaxAnalysis-GUID': msa, 'forms': [{'Form': alloUniEn.text, 'Form-GUID': morph}]})
        else:
            self.lexData.append({'LexEntry-GUID': guid, 'GlossEn': aUniEn.text, 'GlossRu': '', 'LexSense-GUID': sense, 'MorphoSyntaxAnalysis-GUID': msa, 'forms': [{'Form': alloUniEn.text, 'Form-GUID': morph}]})
 
        return wfiGlossGuid # Returns None if there are no homographs

    # Create a morpheme bundle

    def makeMorphBundle(self, guid, ownerguid, bundle, pos):
        wfiMorphBundleRt = ET.Element("rt", attrib={"class": "WfiMorphBundle", "guid": guid, "ownerguid": ownerguid})

        form = ET.SubElement(wfiMorphBundleRt, "Form")
        astr = ET.SubElement(form, "AStr")
        morphString = ET.SubElement(astr, "Run", attrib={"ws": self.tlang})
        try:
            morphString.text = bundle.find("./item[@type='cf']").text.strip("-=")
        except:
            pass

        try:
            morphGlossEnXPath = "./item[@type='gls'][@lang='" + self.glang1 + "']"
            morphGlossEn = bundle.find(morphGlossEnXPath).text.strip("-=")
        except:
            print("WARNING: No " + self.glang1 + " gloss found")
            print(ET.tostring(bundle))
            morphGlossEn = "%%"

        try:
            morphGlossRuXPath = "./item[@type='gls'][@lang='" + self.glang2 + "']"
            morphGlossRu = bundle.find(morphGlossRuXPath).text.strip("-=")
        except:
            print("WARNING: No " + self.glang2 + " gloss found")
            print(ET.tostring(bundle))
            morphGlossRu = "%%"

        # Checking if a gloss already exists
        glossExists = self.checkGloss(self, morphGlossEn, morphString.text)
        if not glossExists:
            glossExists = self.checkGloss(self, morphGlossRu, morphString.text)

        derivPos = None

        if glossExists:
            morphGuid = glossExists[0]
            msaGuid = glossExists[1]
            senseGuid = glossExists[2]
            wfiGlossGuid = None

            derivAffiXPath = "./rt[@guid='" + msaGuid + "']"
            msaItem = self.FWroot.find(derivAffiXPath)
            if msaItem.get("class") == "MoDerivAffMsa":
                try:
                    derivPos = msaItem.find("./ToPartOfSpeech/objsur").get("guid")
                except:
                    # No ToPartOfSpeech in msaItem
                    pass
        else:
            morphGuid = self.createGUID(self)
            msaGuid = self.createGUID(self)
            senseGuid = self.createGUID(self)
            lexEntryGuid = self.createGUID(self)

            # Calling makeLexEntry
            wfiGlossGuid = self.makeLexEntry(self, bundle, lexEntryGuid, morphGuid, msaGuid, senseGuid, pos, ownerguid)

        morph = ET.SubElement(wfiMorphBundleRt, "Morph")
        morphSur = ET.SubElement(morph, "objsur", attrib={"guid": morphGuid, "t": "r"})

        msa = ET.SubElement(wfiMorphBundleRt, "Msa")
        msaSur = ET.SubElement(msa, "objsur", attrib={"guid": msaGuid, "t": "r"})

        sense = ET.SubElement(wfiMorphBundleRt, "Sense")
        senseSur = ET.SubElement(sense, "objsur", attrib={"guid": senseGuid, "t": "r"})

        self.FWroot.append(wfiMorphBundleRt)

        return senseGuid, wfiGlossGuid, derivPos

    # Create an analysis (= a word)

    def makeAnalysis(self, guid, wordformguid, word, wordformExists = False):
        #TODO: add a condition for when the wordform exists, but has different meanings (edit fwdata)

        if not wordformExists:

            # First make a WfiWordform
            wfiWordformRt = ET.Element("rt", attrib={"class": "WfiWordform", "guid": wordformguid})

            wfAnalyses = ET.SubElement(wfiWordformRt, "Analyses")
            analysesSur = ET.SubElement(wfAnalyses, "objsur", attrib={"guid": guid, "t": "o"})

            # Not sure what the cheksum value should be, but it works with 0 all the same
            checksum = ET.SubElement(wfiWordformRt, "Checksum", attrib={"val": "0"})

            wfForm = ET.SubElement(wfiWordformRt, "Form")
            wfFormAuni = ET.SubElement(wfForm, "AUni", attrib={"ws": self.tlang})
            wfFormAuni.text = word.find("./item").text

            spelling = ET.SubElement(wfiWordformRt, "SpellingStatus", attrib={"val": "0"})

            self.FWroot.append(wfiWordformRt)

        # And then an analysis

        wfiAnalysisRt = ET.Element("rt", attrib={"class": "WfiAnalysis", "guid": guid, "ownerguid": wordformguid})

        category = ET.SubElement(wfiAnalysisRt, "Category")

        catValue = None # Default case for when there is no msa

        # How to determine part of speech of a word?
        # 1. Find a stem morph - i.e., the one without hypnens at either end
        # 2. Use the PoS value of that morph (type='msa' in flextext)
        # 3. If there are several stem morphs, take the first one (TODO? what if there are alternatives?)
        # 4. If there are no stem morphs, treat the first on as a stem (TODO? check for this in flextext?)
        #
        # NB: Important for the correct display of inflectional affixes

        noStemMorphs = True
        msaValues = word.findall(".//morphemes/morph/item[@type='msa']")
        if len(msaValues) > 0:
            for mv in range(len(msaValues)):
                if msaValues[mv].text is not None:
                    if re.search(r'^[-=].*|.*[-=]$', msaValues[mv].text):
                        continue
                    else:
                        catValue = msaValues[mv].text
                        noStemMorphs = False
                        break
            if noStemMorphs:
                catValue = msaValues[0].text.strip("-=")

        catGuid = None # Handling unknown POSs
        for i in self.posData:
            if i["pos"] == catValue:
                catGuid = i["id"]
        if catGuid:
            surPOS = ET.SubElement(category, "objsur", attrib={"guid": catGuid, "t": "r"})
        else:
            print(f'{catValue} not found in the .fwdata!')

        evaluation = ET.SubElement(wfiAnalysisRt, "Evaluations")
        # TODO un-hardcode guids for evaluations
        # Even if they don't seeem to matter much
        surEval = ET.SubElement(evaluation, "objsur", attrib={"guid": "fe84db44-36f3-4d77-b7bd-4b0f5e6200f1", "t": "r"})
        surEval = ET.SubElement(evaluation, "objsur", attrib={"guid": "8caa11bb-cac4-4836-a081-1666245106b9", "t": "r"})

        morphBundles = ET.SubElement(wfiAnalysisRt, "MorphBundles")
        listBundles = word.findall(".//morphemes/morph")
        senses4WfiData = list()
        for bundle in listBundles:
            # The hyphen in hyphenated words ("cross-examine") might be recognized as a morpheme on its own
            # This is undesirable, therefore, such morphemes are ignored
            bundleText = bundle.find("./item[@type='cf']").text
            if bundleText is not None:
                if bundleText == "-":
                    continue

            bundleGuid = self.createGUID(self)
            surMorph = ET.SubElement(morphBundles, "objsur", attrib={"guid": bundleGuid, "t": "o"})

            # Calling makeMorphBundle
            mmb = self.makeMorphBundle(self, bundleGuid, guid, bundle, catGuid) #returns senseGuid
            senses4WfiData.append({'Morph-GUID': bundleGuid, 'Morph': bundle.find("./item[@type='cf']").text.strip("-="), 'Sense-GUID': mmb[0]})

            if mmb[1]:
                meanings = ET.SubElement(wfiAnalysisRt, "Meanings")
                meaningsSur = ET.SubElement(meanings, "objsur", attrib={"guid": mmb[1], "t": "o"})

            if mmb[2]:
                if catGuid:
                    surPOS.set("guid", mmb[2])

        self.FWroot.append(wfiAnalysisRt)

        if wordformExists:
            # Add a new analysis to an existing wordform
            wfAnXPath = "./rt[@guid='" + wordformguid + "']/Analyses"
            wfAn = self.FWroot.find(wfAnXPath)
            newAn = ET.SubElement(wfAn, "objsur", attrib={"guid": guid, "t": "o"})

        wordformText = word.find("./item").text

        self.wfiData.append({'WfiWordform-GUID': wordformguid, 'WfiWordform': wordformText, 'WfiAnalysis-GUID': guid, 'Category-GUID': catGuid, 'senses': senses4WfiData})

    # Check if a punctuation mark exists in the DB, return its ID or None if nothing matches
    def checkPunctuation(self, value):
        for pitem in self.punctuationFormData:
            if pitem["value"] == value:
                return pitem["id"]

        return None

    # Create a new PunctuationForm
    def makePunctuationForm(self, value, guid, lang):
        punctFormRt = ET.Element("rt", attrib={"class": "PunctuationForm", "guid": guid})

        PFForm = ET.SubElement(punctFormRt, "Form")
        PFStr = ET.SubElement(PFForm, "Str")
        PFRun = ET.SubElement(PFStr, "Run", attrib={"ws": lang})
        PFRun.text = value

        self.FWroot.append(punctFormRt)

        self.punctuationFormData.append({"id": guid, "value": value})

    # Check if a speaker exists in the DB, return (its ID, its ownerguid) or (None, ownerguid) if nothing matches
    # Ownerguid refers to CmPossibilityList listing people, and is supposed to be unique for all speakers
    def checkSpeaker(self, tag):
        cmPossibilityId = ""
        for sp in self.speakerData:
            cmPossibilityId = sp["cmPossibilityId"]
            if sp["tag"] == tag:
                return (sp["id"], sp["cmPossibilityId"])

        return (None, cmPossibilityId)

    # Create a new CmPerson (= a speaker)
    def addNewSpeaker(self, tag, guid, ownerguid):
        cmPersonRt = ET.Element("rt", attrib={"class": "CmPerson", "guid": guid, "ownerguid": ownerguid})

        backColor = ET.SubElement(cmPersonRt, "BackColor", attrib={"val": "0"})
        dateCreated = ET.SubElement(cmPersonRt, "DateCreated", attrib={"val": self.curDate})
        dateModified = ET.SubElement(cmPersonRt, "DateModified", attrib={"val": self.curDate})
        dateOfBirth = ET.SubElement(cmPersonRt, "DateOfBirth", attrib={"val": "0"})
        dateOfDeath = ET.SubElement(cmPersonRt, "DateOfDeath", attrib={"val": "0"})
        foreColor = ET.SubElement(cmPersonRt, "ForeColor", attrib={"val": "0"})
        gender = ET.SubElement(cmPersonRt, "Gender", attrib={"val": "0"})
        hidden = ET.SubElement(cmPersonRt, "Hidden", attrib={"val": "False"})
        isProtected = ET.SubElement(cmPersonRt, "IsProtected", attrib={"val": "False"})
        isResearcher = ET.SubElement(cmPersonRt, "IsResearcher", attrib={"val": "False"})

        name = ET.SubElement(cmPersonRt, "Name")
        AUniName = ET.SubElement(name, "AUni", attrib={"ws": self.glang1})
        AUniName.text = tag

        sortSpec = ET.SubElement(cmPersonRt, "SortSpec", attrib={"val": "0"})
        underColor = ET.SubElement(cmPersonRt, "UnderColor", attrib={"val": "0"})
        underStyle = ET.SubElement(cmPersonRt, "UnderStyle", attrib={"val": "0"})

        # Now edit CmPossibilityList

        cmPossibilityList = self.FWroot.findall(".//rt[@guid='" + ownerguid + "']")
        if len(cmPossibilityList) == 1:
            possibilities = cmPossibilityList[0].findall(".//Possibilities")[0]
            ET.SubElement(possibilities, "objsur", attrib={"guid": guid, "t": "o"})
        else:
            print("The list of people not found in fwdata")

        self.FWroot.append(cmPersonRt)

        self.speakerData.append({"tag": tag, "id": guid, "cmPossibilityId": ownerguid})

    # Create an instance of Segment (= a sentence)

    def makeSegment(self, guid, ownerguid, phrase, mediaguid=None):
        segmentRt = ET.Element("rt", attrib={"class": "Segment", "guid": guid, "ownerguid": ownerguid})

        analyses = ET.SubElement(segmentRt, "Analyses")
        listWords = phrase.findall(".//words/word")

        for word in listWords:
            # Check if it's a punctuation mark
            try:
                pform = word.find("./item[@type='punct']").text

                pfCheck = self.checkPunctuation(self, pform)
                if pfCheck:
                    # Found a punctuation mark in the dictionary
                    surWord = ET.SubElement(analyses, "objsur", attrib={"guid": pfCheck, "t": "r"})

                else:
                    # Create a new PunctuationForm
                    punctFormGuid = self.createGUID(self)
                    punctLang = word.find("./item[@type='punct']").get("lang")
                    self.makePunctuationForm(self, pform, punctFormGuid, punctLang)
                    surWord = ET.SubElement(analyses, "objsur", attrib={"guid": punctFormGuid, "t": "r"})

            except:
                # Check if an analysis for the wordform already exists
                analysisCheck = self.checkWordform(self, word)

                if analysisCheck:
                    if analysisCheck[0]:
                        # Found the full analysis
                        wordGuid = analysisCheck[1]
                        surWord = ET.SubElement(analyses, "objsur", attrib={"guid": wordGuid, "t": "r"})
                    else:
                        #TODO: Check this block and the next one: is the link to word or wordform correct?
                        wordGuid = self.createGUID(self)
                        wordformGuid = analysisCheck[1]
                        # Calling makeAnalysis with a parameter that excludes WfiWordform generation
                        self.makeAnalysis(self, wordGuid, wordformGuid, word, wordformExists = True)

                        surWord = ET.SubElement(analyses, "objsur", attrib={"guid": wordGuid, "t": "r"})
                else:
                    # No such wordform found
                    wordGuid = self.createGUID(self)
                    wordformGuid = self.createGUID(self)

                    # Calling makeAnalysis if no existing analysis found
                    self.makeAnalysis(self,wordGuid, wordformGuid, word)

                    surWord = ET.SubElement(analyses, "objsur", attrib={"guid": wordGuid, "t": "r"})

        beginOffset = ET.SubElement(segmentRt, "BeginOffset", attrib={"val": "0"})
        beginTimeOffset = ET.SubElement(segmentRt, "BeginTimeOffset")
        beginTime = ET.SubElement(beginTimeOffset, "Uni")
        beginTime.text = phrase.get("begin-time-offset")

        endTimeOffset = ET.SubElement(segmentRt, "EndTimeOffset")
        endTime = ET.SubElement(endTimeOffset, "Uni")
        endTime.text = phrase.get("end-time-offset")

        freeTranslation = ET.SubElement(segmentRt, "FreeTranslation")

        freeTranslList = phrase.findall("./item[@type='gls']")
        for transl in freeTranslList:
            lang = transl.get("lang")
            freeAstr = ET.SubElement(freeTranslation, "AStr", attrib={"ws": lang})
            freeRun = ET.SubElement(freeAstr, "Run", attrib={"ws": lang})
            freeRun.text = transl.text

        litTranslation = ET.SubElement(segmentRt, "LiteralTranslation")

        litTranslList = phrase.findall("./item[@type='lit']")
        segnum = phrase.find(".//item[@type='segnum']")
        litTranslList.append(segnum)
        for transl in litTranslList:
            if transl is not None:
                if transl.get("type") == "segnum":
                    # Ref tier writing system, it's not universally applicable
                    lang = "en-x-ref"
                else:
                    lang = transl.get("lang")
                litAstr = ET.SubElement(litTranslation, "AStr", attrib={"ws": lang})
                litRun = ET.SubElement(litAstr, "Run", attrib={"ws": lang})
                litRun.text = transl.text

        if mediaguid is not None:
            mediaURI = ET.SubElement(segmentRt, "MediaURI")
            mediaSur = ET.SubElement(mediaURI, "objsur", attrib={"guid": mediaguid, "t": "r"})

        # Creating Notes

        noteList = phrase.findall(".//item[@type='note']")
        if len(noteList) > 0:
            notes = ET.SubElement(segmentRt, "Notes")
            for note in noteList:
                if note.text:
                    noteLang = note.get("lang")
                    noteGuid = self.createGUID(self)
                    surNote = ET.SubElement(notes, "objsur", attrib={"guid": noteGuid, "t": "o"})

                    # And the actual Note element

                    noteRt = ET.Element("rt", attrib={"class": "Note", "guid": noteGuid, "ownerguid": guid})

                    noteContent = ET.SubElement(noteRt, "Content")
                    noteAStr = ET.SubElement(noteContent, "AStr", attrib={"ws": noteLang})
                    noteRun = ET.SubElement(noteAStr, "Run", attrib={"ws": noteLang})
                    noteRun.text = note.text

                    self.FWroot.append(noteRt)

        # Handling speakers

        speaker = phrase.get("speaker")
        spk = ET.SubElement(segmentRt, "Speaker")
        spCheck = self.checkSpeaker(self, speaker)

        if spCheck[0]:
            # Speaker exists in the DB
            spkObjsur = ET.SubElement(spk, "objsur", attrib={"guid": spCheck[0], "t": "r"})

        else:
            # Add a new speaker
            spGuid = self.createGUID(self)
            self.addNewSpeaker(self, speaker, spGuid, spCheck[1])
            spkObjsur = ET.SubElement(spk, "objsur", attrib={"guid": spGuid, "t": "r"})

        self.FWroot.append(segmentRt)

    # Create an instance of StTxtPara (= a single paragraph)

    def makeStTxtPara(self, guid, ownerguid, paragraph, mediaguid):
        stTxtParaRt = ET.Element("rt", attrib={"class": "StTxtPara", "guid": guid, "ownerguid": ownerguid})

        content = ET.SubElement(stTxtParaRt, "Contents")
        strEl = ET.SubElement(content, "Str")
        run = ET.SubElement(strEl, "Run", attrib={"ws": self.tlang})

        paraTextXPath = ".//phrases/phrase/item[@lang='" + self.tlang + "'][@type='txt']"
        paraText = paragraph.findall(paraTextXPath)
        textStr = ""
        if (len(paraText)) > 0:
            for text in paraText:
                textStr = textStr + text.text
        else:
            print("Debug message: No text for the paragraph was found, could be an error")

        run.text = textStr
        parseCurrent = ET.SubElement(stTxtParaRt, "ParseIsCurrent", attrib={"val": "True"})

        segmentList = ET.SubElement(stTxtParaRt, "Segments")
        listSentences = paragraph.findall(".//phrases/phrase")

        for sent in listSentences:
            sentGuid = self.createGUID(self)
            surSent = ET.SubElement(segmentList, "objsur", attrib={"guid": sentGuid, "t": "o"})

            # Calling MakeSegment
            self.makeSegment(self, sentGuid, guid, sent, mediaguid)

        self.FWroot.append(stTxtParaRt)

    def getFilenames(self, path):
        for i in os.scandir(path):
            if i.is_dir(follow_symlinks=False):
                yield from self.getFilenames(self, i.path)
            elif i.is_file() and i.name.endswith('flextext'):
                yield i
            else:
                continue

    # Main XML parser block
    def convertFiles(self, path):
        count_files = self.getFilenames(self, path)
        num_files = 0

        for f in count_files:
            num_files = num_files + 1

        if num_files > 100:
            file_counter, previous_step = 0, 0

        filelist = self.getFilenames(self, path)
        for f in filelist:
            nextfile = "Now converting\n" + f.name
            print(nextfile)

            if num_files <= 100:
                self.main_window.update_progress(nextfile, int((1/num_files) * 100))
            else:
                file_counter = file_counter + 1
                current_step = int((file_counter/num_files) * 100)
                if current_step > previous_step:
                    self.main_window.update_progress(nextfile, 1)
                previous_step = current_step
            tree = ET.parse(f.path)
            root = tree.getroot()

            # Create a Text

            textContainer = root.find(".//interlinear-text")

            textUID = self.createGUID(self)
            textRt = ET.Element("rt", attrib={"class": "Text", "guid": textUID})

            abbr = ET.SubElement(textRt, "Abbreviation")
            abbuni = ET.SubElement(abbr, "AUni", attrib={"ws": self.glang1})
            # Handle cases where there is no abbreviation provided in flextext
            abbrText = root.find(".//interlinear-text/item[@type='abbreviation']")
            if abbrText is None:
                abbrText = root.find(".//interlinear-text/item[@type='title-abbreviation']")
            if abbrText is not None:
                abbuni.text = abbrText.text
            else:
                # The default abbreviation that is formatted as the flextext filename plus a timestamp
                abbuni.text = f.name + "_" + str(date.today())

            contents = ET.SubElement(textRt, "Contents")
            StTextUID = self.createGUID(self)
            subStText = ET.SubElement(contents, "objsur", attrib={"guid": StTextUID, "t": "o"})

            dateCreated = ET.SubElement(textRt, "DateCreated", attrib={"val": self.curDate})
            dateModified = ET.SubElement(textRt, "DateModified", attrib={"val": self.curDate})

            isTransl = ET.SubElement(textRt, "IsTranslated", attrib={"val": "False"})

            if textContainer.find("./media-files"):
                mediaFiles = ET.SubElement(textRt, "MediaFiles")
                mediaGuid = self.createGUID(self)
                mediaSub = ET.SubElement(mediaFiles, "objsur", attrib={"guid": mediaGuid, "t": "o"})

                # Create mediafile entries

                cmMediaContainerRt = ET.Element("rt", attrib={"class": "CmMediaContainer", "guid": mediaGuid, "ownerguid": textUID})
                mediaURIs = ET.SubElement(cmMediaContainerRt, "MediaURIs")
                mediaURIGuid = self.createGUID(self)
                mediaURISub = ET.SubElement(mediaURIs, "objsur", attrib={"guid": mediaURIGuid, "t": "o"})

                self.FWroot.append(cmMediaContainerRt)

                cmMediaURIRt = ET.Element("rt", attrib={"class": "CmMediaURI", "guid": mediaURIGuid, "ownerguid": mediaGuid})
                mediaURI = ET.SubElement(cmMediaURIRt, "MediaURI")
                URIPath = textContainer.find("./media-files/media").attrib["location"]
                mediaURIUni = ET.SubElement(mediaURI, "Uni")
                mediaURIUni.text = URIPath

                self.FWroot.append(cmMediaURIRt)
            else:
                # If the text does not have media associated with it
                mediaURIGuid = None


            textName = ET.SubElement(textRt, "Name")
            nameAuni = ET.SubElement(textName, "AUni", attrib={"ws": self.glang1})
            # Handle cases where there is no title provided in flextext
            titleText = root.find(".//interlinear-text/item[@type='title']")
            if titleText is not None:
                nameAuni.text = titleText.text
            else:
                # The default text name that is formatted as the flextext filename plus a timestamp
                nameAuni.text = f.name + "_" + str(date.today())

            textSource = ET.SubElement(textRt, "Source")
            sourceAstr = ET.SubElement(textSource, "AStr", attrib={"ws": self.glang1})
            sourceRun = ET.SubElement(sourceAstr, "Run", attrib={"ws": self.glang1})
            # Handle cases where there is no title provided in flextext
            sourceText = root.find(".//interlinear-text/item[@type='source']")
            if sourceText is not None:
                sourceRun.text = sourceText.text
            else:
                # The default source is an empty string
                sourceRun.text = ""

            # Create an StText (= a list of paragraphs)

            stTextRt = ET.Element("rt", attrib={"class": "StText", "guid": StTextUID, "ownerguid": textUID})

            dateModified = ET.SubElement(stTextRt, "DateModified", attrib={"val": self.curDate})
            allParagraphs = root.findall(".//paragraph")
            paraUIDList = list()
            stParagraphs = ET.SubElement(stTextRt, "Paragraphs")

            for pr in range(len(allParagraphs)):
                curParaID = self.createGUID(self)
                paraUIDList.append(curParaID)
                surPara = ET.SubElement(stParagraphs, "objsur", attrib={"guid": curParaID, "t": "o"})

                # Calling makeStTxtPara here
                self.makeStTxtPara(self, curParaID, StTextUID, allParagraphs[pr], mediaURIGuid)

            rigtToLeft = ET.SubElement(stTextRt, "RightToLeft", attrib={"val": "False"})

            self.FWroot.append(stTextRt)
            self.FWroot.append(textRt)
