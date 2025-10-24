# SPDX-License-Identifier: GPL-2.0-or-later
# homalg: A homological algebra meta-package for computable Abelian categories
#
# Reading the implementation part of the package.
#

## init
ReadPackage( "homalg", "gap/homalg.gi" );

## categories
ReadPackage( "homalg", "gap/HomalgCategory.gi" );

## objects/subobjects
ReadPackage( "homalg", "gap/HomalgObject.gi" );
ReadPackage( "homalg", "gap/HomalgSubobject.gi" );

## morphisms
ReadPackage( "homalg", "gap/HomalgMorphism.gi" );

## elements
ReadPackage( "homalg", "gap/HomalgElement.gi" );

## filtrations
ReadPackage( "homalg", "gap/HomalgFiltration.gi" );

## complexes
ReadPackage( "homalg", "gap/HomalgComplex.gi" );

## chain maps
ReadPackage( "homalg", "gap/HomalgChainMorphism.gi" );

## bicomplexes
ReadPackage( "homalg", "gap/HomalgBicomplex.gi" );

## bigraded objects
ReadPackage( "homalg", "gap/HomalgBigradedObject.gi" );

## spectral sequences
ReadPackage( "homalg", "gap/HomalgSpectralSequence.gi" );

## functors
ReadPackage( "homalg", "gap/HomalgFunctor.gi" );

## diagrams
ReadPackage( "homalg", "gap/HomalgDiagram.gi" );

## main
ReadPackage( "homalg", "gap/StaticObjects.gi" );

ReadPackage( "homalg", "gap/Morphisms.gi" );

ReadPackage( "homalg", "gap/Complexes.gi" );

ReadPackage( "homalg", "gap/ChainMorphisms.gi" );

ReadPackage( "homalg", "gap/SpectralSequences.gi" );

ReadPackage( "homalg", "gap/Filtrations.gi" );

ReadPackage( "homalg", "gap/BasicFunctors.gi" );
ReadPackage( "homalg", "gap/OtherFunctors.gi" );
ReadPackage( "homalg", "gap/ToolFunctors.gi" );

## LogicForHomalg subpackages
ReadPackage( "homalg", "gap/LIOBJ.gi" );
ReadPackage( "homalg", "gap/LIMOR.gi" );
ReadPackage( "homalg", "gap/LICPX.gi" );
ReadPackage( "homalg", "gap/LICHM.gi" );

if IsBound( MakeThreadLocal ) then
    Perform(
            [
             "HOMALG",
             "LIOBJ",
             "LogicalImplicationsForHomalgStaticObjects",
             "LIMOR",
             "LogicalImplicationsForHomalgMorphisms",
             "LogicalImplicationsForHomalgEndomorphisms",
             "LICPX",
             "LogicalImplicationsForHomalgComplexes",
             "LICHM",
             "LogicalImplicationsForHomalgChainMorphisms",
             ],
            MakeThreadLocal );
fi;
