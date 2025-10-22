<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:map="http://www.w3.org/2005/xpath-functions/map"
    xmlns:inel="http://inel.corpora.uni-hamburg.de"
    exclude-result-prefixes="#all"
    version="3.0">
    <xsl:output method="xml" indent="yes" encoding="utf-8" omit-xml-declaration="no"/>
    <xsl:namespace-alias stylesheet-prefix="#default" result-prefix=""/>
    
    <xsl:param name="folder-in" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step1/'"/>
    <xsl:param name="folder-out" select="'file:///C:/YandexDisk/INEL/lang_Enets/TB2flex/step2/'"/>
    <xsl:param name="filemask" select="'?select=*.eaf'"/>

    <!-- filename for list of replacements in tx and mb tiers -->
    <xsl:param name="replacements-file-tx-mb" select="'replacements-tx-mb.xml'"/>
    <!-- filename for list of replacements in ge tier -->
    <xsl:param name="replacements-file-ge" select="'replacements-ge.xml'"/>
    <!-- filename for list of replacements in ps tier -->
    <xsl:param name="replacements-file-ps" select="'replacements-ps.xml'"/>
    <!-- filename for list of complex replacements mb tier (for two adjacent morphs) -->
    <xsl:param name="replacements-file-complex" select="'replacements-complex.xml'"/>
    
    <xsl:variable name="sourcecollection" select="collection(concat($folder-in,$filemask))"/>
    <xsl:variable name="replace-tx-mb" select="doc($replacements-file-tx-mb)//item" /> 
    <xsl:variable name="replace-ge" select="doc($replacements-file-ge)//item" /> 
    <xsl:variable name="replace-ps" select="doc($replacements-file-ps)//item" /> 
    <xsl:variable name="replace-complex" select="doc($replacements-file-complex)//item" />

    <xsl:key name="morphs" match="TIER[@LINGUISTIC_TYPE_REF='mb-cf-enf']//ANNOTATION" use="REF_ANNOTATION/@ANNOTATION_ID"/>

    <xsl:function name="inel:skip-morph" as="xs:boolean">
        <xsl:param name="ann-id" as="xs:string"/>
        <xsl:param name="top" as="node()"/>
        <xsl:sequence select="if (some $i in $replace-complex satisfies 
            ($i/@action='merge'
            and matches(key('morphs',$ann-id,$top)//ANNOTATION_VALUE/text(),$i/@next))
            and matches(key('morphs',$ann-id,$top)/preceding-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text(),$i/@in)) 
            then true() else false()"/>
    </xsl:function>


    <xsl:function name="inel:replace-complex" as="xs:string">
        <xsl:param name="text-in" as="xs:string" />
        <xsl:param name="text-next" as="xs:string"/>
        <xsl:param name="replacements" as="item()*" />
        <xsl:param name="tier" as="xs:string+" />
        <xsl:variable name="text-out" select="if(count($replacements)>0 and $replacements[1]/@tier=$tier
            and matches($text-in,$replacements[1]/@in) and matches($text-next,$replacements[1]/@next)) 
            then replace($text-in,$replacements[1]/@in,$replacements[1]/@out)
            else $text-in"/>
        <xsl:value-of select="if(count($replacements)>1) 
            then inel:replace-complex($text-out,$text-next,subsequence($replacements,2),$tier)
            else $text-out"/>
    </xsl:function>
    
    <xsl:function name="inel:replace-next" as="xs:string">
        <xsl:param name="text-in" as="xs:string" />
        <xsl:param name="text-prev" as="xs:string"/>
        <xsl:param name="replacements" as="item()*" />
        <xsl:param name="tier" as="xs:string+" />
        <xsl:variable name="text-out" select="if(count($replacements)>0 and $replacements[1]/@tier=$tier
            and $replacements[1]/@action='change'
            and matches($text-prev,$replacements[1]/@in) and matches($text-in,$replacements[1]/@next)) 
            then replace($text-in,$replacements[1]/@next,$replacements[1]/@next-out)
            else $text-in"/>
        <xsl:value-of select="if(count($replacements)>1) 
            then inel:replace-next($text-out,$text-prev,subsequence($replacements,2),$tier)
            else $text-out"/>
    </xsl:function>
    
    <xsl:function name="inel:replace-iter" as="xs:string">
        <xsl:param name="text-in" as="xs:string" />
        <xsl:param name="replacements" as="item()*" />
        <xsl:param name="tier" as="xs:string+" />
        <xsl:variable name="text-out" select="if(count($replacements)>0 and $replacements[1]/@tier=$tier) 
            then replace($text-in,$replacements[1]/@in,$replacements[1]/@out)
            else $text-in"/>
        <xsl:value-of select="if(count($replacements)>1) 
            then inel:replace-iter($text-out,subsequence($replacements,2),$tier)
            else $text-out"/>
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

    <!-- replacements in ps -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='ps-msa-en']//ANNOTATION_VALUE/text()">
        <xsl:value-of select="inel:replace-iter(.,$replace-ps,('ps'))"/>
    </xsl:template>
    
    <!-- replacements in gr -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='gr-gls-ru']//ANNOTATION_VALUE/text()">
        <xsl:variable name="text-next" select="if (ancestor::ANNOTATION/following-sibling::ANNOTATION)
            then ancestor::ANNOTATION/following-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text() 
            else ''"/>
        <xsl:value-of select="inel:replace-complex(.,$text-next,$replace-complex,('gr','ge,gr')) => inel:replace-iter($replace-ge,('gr','ge,gr'))"/>
    </xsl:template>
    
    <!-- replacements in ge -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='ge-gls-en']//ANNOTATION_VALUE/text()">
        <xsl:variable name="text-next" select="if (ancestor::ANNOTATION/following-sibling::ANNOTATION)
            then ancestor::ANNOTATION/following-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text() 
            else ''"/>
        <xsl:variable name="text-prev" select="if (ancestor::ANNOTATION/preceding-sibling::ANNOTATION)
            then ancestor::ANNOTATION/preceding-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text() 
            else ''"/>
        <xsl:value-of select="inel:replace-complex(.,$text-next,$replace-complex,('ge','ge,gr')) 
            => inel:replace-next($text-prev,$replace-complex,'ge')
            => inel:replace-iter($replace-ge,('ge','ge,gr'))"/>
    </xsl:template>
    
    <!-- replacements in mb -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='mb-cf-enf']//ANNOTATION_VALUE/text()">
        <xsl:variable name="text-next" select="if (ancestor::ANNOTATION/following-sibling::ANNOTATION)
            then ancestor::ANNOTATION/following-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text() 
            else ''"/>
        <xsl:variable name="text-prev" select="if (ancestor::ANNOTATION/preceding-sibling::ANNOTATION)
            then ancestor::ANNOTATION/preceding-sibling::ANNOTATION[1]//ANNOTATION_VALUE/text() 
            else ''"/>
        <xsl:value-of select="inel:replace-complex(.,$text-next,$replace-complex,'mb')
            => inel:replace-next($text-prev,$replace-complex,'mb')
            => inel:replace-iter($replace-tx-mb,('mb','tx,mb'))"/>
    </xsl:template>
    
    <!-- skip morphs that must be merged into preceding morph (in mb tier) -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='mb-cf-enf']//ANNOTATION">
        <xsl:if test="not(inel:skip-morph(./REF_ANNOTATION/@ANNOTATION_ID,/))">
            <xsl:copy>
                <xsl:apply-templates select="@*"/>
                <xsl:apply-templates/>
            </xsl:copy>
        </xsl:if>
    </xsl:template>

    <!-- skip morphs that must be merged into preceding morph (referring annotaions in ge, gr and ps tiers) -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF=('ge-gls-en','gr-gls-ru','ps-msa-en')]//ANNOTATION">
        <xsl:if test="not(inel:skip-morph(./REF_ANNOTATION/@ANNOTATION_REF,/))">
            <xsl:copy>
                <xsl:apply-templates select="@*"/>
                <xsl:apply-templates/>
            </xsl:copy>
        </xsl:if>
    </xsl:template>
    
    <!-- replacements in tx -->
    <xsl:template match="TIER[@LINGUISTIC_TYPE_REF='tx-txt-enf']//ANNOTATION_VALUE/text()">
        <xsl:value-of select="inel:replace-iter(.,$replace-tx-mb,('tx','tx,mb'))"/>
    </xsl:template>
</xsl:stylesheet>