<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:map="http://www.w3.org/2005/xpath-functions/map"
    xmlns:inel="http://inel.corpora.uni-hamburg.de"
    exclude-result-prefixes="#all"
    version="3.0">
    <xsl:output method="xml" indent="yes" encoding="utf-8" omit-xml-declaration="no"/>
    <xsl:namespace-alias stylesheet-prefix="#default" result-prefix=""/>
    
    <xsl:param name="folder-in" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step2/'"/>
    <xsl:param name="folder-out" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step3/'"/>
    <xsl:param name="filemask" select="'?select=*.eaf'"/>

    <xsl:variable name="sourcecollection" select="collection(concat($folder-in,$filemask))"/>
 
    <xsl:variable name="punct-regex" select="'[\.\?!,\(\)…\-]'"/>
    <xsl:variable name="non-punct-regex" select="'[^\.\?!,\(\)…\-]'"/>
    
    <!-- the key for translations uses the translation's reference to the sentence code in ref tier -->
    <xsl:key name="rus-transl" match="TIER[@LINGUISTIC_TYPE_REF='fr-gls-ru']//REF_ANNOTATION" use="@ANNOTATION_REF"/>
    <!-- the key for morphs uses morph's reference to the word -->
    <!-- only first morph in a word (i.e. with no previous morph) is indexed -->
    <xsl:key name="mb" match="TIER[@LINGUISTIC_TYPE_REF='mb-cf-enh']//REF_ANNOTATION[not(@PREVIOUS_ANNOTATION)]" use="@ANNOTATION_REF"/>
    <!-- the key for glosses uses gloss's reference to the morph -->
    <xsl:key name="gr" match="TIER[@LINGUISTIC_TYPE_REF='gr-gls-ru']//REF_ANNOTATION" use="@ANNOTATION_REF"/>
    
    <xsl:function name="inel:capitalize" as="xs:string">
        <xsl:param name="text-in" as="xs:string"/>
        <xsl:sequence select="if (matches($text-in, '^('||$non-punct-regex||'|$)')) 
            then upper-case(substring($text-in,1,1))||substring($text-in,2)
            else substring($text-in,1,1)||inel:capitalize(substring($text-in,2))"/>
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
    
    <!-- capitalize proper names in mb -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='mb-cf-enh']//ANNOTATION_VALUE/text()">
        <!-- get russian gloss of the current morph -->
        <xsl:variable name="rus-gloss" select="key('gr',ancestor::REF_ANNOTATION/@ANNOTATION_ID)/ANNOTATION_VALUE/text()"/>
        <!-- consider word a proper name if russian gloss starts with a (single) capital (exlude acronyms like ОПХ) -->
        <xsl:variable name="is-proper" select="matches($rus-gloss,'^[А-ЯЁ][а-яё]')"/>
        <xsl:value-of select="(if ($is-proper) then upper-case(substring(.,1,1))||substring(.,2) else .)"/>
    </xsl:template>

    <!-- capitalize first word in tx -->
    <!-- capitalize proper names in tx -->
    <!-- add full stop after last word in tx if there is no full stop yet -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='tx-txt-enh']//ANNOTATION_VALUE/text()">
        <!-- if there is a reference to previous annotation (in a sentence) then it is not the first word in sentence -->
        <xsl:variable name="is-first-word" select="if (ancestor::REF_ANNOTATION/@PREVIOUS_ANNOTATION) then false() else true()"/>
        <!-- if next word has a reference to previous annotation (in a sentence) then it is not the last word in sentence -->
        <xsl:variable name="is-last-word" select="if (not(ancestor::ANNOTATION/following-sibling::ANNOTATION[1]/REF_ANNOTATION/@PREVIOUS_ANNOTATION)) then true() else false()"/>
        <!-- get russian gloss of the (first) morph referring to the current word in tx -->
        <xsl:variable name="rus-gloss" select="key('gr',key('mb',ancestor::REF_ANNOTATION/@ANNOTATION_ID)/@ANNOTATION_ID)/ANNOTATION_VALUE/text()"/>
        <!-- consider word a proper name if russian gloss starts with a (single) capital (exlude acronyms like ОПХ) -->
        <xsl:variable name="is-proper" select="matches($rus-gloss,'^[А-ЯЁ][а-яё]')"/>
        <!-- get russian translation referring to the same sentence code in ref tier -->
        <xsl:variable name="rus-transl" select="key('rus-transl',ancestor::REF_ANNOTATION/@ANNOTATION_REF)/ANNOTATION_VALUE/text()"/>
        <!-- get final punctuation from russian translation ('?','!' or '.') -->
        <xsl:variable name="final-punct" select="if (ends-with($rus-transl,'?')) then '?' else if (ends-with($rus-transl,'!')) then '!' else '.'"/>
        <!-- add final punctuation if is last word and has none -->
        <xsl:variable name="add-punct" select="if ($is-last-word and not(matches(.,'[\.\?!]$'))) then $final-punct else ''"/>
        <!-- capitalize if first word or proper name, add final punctuation if needed -->
        <xsl:value-of select="(if ($is-first-word or $is-proper) then inel:capitalize(.) else .)||$add-punct"/>
    </xsl:template>
    
    <!-- capitalize first word in Russian and English translations -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF=('fr-gls-ru','fe-gls-en')]//ANNOTATION_VALUE/text()">
        <!-- add final punctuation if has none -->
        <xsl:variable name="add-punct" select="if (not(matches(.,'[\.\?!][\) &quot;]*$'))) then '.' else ''"/>
        <xsl:value-of select="inel:capitalize(.)||$add-punct"/>
    </xsl:template> 
        
</xsl:stylesheet>