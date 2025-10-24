# SPDX-License-Identifier: GPL-2.0-or-later
# MatricesForHomalg: Matrices for the homalg project
#
# Reading the implementation part of the package.
#
##
##  Reading the implementation part of the MatricesForHomalg package.
##
#############################################################################

## init
ReadPackage( "MatricesForHomalg", "gap/MatricesForHomalg.gi" );

## rings
ReadPackage( "MatricesForHomalg", "gap/homalgTable.gi" );
ReadPackage( "MatricesForHomalg", "gap/HomalgRing.gi" );

## matrices
ReadPackage( "MatricesForHomalg", "gap/HomalgMatrix.gi" );

## ring maps
ReadPackage( "MatricesForHomalg", "gap/HomalgRingMap.gi" );

## ring relations
ReadPackage( "MatricesForHomalg", "gap/HomalgRingRelations.gi" );

## tools/service/basic
ReadPackage( "MatricesForHomalg", "gap/Tools.gi" );
ReadPackage( "MatricesForHomalg", "gap/Service.gi" );
ReadPackage( "MatricesForHomalg", "gap/Basic.gi" );

## LogicForHomalg subpackages

ReadPackage( "MatricesForHomalg", "gap/LIRNG.gi" );
ReadPackage( "MatricesForHomalg", "gap/LIMAP.gi" );

## NEVER EVER preload LIMAT.gi and COLEM.gi; i.e.
## they must be loaded after Tools.gi, Service.gi, and Basic.gi,
## otherwise the logical methods get a lower rank than the generic ones
ReadPackage( "MatricesForHomalg", "gap/COLEM.gi" );
ReadPackage( "MatricesForHomalg", "gap/LIMAT.gi" );

# This is a backup For LIMAT with the minimal logical requierements
# for empty matrices for the package to be functional.
# do not use, unless you know what you do!
# ReadPackage( "MatricesForHomalg", "gap/LIMATEmp.gi" );

## specific GAP4 internal rings
ReadPackage( "MatricesForHomalg", "gap/Euclidean.gi" );
ReadPackage( "MatricesForHomalg", "gap/Integers.gi" );
#ReadPackage( "MatricesForHomalg", "gap/EDIM.gi" );

## the subpackage ResidueClassRingForHomalg
ReadPackage( "MatricesForHomalg", "gap/ResidueClassRingForHomalg.gi" );
ReadPackage( "MatricesForHomalg", "gap/ResidueClassRing.gi" );
ReadPackage( "MatricesForHomalg", "gap/ResidueClassRingBasic.gi" );
ReadPackage( "MatricesForHomalg", "gap/ResidueClassRingTools.gi" );

if IsBound( MakeThreadLocal ) then
    Perform(
            [
             "HOMALG_MATRICES",
             "LIRNG",
             "LogicalImplicationsForHomalgRings",
             "LogicalImplicationsForHomalgRingElements",
             "HOMALG_RESIDUE_CLASS_RING",
             "CommonHomalgTableForResidueClassRingsBasic",
             "CommonHomalgTableForResidueClassRings",
             "CommonHomalgTableForResidueClassRingsTools",
             ],
            MakeThreadLocal );
fi;

if IsPackageMarkedForLoading( "JuliaInterface", ">= 0.2" ) then
    ReadPackage( "MatricesForHomalg", "gap/Julia.gi" );
fi;
