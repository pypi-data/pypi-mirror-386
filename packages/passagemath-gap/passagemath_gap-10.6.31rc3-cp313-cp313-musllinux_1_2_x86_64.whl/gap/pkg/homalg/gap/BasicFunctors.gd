# SPDX-License-Identifier: GPL-2.0-or-later
# homalg: A homological algebra meta-package for computable Abelian categories
#
# Declarations
#

##  Declarations for basic functors.

####################################
#
# global variables:
#
####################################

####################################
#
# attributes:
#
####################################

##  <#GAPDoc Label="CokernelEpi">
##  <ManSection>
##    <Attr Arg="phi" Name="CokernelEpi" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural epimorphism from the <C>Range</C><M>(</M><A>phi</A><M>)</M>
##      onto the <C>Cokernel</C><M>(</M><A>phi</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "CokernelEpi",
        IsHomalgMorphism );

##  <#GAPDoc Label="CokernelNaturalGeneralizedIsomorphism">
##  <ManSection>
##    <Attr Arg="phi" Name="CokernelNaturalGeneralizedIsomorphism" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural generalized isomorphism from the <C>Cokernel</C><M>(</M><A>phi</A><M>)</M>
##      onto the <C>Range</C><M>(</M><A>phi</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "CokernelNaturalGeneralizedIsomorphism",
        IsHomalgMorphism );

##  <#GAPDoc Label="KernelEmb">
##  <ManSection>
##    <Attr Arg="phi" Name="KernelEmb" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural embedding of the <C>Kernel</C><M>(</M><A>phi</A><M>)</M>
##      into the <C>Source</C><M>(</M><A>phi</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "KernelEmb",
        IsHomalgMorphism );

##  <#GAPDoc Label="ImageObjectEmb">
##  <ManSection>
##    <Attr Arg="phi" Name="ImageObjectEmb" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural embedding of the <C>ImageObject</C><M>(</M><A>phi</A><M>)</M>
##      into the <C>Range</C><M>(</M><A>phi</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "ImageObjectEmb",
        IsHomalgMorphism );

##  <#GAPDoc Label="ImageObjectEpi">
##  <ManSection>
##    <Attr Arg="phi" Name="ImageObjectEpi" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural epimorphism from the <C>Source</C><M>(</M><A>phi</A><M>)</M>
##      onto the <C>ImageObject</C><M>(</M><A>phi</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "ImageObjectEpi",
        IsHomalgMorphism );

##  <#GAPDoc Label="NatTrIdToHomHom_R">
##  <ManSection>
##    <Attr Arg="M" Name="NatTrIdToHomHom_R" Label="for morphisms"/>
##    <Returns>a &homalg; morphism</Returns>
##    <Description>
##      The natural evaluation morphism from the &homalg; object <A>M</A>
##      to its double dual <C>HomHom</C><M>(</M><A>M</A><M>)</M>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
DeclareAttribute( "NatTrIdToHomHom_R",
        IsHomalgObject );

####################################
#
# global functions and operations:
#
####################################

# basic operations:

DeclareOperation( "Cokernel",
        [ IsHomalgMorphism ] );

DeclareAttribute( "ImageObject",
        IsHomalgMorphism );

## Kernel is already declared in the GAP library via DeclareOperation("Kernel",[IsObject]); (why so general?)

DeclareOperation( "DefectOfExactness",
        [ IsHomalgComplex ] );

DeclareOperation( "DefectOfExactness",
        [ IsHomalgMorphism, IsHomalgMorphism ] );

DeclareOperation( "Hom",
        [ IsHomalgObject, IsHomalgObject ] );

DeclareOperation( "Ext",
        [ IsInt, IsHomalgObject, IsHomalgObject ] );

DeclareOperation( "InternalHom",
        [ IsHomalgObjectOrMorphism, IsHomalgObjectOrMorphism ] );

DeclareOperation( "InternalHom",
        [ IsHomalgObjectOrMorphism ] );

DeclareOperation( "InternalExt",
        [ IsInt, IsHomalgObjectOrMorphism, IsHomalgObjectOrMorphism ] );

DeclareOperation( "InternalExt",
        [ IsHomalgObjectOrMorphism, IsHomalgObjectOrMorphism ] );

DeclareOperation( "InternalExt",
        [ IsInt, IsHomalgObjectOrMorphism ] );

DeclareOperation( "InternalExt",
        [ IsHomalgObjectOrMorphism ] );

DeclareOperation( "Tor",
        [ IsInt, IsHomalgObject, IsHomalgObject ] );

DeclareOperation( "LeftDualizingFunctor",
        [ IsStructureObject, IsString ] );

DeclareOperation( "LeftDualizingFunctor",
        [ IsStructureObject ] );

DeclareOperation( "RightDualizingFunctor",
        [ IsStructureObject, IsString ] );

DeclareOperation( "RightDualizingFunctor",
        [ IsStructureObject ] );

DeclareOperation( "Dualize",
        [ IsStructureObjectOrObjectOrMorphism ] );

DeclareOperation( "TensorProductOp",
        [ IsList, IsStructureObjectOrObjectOrMorphism ] );

DeclareOperation( "BaseChange",
        [ IsStructureObject, IsHomalgStaticObject ] );

####################################
#
# synonyms:
#
####################################

DeclareSynonym( "DefectOfHoms",
        DefectOfExactness );
