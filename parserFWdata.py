import os
import json
import xml.etree.ElementTree as ET
import time

def parse(xml, target, gloss, gloss2, main_window):
    if not os.path.exists("parsed"):
        os.mkdir("parsed")

    tree = ET.parse(xml)
    root = tree.getroot()

    parsing_steps = 7
    # call these functions with csv=True to get CSV output alongside JSON
    main_window.update_progress("Now parsing\nPartOfSpeech...", int(100/parsing_steps))
    export_pos(root)

    main_window.update_progress("Now parsing\nMoMorphType...", int(100/parsing_steps))
    export_momorphtype(root)

    main_window.update_progress("Now parsing\nLexData...", int(100/parsing_steps))
    export_lexdata(root, target, gloss, gloss2)

    main_window.update_progress("Now parsing\nWfiAnalysis...", int(100/parsing_steps))
    export_wfianalysis(root, target)

    main_window.update_progress("Now parsing\nMoInflAffixSlot...", int(100/parsing_steps))
    export_moinflaffixslot(root)

    main_window.update_progress("Now parsing\nPunctuationForm...", int(100/parsing_steps))
    export_punctuationform(root)

    main_window.update_progress("Now parsing\nSpeakerData...", int(100/parsing_steps))
    export_speakerdata(root)

    #print("Done parsing!")


#export the database of PartOfSpeech
def export_pos(root, csv=False):
    if csv:
        resultFile = open('parsed/PartOfSpeechData.csv', 'w')

    posList = root.findall(".//rt[@class='PartOfSpeech']")
    output = list()

    for pos in posList:
        guid = pos.get("guid")
        if len(pos.findall(".//Abbreviation/AUni")) > 0:
            abbr = pos.findall(".//Abbreviation/AUni")[0].text
        else:
            print(f'Part of speeech with the ID {guid} has no abbreviation, skipping...')
            continue
        if len(pos.findall(".//Name/AUni")) > 0:
            name = pos.findall(".//Name/AUni")[0].text
        else:
            print(f'Part of speeech with the ID {guid} has no name, skipping...')
            continue

        output.append({ "pos": abbr, "id": guid, "name": name })

        if csv:
            outputLine = guid + "¶" + abbr + "¶" + name
            resultFile.write(outputLine)
            resultFile.write('\n')

    if csv:
        resultFile.close()
    with open("parsed/PartOfSpeechData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

#export the database of MoMorphType
def export_momorphtype(root, csv=False):
    if csv:
        resultFile = open('parsed/MoMorphType.csv', 'w')

    momoList = root.findall(".//rt[@class='MoMorphType']")
    output = list()

    for momo in momoList:
        guid = momo.get("guid")
        abbr = momo.findall(".//Abbreviation/AUni")[0].text
        name = momo.findall(".//Name/AUni")[0].text

        output.append({ "id": guid, "fullname": abbr, "abbr": name })
        if csv:
            outputLine = id + "¶" + abbr + "¶" + name
            resultFile.write(outputLine)
            resultFile.write('\n')

    if csv:
        resultFile.close()
    with open("parsed/MoMorphType.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

#export the database of LexEntry-LexSense + allomorphs + MSA
def export_lexdata(root, target, gloss, gloss2, csv=False):
    if csv:
        resultFile = open('parsed/LexData.csv', 'w')
        legendLine = "LexEntry GUID" + "¶" + "GlossEn" + "¶" + "GlossRu" + "¶" + "LexSense GUID" + "¶" + "MorphoSyntaxAnalysis GUID" + "¶" + "Lexeme Form" + "¶" + "Lexeme Form GUID" + "¶" + "Alternate Form"  + "¶" + "Alternate Form GUID"
        resultFile.write(legendLine)
        resultFile.write('\n')
    lexList = root.findall(".//rt[@class='LexSense']")
    output = list()

    for lex in lexList:
        lexId = lex.get("guid")
        try:
            glossEnXPath = ".//Gloss/AUni[@ws='" + gloss + "']"
            glossEn = lex.find(glossEnXPath).text
        except AttributeError:
            glossEn = ""

        try:
            glossRuXPath = ".//Gloss/AUni[@ws='" + gloss2 + "']"
            glossRu = lex.find(glossRuXPath).text
        except AttributeError:
            glossRu = ""

        try:
            msa = lex.findall(".//MorphoSyntaxAnalysis/objsur")[0].get("guid")
        except IndexError:
            msa = ""

        lexEntry = lex.get("ownerguid")
        entryXpath = ".//rt[@guid='" + lexEntry + "']"
        entryId = root.findall(entryXpath)[0]

        lexemeGuid = entryId.findall(".//LexemeForm/objsur")[0].get("guid")
        lexemeXPath = ".//rt[@guid='" + lexemeGuid + "']/Form/AUni[@ws='" + target + "']"
        lexemeForm = root.findall(lexemeXPath)[0].text

        listOfFormsJSON = list()
        curForm = dict()
        curForm["Form"] = lexemeForm
        curForm["Form-GUID"] = lexemeGuid
        listOfFormsJSON.append(curForm)

        if csv:
            listOfForms = list()
            listOfForms.append(lexemeForm)
            listOfForms.append(lexemeGuid)

        alterForms = entryId.findall(".//AlternateForms/objsur")
        for af in alterForms:
            afId = af.get("guid")
            moAlterXPath = ".//rt[@guid='" + afId + "']/Form/AUni[@ws='" + target + "']"
            try:
                altForm = root.findall(moAlterXPath)[0].text
            except IndexError:
                altForm = ""

            curForm = dict()
            curForm["Form"] = altForm
            curForm["Form-GUID"] = afId
            listOfFormsJSON.append(curForm)

            if csv:
                listOfForms.append(altForm)
                listOfForms.append(afId)

        output.append({ "LexSense-GUID": lexId, "GlossEn": glossEn,
                    "GlossRu": glossRu, "LexEntry-GUID": lexEntry,
                    "MorphoSyntaxAnalysis-GUID": msa, "forms": listOfFormsJSON })

        if csv:
            forms = "¶".join(listOfForms)
            outputLine = lexEntry + "¶" + glossEn + "¶" + glossRu + "¶" + lexId + "¶" + msa + "¶" + forms
            resultFile.write(outputLine)
            resultFile.write('\n')

    with open("parsed/LexData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

    if csv:
        resultFile.close()

#export the database of WfiAnalyses
def export_wfianalysis(root, target, csv=None):
    if csv:
        resultFile = open('parsed/WfiData.csv', 'w')
        legendLine = "WfiWordform GUID" + "¶" + "WfiWordform" + "¶" + "WfiAnalysis GUID" + "¶" + "MoprhGUID" + "¶" + "Morph text" + "¶" + "Sense GUID"
        resultFile.write(legendLine)
        resultFile.write('\n')
    wifiList = root.findall(".//rt[@class='WfiAnalysis']")
    output = list()

    for wifi in wifiList:
        guid = wifi.get("guid")
        ownerid = wifi.get("ownerguid")

        wordformXPath = ".//rt[@guid='" + ownerid + "']/Form/AUni[@ws='" + target + "']"
        try:
            wordform = root.findall(wordformXPath)[0].text
        except:
            wordform = ""

        try:
            categoryGUID = wifi.findall(".//Category/objsur")[0].get("guid")
        except:
            categoryGUID = ""

        morphBundles = wifi.findall(".//MorphBundles/objsur")
        listOfMorphsJSON = list()

        if csv:
            listOfMorphs = list()

        for morph in morphBundles:
            morphguid = morph.get("guid")
            morphXPath = ".//rt[@guid='" + morphguid + "']"

            morphBundle = root.findall(morphXPath)[0]

            try:
                morphText = morphBundle.findall(".//Form/AStr/Run")[0].text
            except:
                morphText = ""

            try:
                morphGUID = morphBundle.findall(".//Morph/objsur")[0].get("guid")
            except:
                morphGUID = ""

            try:
                senseGUID = morphBundle.findall(".//Sense/objsur")[0].get("guid")
            except:
                senseGUID = ""

            curMorph = dict()
            curMorph["Morph-GUID"] = morphGUID
            curMorph["Morph"] = morphText
            curMorph["Sense-Guid"] = senseGUID
            listOfMorphsJSON.append(curMorph)

            if csv:
                listOfMorphs.append(morphGUID)
                listOfMorphs.append(morphText)
                listOfMorphs.append(senseGUID)

        output.append({ "WfiWordform-GUID": ownerid, "WfiWordform": wordform,
                       "WfiAnalysis-GUID": guid, "Category-GUID": categoryGUID, "senses": listOfMorphsJSON })

        if csv:
            morphsString = "¶".join(listOfMorphs)
            outputLine = ownerid + "¶" + wordform + "¶" + guid + "¶" + categoryGUID + "¶" + morphsString
            resultFile.write(outputLine)
            resultFile.write('\n')

    if csv:
        resultFile.close()

    with open("parsed/WfiData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

# export MoInflAffixSlotData
def export_moinflaffixslot(root, csv=False):
    if csv:
        resultFile = open('parsed/MoInflAffixSlotData.csv', 'w')
    miasdList = root.findall(".//rt[@class='MoInflAffixSlot']")
    output = list()

    for miasd in miasdList:
        guid = miasd.get("guid")
        ownerid = miasd.get("ownerguid")
        try:
            name = miasd.findall(".//Name/AUni")[0].text
        except:
            name = ""

        output.append({ "slot": name, "id": guid, "posid": ownerid })

        if csv:
            outputLine = name + "¶" + id + "¶" + ownerid
            resultFile.write(outputLine)
            resultFile.write('\n')

    if csv:
        resultFile.close()

    with open("parsed/MoInflAffixSlotData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

# export PunctuationFormData
def export_punctuationform(root, csv=False):
    if csv:
        resultFile = open('parsed/PunctuationFormData.csv', 'w')
    punctList = root.findall(".//rt[@class='PunctuationForm']")
    output = list()

    for pf in punctList:
        guid = pf.get("guid")
        value = pf.findall(".//Form/Str/Run")[0].text

        output.append({ "id": guid, "value": value })

        if csv:
            outputLine = id + "¶" + value
            resultFile.write(outputLine)
            resultFile.write("\n")

    with open("parsed/PunctuationFormData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)

    if csv:
        resultFile.close()

# export SpeakerData
def export_speakerdata(root, csv=False):
    if csv:
        resultFile = open('parsed/SpeakerData.csv', 'w')
    speakerList = root.findall(".//rt[@class='CmPerson']")
    output = list()

    for sp in speakerList:
        guid = sp.get("guid")
        cmPossibilityId = sp.get("ownerguid")
        try:
            value = sp.findall(".//Name/AUni")[0].text
        except:
            value = ""

        output.append({"tag": value, "id": guid, "cmPossibilityId": cmPossibilityId})

        if csv:
            outputLine = value + "¶" + guid + "¶" + cmPossibilityId
            resultFile.write(outputLine)
            resultFile.write("\n")

    if csv:
        resultFile.close()

    with open("parsed/SpeakerData.json", 'w', encoding='utf8') as j:
        print(json.dumps(output), file=j)


#export the elements of each class in a separate XML
#TODO: refactor as functions
'''rtlist = root.findall(".//rt")
classList = list()

for rt in rtlist:
    rtClass = rt.get("class")
    classList.append(rtClass)

classList = sorted(list(set(classList)))

for elem in range(len(classList)):
    xpathClass = ".//rt[@class='" + classList[elem] + "']"
    rtOfClass = root.findall(xpathClass)

    classTxtFilename = classList[elem] + ".xml"
    classRoot = ET.Element("tag")
    with open(classTxtFilename, "w") as clOut:
        for roc in rtOfClass:
            classRoot.append(roc)
    classTree = ET.ElementTree(element=classRoot)
    classTree.write(classTxtFilename, encoding="utf-8")'''

#export the elements related to a single text id in an XML file
'''def parseId(rt):
    guid = rt.get("guid")
    idList.append(guid)
    textRoot.append(rt)
    print(rt.get("class"))

    if rt.get("ownerguid"):
        ownerguid = rt.get("ownerguid")
        if ownerguid not in idList:
            XPathOwner = ".//rt[@guid='" + ownerguid + "']"
            #parseId(root.findall(XPathOwner)[0])

    objsur = rt.findall(".//objsur")
    for obj in objsur:
        if obj.get("guid") not in idList:
            XPathObjsur = ".//rt[@guid='" + obj.get("guid") + "']"
            surobj = root.findall(XPathObjsur)[0]
            if surobj.get("class") in skipClassList:
                pass
            else:
                parseId(surobj)

textRoot = ET.Element("Element")
idList = list()

skipClassList = ["PartOfSpeech", "CmAgentEvaluation", "MoMorphType", "MoStemName"]

text = root.findall(".//rt[@guid='0e35f44b-3134-457b-86c7-0d5f6d8bf74d']")

parseId(text[0])
textTree = ET.ElementTree(element=textRoot)
textTree.write("text-test.xml", encoding="utf-8")'''
