<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:map="http://www.w3.org/2005/xpath-functions/map"
    xmlns:inel="http://inel.corpora.uni-hamburg.de"
    exclude-result-prefixes="#all"
    version="3.0">
    <xsl:output method="xml" indent="yes" encoding="utf-8" omit-xml-declaration="no"/>
    <xsl:namespace-alias stylesheet-prefix="#default" result-prefix=""/>
    
    <xsl:param name="folder-in" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/todo/'"/>
    <xsl:param name="folder-out" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step1/'"/>
    <xsl:param name="filemask" select="'?select=*.eaf'"/>
    <xsl:variable name="sourcecollection" select="collection(concat($folder-in,$filemask))"/>
    
    <xsl:variable name="speaker-codes" select="map {
        'AM' : 'SAM',
        'AN' : 'PAN',
        'AP' : 'BAP',
        'AS' : 'BAS',
        'ASP' : 'PAS',
        'ASS' : 'SAS',
        'DA' : 'SDnA',
        'DS' : 'BDS',
        'EDB' : 'BED',
        'EIB' : 'BEI',
        'ES' : 'GES',
        'GA' : 'IGA',
        'IE' : 'BIE',
        'II' : 'SIIP',
        'KAB' : 'BKA',
        'KDJA' : 'YKD',
        'LKU' : 'BLK',
        'LD' : 'BLD',
        'MNB' : 'BMN',
        'MNS' : 'SMN',
        'ND' : 'LND',
        'NI' : 'SNI',
        'NK' : 'BNK',
        'NKU' : 'BNKu',
        'NNB' : 'BNN',
        'NPCH' : 'ChNP',
        'NSB' : 'BNS',
        'NSP' : 'PNS',
        'PN' : 'BPN',
        'SA' : 'RSA',
        'SPB' : 'BSP',
        'TN' : 'BTN',
        'VMS' : 'SVM',
        'VN' : 'PVN',
        'VINB' : 'BViN',
        'VNB' : 'BVN',
        'ZKU' : 'TZK',
        'ZN' : 'BZN',
        'XXX' : 'XXX',
        'AS_NI' : 'BAS',
        'AS_DA' : 'BAS',
        'ASS_VMS_NNB' : 'SVM',
        'NI_ES' : 'SNI'
        }"/>
    <!-- AS_NI, AS_DA, ASS_VMS_NNB, NI_ES: default speaker for dialogues with incomplete tiers -->
    
    <xsl:variable name="tier-names" select="map { 
        'ref' : 'ref-segnum-en', 
        'tx_lat_for_toolbox' : 'tx-txt-enf', 
        'mb' : 'mb-cf-enf',
        'ge' : 'ge-gls-en', 
        'ger' : 'gr-gls-ru',
        'ps' : 'ps-msa-en',
        'ft_r' : 'fr-gls-ru',
        'ft_e' : 'fe-gls-en',
        'tx_lat_during_transcription' : 'stl-lit-enf-Latn-x-source',
        'tx_cyr' : 'st-lit-enf-x-source',
        'ft_r_during_transcription' : 'ltr-lit-ru',
        'lit_trans_e' : 'lte-lit-en',
        'com_m' : 'nto-note-ru'
        }"/>
    
    <xsl:variable name="tiers-2nd-speaker" select="('NN_tx_lat_during_transcription', 'tx_lat-AP', 'tx_lat_during_transcription_AS', 
        'tx_lat_during_transcription_DA', 'tx_lat_during_transcription_ES', 'tx_lat_during_transcription_GA', 
        'tx_lat_during_transcription_NI', 'tx_lat_during_transcription_NN')"/>
    
    <xsl:variable name="speakers-2nd-speaker" select="map {'NN_tx_lat_during_transcription': 'NNB', 'tx_lat-AP' : 'AP', 'tx_lat_during_transcription_AS' : 'AS', 
        'tx_lat_during_transcription_DA' : 'DA', 'tx_lat_during_transcription_ES' : 'ES', 'tx_lat_during_transcription_GA' : 'GA', 
        'tx_lat_during_transcription_NI' : 'NI', 'tx_lat_during_transcription_NN' : 'NNB'}"/>

    <xsl:variable name="tiers-append" select="map {
        'tx_lat_during_transcription' : ('tx_lat','tx_lat_during_transcription_VN'),
        'tx_cyr' : 'tx_cyr_during_transcription',
        'ft_r_during_transcription' : ('lit_trans','Preliminary_Translation','ft_r_during_transcription_VN','ft_r_during_transcription_preliminary'),
        'com_m' : ('add_ling','ASK','ZN_comments','answers_ZN','cmt_e','cmt_r','com_gl','com_m_ZN','nt','questions')
        }"/>
    
    <xsl:variable name="tiers-skip" select="('speaker','recorder','translator','annotator_preliminary','annotator_toolbox',
        'tx_lat','NN_tx_lat_during_transcription', 'tx_lat-AP', 'tx_lat_during_transcription_AS', 
        'tx_lat_during_transcription_DA', 'tx_lat_during_transcription_ES', 'tx_lat_during_transcription_GA', 
        'tx_lat_during_transcription_NI', 'tx_lat_during_transcription_NN', 'tx_lat_during_transcription_VN',
        'tx_cyr_during_transcription','lit_trans','Preliminary_Translation','ft_r_during_transcription_VN',
        'ft_r_during_transcription_preliminary','add_ling','ASK','ZN_comments','answers_ZN','cmt_e','cmt_r','com_gl','com_m_ZN','nt','questions',
        'info','Comments_Enets_phonology','Enets_phonology','ashl','glossing','literal_trans_to_print','rus_to_print','tx_lat_to_print')"/>
    
    <xsl:function name="inel:rename-tier" as="xs:string">
        <xsl:param name="name-old" as="xs:string"></xsl:param>
        <xsl:variable name="speaker-old" select="substring-after($name-old,'@')"/>
        <xsl:variable name="speaker-new" select="if(map:contains($speaker-codes,$speaker-old)) then $speaker-codes($speaker-old) else $speaker-old"/>
        <xsl:variable name="tier-old" select="substring-before($name-old,'@')"/>
        <xsl:variable name="tier-new" select="if(map:contains($tier-names,$tier-old)) then $tier-names($tier-old) else $tier-old"/>
        <xsl:value-of select="if($speaker-new='unknown') then $tier-new else $speaker-new||'@'||$tier-new"/>
    </xsl:function>
    
    <xsl:function name="inel:rename-type" as="xs:string">
        <xsl:param name="type-old" as="xs:string"></xsl:param>
        <xsl:value-of select="if(map:contains($tier-names,$type-old)) then $tier-names($type-old) else $type-old"/>
    </xsl:function>
    
    <xsl:template name="main" match="/">
        <xsl:for-each select="$sourcecollection">
            <xsl:variable name="filename" select="replace(document-uri(current()),'^.+/','')"/>
            <xsl:variable name="textname" select="replace($filename,'\.eaf','')"/>
            <xsl:result-document method="xml" indent="yes" encoding="utf-8" omit-xml-declaration="no"
                href="{concat($folder-out,$filename)}">
                <xsl:apply-templates/>
            </xsl:result-document>    
        </xsl:for-each>
    </xsl:template>

    <!-- identity template -->
    <!-- Everything which is not treated in a special way is just copied entirely -->
    <xsl:template match="*|text()|@*">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>
    
    <!-- skip tiers, e.g. those copied elsewhere -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF=$tiers-skip]"/>
    
    <!-- change tier names for the given tier and its parent reference -->
    <xsl:template match="@TIER_ID">
        <xsl:attribute name="TIER_ID" select="inel:rename-tier(.)"/>
    </xsl:template>
    
    <xsl:template match="@PARENT_REF">
        <xsl:attribute name="PARENT_REF" select="inel:rename-tier(.)"/>
    </xsl:template>
    
    <!-- change tier names for the given linguistic type and references to it -->
    <xsl:template match="@LINGUISTIC_TYPE_ID">
        <xsl:attribute name="LINGUISTIC_TYPE_ID" select="inel:rename-type(.)"/>
    </xsl:template>

    <xsl:template match="@LINGUISTIC_TYPE_REF">
        <xsl:attribute name="LINGUISTIC_TYPE_REF" select="inel:rename-type(.)"/>
    </xsl:template>
    
    <!-- change speaker codes -->
    <xsl:template match="@PARTICIPANT">
        <xsl:param name="speaker-from-textcode" tunnel="yes"/>
        <xsl:attribute name="PARTICIPANT" select="if (.='unknown') then $speaker-codes($speaker-from-textcode) else $speaker-codes(.)"/>
    </xsl:template>
    
    <!-- append annotations from secondary tiers if primary tier is listed in $tiers-append -->
    <xsl:template match="TIER[map:contains($tiers-append,@LINGUISTIC_TYPE_REF)]//ANNOTATION_VALUE">
        <xsl:variable name="tiers-alt" select="$tiers-append(ancestor::TIER/@LINGUISTIC_TYPE_REF)"/>
        <xsl:variable name="speaker" select="ancestor::TIER/@PARTICIPANT"/>
        <xsl:variable name="annot-ref" select="../@ANNOTATION_REF"/>
        <xsl:variable name="value-own" select="./text()"/>
        <xsl:variable name="value-2nd-speaker">
            <xsl:value-of select="if (ancestor::TIER/@LINGUISTIC_TYPE_REF = 'tx_lat_during_transcription'
                and not(empty(//TIER[@LINGUISTIC_TYPE_REF=$tiers-2nd-speaker]))) 
                then string-join(
                    for $t in $tiers-2nd-speaker return 
                        //TIER[@LINGUISTIC_TYPE_REF=$t]//REF_ANNOTATION[@ANNOTATION_REF=$annot-ref]/ANNOTATION_VALUE[text()!='']/concat('[',$speaker-codes($speakers-2nd-speaker($t)),':] ',text()),
                    ' || ')
                else ''"/>
        </xsl:variable>
        <xsl:variable name="value-alt">
            <xsl:value-of select="for $t in $tiers-alt return
                //TIER[@LINGUISTIC_TYPE_REF=$t and @PARTICIPANT=$speaker]//REF_ANNOTATION[@ANNOTATION_REF=$annot-ref]/ANNOTATION_VALUE/text()"/>
        </xsl:variable>
        <ANNOTATION_VALUE>
            <!-- concatenates own value with values from secondary tiers, excluding empty strings -->
            <xsl:value-of select="string-join(($value-own, $value-2nd-speaker[.!=''], string-join($value-alt[.!=''], ' || '))[.!=''], ' || ')"/>
        </ANNOTATION_VALUE>
    </xsl:template>
    

    <!-- Update annotation counter for annotations in added top-level tiers-->
    <xsl:template match="HEADER/PROPERTY[@NAME='lastUsedAnnotationId']">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:value-of select="string(number(text())+3)"/>
        </xsl:copy>
    </xsl:template>
    
    <!-- Insert top-level info tiers -->    
    <xsl:template match="ANNOTATION_DOCUMENT">
        <xsl:variable name="filename" select="substring-before(base-uri(),'.eaf')=>replace('^.*/','')"/>
        <xsl:variable name="textcode" select="replace((TIER[@LINGUISTIC_TYPE_REF='ref']//ANNOTATION_VALUE)[1]/text(),'_[0-9]+$','')"/>
        <xsl:variable name="speaker" select="replace($textcode,'[0-9]+.*$','')"/>
        <xsl:variable name="ann-last" select="number(HEADER/PROPERTY[@NAME='lastUsedAnnotationId']/text())"/>
        <xsl:variable name="timeslot-first" select="TIME_ORDER/TIME_SLOT[1]/@TIME_SLOT_ID"/>
        <xsl:variable name="timeslot-last" select="TIME_ORDER/TIME_SLOT[position()=last()]/@TIME_SLOT_ID"/>
        <xsl:variable name="info-speaker" select="TIER[@LINGUISTIC_TYPE_REF='speaker']//ANNOTATION_VALUE/text()"/>
        <xsl:variable name="info-recorder" select="TIER[@LINGUISTIC_TYPE_REF='recorder']//ANNOTATION_VALUE/text()"/>
        <xsl:variable name="info-translator" select="TIER[@LINGUISTIC_TYPE_REF='translator']//ANNOTATION_VALUE/text()"/>
        <xsl:variable name="info-ann-prelim" select="TIER[@LINGUISTIC_TYPE_REF='annotator_preliminary']//ANNOTATION_VALUE/text()"/>
        <xsl:variable name="info-ann-toolbox" select="TIER[@LINGUISTIC_TYPE_REF='annotator_toolbox']//ANNOTATION_VALUE/text()"/>
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates select="* except (LINGUISTIC_TYPE|CONSTRAINT)">
                <xsl:with-param name="speaker-from-textcode" select="$speaker" tunnel="yes"/>
            </xsl:apply-templates>
            
            <!-- top-level tier with text code -->
            <TIER LINGUISTIC_TYPE_REF="interlinear-text-abbreviation-en" TIER_ID="interlinear-text-abbreviation-en">
                <ANNOTATION>
                    <ALIGNABLE_ANNOTATION ANNOTATION_ID="a{string($ann-last+1)}"
                        TIME_SLOT_REF1="{$timeslot-first}" TIME_SLOT_REF2="{$timeslot-last}">
                        <ANNOTATION_VALUE><xsl:value-of select="$textcode"/></ANNOTATION_VALUE>
                    </ALIGNABLE_ANNOTATION>
                </ANNOTATION>
            </TIER>
            
            <!-- dependent tiers with other info -->
            <TIER LINGUISTIC_TYPE_REF="interlinear-text-title-en"
                PARENT_REF="interlinear-text-abbreviation-en" TIER_ID="interlinear-text-title-en">
                <ANNOTATION>
                    <REF_ANNOTATION ANNOTATION_ID="a{string($ann-last+2)}" ANNOTATION_REF="a{string($ann-last+1)}">
                        <ANNOTATION_VALUE><xsl:value-of select="'$$'||$filename"/></ANNOTATION_VALUE>
                    </REF_ANNOTATION>
                </ANNOTATION>
            </TIER>
            <TIER LINGUISTIC_TYPE_REF="interlinear-text-source-en"
                PARENT_REF="interlinear-text-abbreviation-en" TIER_ID="interlinear-text-source-en">
                <ANNOTATION>
                    <REF_ANNOTATION ANNOTATION_ID="a{string($ann-last+3)}" ANNOTATION_REF="a{string($ann-last+1)}">
                        <ANNOTATION_VALUE>@speaker: <xsl:value-of select="$info-speaker"/>;&#x2028;@recorder: <xsl:value-of select="$info-recorder"/>;&#x2028;@translator: <xsl:value-of select="$info-translator"/>;&#x2028;@annotator_preliminary: <xsl:value-of select="$info-ann-prelim"/>;&#x2028;@annotator_toolbox: <xsl:value-of select="$info-ann-toolbox"/>;&#x2028;@filename: <xsl:value-of select="$filename"/>;&#x2028;@textcode: <xsl:value-of select="$textcode"/>;&#x2028;@collection: Khanina&amp;Shluinsky Enets glossed collection 2008-2012</ANNOTATION_VALUE>
                    </REF_ANNOTATION>
                </ANNOTATION>
            </TIER>
            
            <!-- new types for added tiers -->
            <LINGUISTIC_TYPE GRAPHIC_REFERENCES="false"
                LINGUISTIC_TYPE_ID="interlinear-text-abbreviation-en" TIME_ALIGNABLE="true"/>
            <LINGUISTIC_TYPE CONSTRAINTS="Symbolic_Association"
                GRAPHIC_REFERENCES="false"
                LINGUISTIC_TYPE_ID="interlinear-text-title-en" TIME_ALIGNABLE="false"/>
            <LINGUISTIC_TYPE CONSTRAINTS="Symbolic_Association"
                GRAPHIC_REFERENCES="false"
                LINGUISTIC_TYPE_ID="interlinear-text-source-en" TIME_ALIGNABLE="false"/>
            <xsl:apply-templates select="(LINGUISTIC_TYPE|CONSTRAINT)"/>
        </xsl:copy>
    </xsl:template>
    
    
</xsl:stylesheet>