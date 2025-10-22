<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:map="http://www.w3.org/2005/xpath-functions/map"
    xmlns:fn="http://www.w3.org/2005/xpath-functions"
    xmlns:inel="http://inel.corpora.uni-hamburg.de"
    exclude-result-prefixes="#all"
    version="3.0">
    <xsl:output method="xml" indent="yes" encoding="utf-8" omit-xml-declaration="no"/>
    <xsl:namespace-alias stylesheet-prefix="#default" result-prefix=""/>
    
    <xsl:param name="folder-in" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step3/'"/>
    <xsl:param name="folder-out" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/done/'"/>
    <xsl:param name="filemask" select="'?select=*.flextext'"/>

    <xsl:variable name="sourcecollection" select="collection(concat($folder-in,$filemask))"/>
    
    <xsl:variable name="punct-regex" select="'[\.\?!,\(\)…\-]'"/>
    <xsl:variable name="non-punct-regex" select="'[^\.\?!,\(\)…\-]'"/>
    
    <xsl:template name="main" match="/">
        <xsl:for-each select="$sourcecollection">
            <xsl:variable name="filename" select="replace(document-uri(current()),'^.+/','')"/>
            <xsl:variable name="textname" select="replace($filename,'\.flextext','')"/>
            
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

    <!-- if a word starts with non-punctuation and ends with punctuation, move punctuation to a separate word -->
    <xsl:template match="word[matches(item[@type='txt' and @lang='enf']/text(),'^'||$non-punct-regex||'.*'||$punct-regex||'$')]">
        <!-- take all except trailing punctuation into main word -->
        <xsl:variable name="word" select="replace(item[@type='txt' and @lang='enf']/text(),$punct-regex||'+$','')"/>
        <!-- take all except leading non-punctuatin into punct word -->
        <xsl:variable name="punct" select="replace(item[@type='txt' and @lang='enf']/text(),'^'||$non-punct-regex||'+','')"/>
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <item type="txt" lang="enf"><xsl:value-of select="$word"/></item>
            <xsl:apply-templates select="* except item[@type='txt' and @lang='enf']"/>
        </xsl:copy>
        <word>
            <item type="punct" lang="enf"><xsl:value-of select="$punct"/></item>
        </word>
    </xsl:template>

    <!-- If a word is all in brackets, mark whole word as punct -->
    <xsl:template match="word[matches(item[@type='txt' and @lang='enf']/text(),'^\(+'||$non-punct-regex||'.+\)\.?$')]">
        <xsl:variable name="word" select="item[@type='txt' and @lang='enf']/text()"/>
        <word>
            <item type="punct" lang="enf"><xsl:value-of select="$word"/></item>
        </word>
    </xsl:template>
    
    <!-- If a word has nothing but punctuation, mark whole word as punct -->
    <xsl:template match="word[matches(item[@type='txt' and @lang='enf']/text(),'^'||$punct-regex||'+$')]">
        <xsl:variable name="word" select="item[@type='txt' and @lang='enf']/text()"/>
        <word>
            <item type="punct" lang="enf"><xsl:value-of select="$word"/></item>
        </word>
    </xsl:template>
    
    
    <!-- if there are no words in sentence, add a word with '((…)).' -->
    <xsl:template match="words">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:choose>
                <xsl:when test="./word">
                    <xsl:apply-templates select="*"/>
                </xsl:when>
                <xsl:otherwise>
                    <word>
                        <item type="punct" lang="enf">((…)).</item>
                    </word>
                </xsl:otherwise>
            </xsl:choose>
            
        </xsl:copy>
    </xsl:template>
    
    <!-- change speaker code if another speaker code is specified in the beginning of stl -->
    <xsl:template match="phrase/@speaker">
        <xsl:variable name="stl-text" select="../item[@lang='enf-Latn-x-source' and @type='lit']/text()"/>
        <xsl:variable name="second-speaker" select="if (matches($stl-text,'^\[[A-Za-z]+:\]')) 
            then substring-before($stl-text,':]')=>substring-after('[') else ''"/>
        <xsl:attribute name="speaker" select="if ($second-speaker='') then . else $second-speaker"/>
    </xsl:template>

    <!-- add ts for each phrase -->
    <!-- if there are no words in sentence, use '((…)).' as text -->
    <xsl:template match="phrase">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <item type="txt" lang="enf">
                <xsl:value-of select="if (words/word) 
                    then string-join((.//word/item[@type='txt' and @lang='enf']),' ') 
                    else '((…)).'"/>
            </item>
            <xsl:apply-templates select="*"/>
        </xsl:copy>
    </xsl:template>
    
</xsl:stylesheet>