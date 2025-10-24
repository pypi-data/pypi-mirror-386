# SPDX-License-Identifier: GPL-2.0-or-later
# GradedRingForHomalg: Endow Commutative Rings with an Abelian Grading
#
# Implementations
#

####################################
#
# global variables:
#
####################################

##
InstallValue( GradedRingMacrosForSingular,
        rec(
            
    _CAS_name := "Singular",
    
    _Identifier := "GradedRingForHomalg",
    
    MultiDeg := "\n\
proc MultiDeg (pol,weights)\n\
{\n\
  int mul=size(weights);\n\
  intmat m[1][mul];\n\
  for (int i=1; i<=mul; i++)\n\
  {\n\
    m[1,i]=Deg(pol,weights[i]);\n\
  }\n\
  return(m);\n\
}\n\n",

    MultiDegOfMatrixEntry := "\n\
proc MultiDegOfMatrixEntry (matrix M,weights,row,col)\n\
{\n\
  int mul=size(weights);\n\
  intmat m[1][mul];\n\
  for (int i=1; i<=mul; i++)\n\
  {\n\
    m[1,i]=Deg(M[row,col],weights[i]);\n\
  }\n\
  return(m);\n\
}\n\n",
    
    DegreesOfEntries := "\n\
proc DegreesOfEntries (matrix M)\n\
{\n\
  intmat m[ncols(M)][nrows(M)];\n\
  for (int i=1; i<=ncols(M); i++)\n\
  {\n\
    for (int j=1; j<=nrows(M); j++)\n\
    {\n\
      m[i,j] = deg(M[j,i]);\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
    
    WeightedDegreesOfEntries := "\n\
proc WeightedDegreesOfEntries (matrix M, weights)\n\
{\n\
  intmat m[ncols(M)][nrows(M)];\n\
  for (int i=1; i<=ncols(M); i++)\n\
  {\n\
    for (int j=1; j<=nrows(M); j++)\n\
    {\n\
      m[i,j] = Deg(M[j,i],weights);\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
        
    NonTrivialDegreePerRowWithColPosition := "\n\
proc NonTrivialDegreePerRowWithColPosition(matrix M)\n\
{\n\
  intmat m[2][ncols(M)];\n\
  poly e;\n\
  for (int i=1; i<=ncols(M); i++)\n\
  {\n\
    for (int j=1; j<=nrows(M); j++)\n\
    {\n\
      e = M[j,i];\n\
      if ( e <> 0 ) { m[1,i] = deg(e); m[2,i] = j; break; }\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
    
    NonTrivialWeightedDegreePerRowWithColPosition := "\n\
proc NonTrivialWeightedDegreePerRowWithColPosition(matrix M, weights)\n\
{\n\
  intmat m[2][ncols(M)];\n\
  poly e;\n\
  for (int i=1; i<=ncols(M); i++)\n\
  {\n\
    for (int j=1; j<=nrows(M); j++)\n\
    {\n\
      e = M[j,i];\n\
      if ( e <> 0 ) { m[1,i] = Deg(e,weights); m[2,i] = j; break; }\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
    
    NonTrivialDegreePerColumnWithRowPosition := "\n\
proc NonTrivialDegreePerColumnWithRowPosition (matrix M)\n\
{\n\
  intmat m[2][nrows(M)];\n\
  poly e;\n\
  for (int j=1; j<=nrows(M); j++)\n\
  {\n\
    for (int i=1; i<=ncols(M); i++)\n\
    {\n\
      e = M[j,i];\n\
      if ( e <> 0 ) { m[1,j] = deg(e); m[2,j] = i; break; }\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
    
    NonTrivialWeightedDegreePerColumnWithRowPosition := "\n\
proc NonTrivialWeightedDegreePerColumnWithRowPosition (matrix M, weights)\n\
{\n\
  intmat m[2][nrows(M)];\n\
  poly e;\n\
  for (int j=1; j<=nrows(M); j++)\n\
  {\n\
    for (int i=1; i<=ncols(M); i++)\n\
    {\n\
      e = M[j,i];\n\
      if ( e <> 0 ) { m[1,j] = Deg(e,weights); m[2,j] = i; break; }\n\
    }\n\
  }\n\
  return(m);\n\
}\n\n",
    
    ("#LinSyzForHomalg") := "\n\
proc LinSyzForHomalg(matrix m)\n\
{\n\
  def save=degBound;\n\
  degBound=1; // it will be a disaster if degBound=0 below is not reached\n\
  def r = res(m,2);\n\
  degBound=save; // puh ... \n\
  return(r[2]);\n\
}\n\n",
    
    LinearSyzygiesGeneratorsOfRows := "\n\
proc LinearSyzygiesGeneratorsOfRows(m)\n\
{\n\
  return(LinSyzForHomalg(m))\n\
}\n\n",
    
    LinearSyzygiesGeneratorsOfColumns := "\n\
proc LinearSyzygiesGeneratorsOfColumns(m)\n\
{\n\
  return(Involution(LinSyzForHomalg(Involution(m))));\n\
}\n\n",
    
    ("$CheckLinExtSyz") := "\n\
// start: check degBound in SCA:\n\
if ( defined( basering ) != 0 )\n\
{\n\
  def homalg_variable_basering = basering;\n\
}\n\
ring homalg_Exterior_1 = 0,(e0,e1),dp;\n\
def homalg_Exterior_2 = superCommutative_ForHomalg(1);\n\
setring homalg_Exterior_2;\n\
option(redTail);short=0;\n\
matrix homalg_Exterior_3[3][2] = e0,0,e1,e0,0,e1;\n\
matrix homalg_Exterior_4=LinSyzForHomalg(homalg_Exterior_3);\n\
if (ncols(homalg_Exterior_4) == 1 && homalg_Exterior_4[1,1] <> 0 && homalg_Exterior_4[2,1] <> 0)\n\
{\n\
  def LinSyzForHomalgExterior = 1;\n\
}\n\
kill homalg_Exterior_4; kill homalg_Exterior_3; kill homalg_Exterior_2; kill homalg_Exterior_1;\n\
if ( defined( homalg_variable_basering ) != 0 )\n\
{\n\
  setring homalg_variable_basering;\n\
}\n\
// end: check degBound in SCA.\n\
\n\n",
    
    )

);

##
UpdateMacrosOfCAS( GradedRingMacrosForSingular, SingularMacros );
UpdateMacrosOfLaunchedCASs( GradedRingMacrosForSingular );

##
InstallValue( GradedRingTableForSingularTools,
        
        rec(
               WeightedDegreeOfRingElement :=
                 function( r, weights, R )
                   
                   return Int( homalgSendBlocking( [ "deg( ", r, ",intvec(", weights, "))" ], "need_output", HOMALG_IO.Pictograms.DegreeOfRingElement ) );
                   
                 end,
               
               MultiWeightedDegreeOfRingElement :=
                 function( r, weights, R )
                   
                   if IsList( weights ) then
                       
                       weights := MatrixOfWeightsOfIndeterminates( R, weights );
                       
                   fi;
                   
                   return StringToIntList( homalgSendBlocking( [ "MultiDeg(", r, weights, ")" ], "need_output", HOMALG_IO.Pictograms.DegreeOfRingElement ) );
                   
                 end,
               
               DegreesOfEntries :=
                 function( M )
                   local list_string, L;
                   
                   list_string := homalgSendBlocking( [ "DegreesOfEntries( ", M, " )" ], "need_output", HOMALG_IO.Pictograms.DegreesOfEntries );
                   
                   L :=  StringToIntList( list_string );
                   
                   return ListToListList( L, NumberRows( M ), NumberColumns( M ) );
                   
                 end,
               
               WeightedDegreesOfEntries :=
                 function( M, weights )
                   local list_string, L;
                   
                     list_string := homalgSendBlocking( [ "WeightedDegreesOfEntries(", M, ",intvec(", weights, "))" ], "need_output", HOMALG_IO.Pictograms.DegreesOfEntries );
                     
                     L :=  StringToIntList( list_string );
                     
                     return ListToListList( L, NumberRows( M ), NumberColumns( M ) );
                     
                 end,
                 
#                MultiWeightedDegreesOfEntries :=
#                  function( M, weights, R )
#                    local nr_rows, nr_cols, i, j, deg_mat;
#                    
#                    nr_rows := NumberRows( M );
#                    nr_cols := NumberColumns( M );
#                    
#                    deg_mat := NullMat( nr_rows, nr_cols );
#                    
#                    for i in [ 1 .. nr_rows ] do
#                        for j in [ 1 .. nr_cols ] do
#                            deg_mat[ i ][ j ] := StringToIntList( homalgSendBlocking( [ "MultiDegOfMatrixEntry(", M, weights, j, i, ")" ], "need_output", HOMALG_IO.Pictograms.DegreeOfRingElement ) );
#                         od;
#                     od;
#                     
#                     return deg_mat;
#                     
#                 end,
               
               NonTrivialDegreePerRowWithColPosition :=
                 function( M )
                   local L;
                   
                   L := homalgSendBlocking( [ "NonTrivialDegreePerRowWithColPosition( ", M, " )" ], "need_output", HOMALG_IO.Pictograms.NonTrivialDegreePerRow );
                   
                   L := StringToIntList( L );
                   
                   return ListToListList( L, 2, NumberRows( M ) );
                   
                 end,
               
               NonTrivialWeightedDegreePerRowWithColPosition :=
                 function( M, weights )
                   local L;
                   
                   L := homalgSendBlocking( [ "NonTrivialWeightedDegreePerRowWithColPosition(", M, ",intvec(", weights, "))" ], "need_output", HOMALG_IO.Pictograms.NonTrivialDegreePerRow );
                   
                   L := StringToIntList( L );
                   
                   return ListToListList( L, 2, NumberRows( M ) );
                   
                 end,
               
               NonTrivialDegreePerColumnWithRowPosition :=
                 function( M )
                   local L;
                   
                   L := homalgSendBlocking( [ "NonTrivialDegreePerColumnWithRowPosition( ", M, " )" ], "need_output", HOMALG_IO.Pictograms.NonTrivialDegreePerColumn );
                   
                   L := StringToIntList( L );
                   
                   return ListToListList( L, 2, NumberColumns( M ) );
                   
                 end,
               
               NonTrivialWeightedDegreePerColumnWithRowPosition :=
                 function( M, weights )
                   local L;
                   
                   L := homalgSendBlocking( [ "NonTrivialWeightedDegreePerColumnWithRowPosition(", M, ",intvec(", weights, "))" ], "need_output", HOMALG_IO.Pictograms.NonTrivialDegreePerColumn );
                   
                   L := StringToIntList( L );
                   
                   return ListToListList( L, 2, NumberColumns( M ) );
                   
                 end,
               
               LinearSyzygiesGeneratorsOfRows :=
                 function( M )
                   local N;
                   
                   N := HomalgVoidMatrix(
                                "unknown_number_of_rows",
                                NumberRows( M ),
                                HomalgRing( M )
                                );
                   
                   homalgSendBlocking(
                           [ "matrix ", N, " = LinearSyzygiesGeneratorsOfRows(", M, ")" ],
                           "need_command",
                           HOMALG_IO.Pictograms.LinearSyzygiesGenerators
                           );
                   
                   return N;
                   
                 end,
               
               LinearSyzygiesGeneratorsOfColumns :=
                 function( M )
                   local N;
                   
                   N := HomalgVoidMatrix(
                                NumberColumns( M ),
                                "unknown_number_of_columns",
                                HomalgRing( M )
                                );
                   
                   homalgSendBlocking(
                           [ "matrix ", N, " = LinearSyzygiesGeneratorsOfColumns(", M, ")" ],
                           "need_command",
                           HOMALG_IO.Pictograms.LinearSyzygiesGenerators
                           );
                   
                   return N;
                   
                 end,
               
        )
 );

## enrich the global and the created homalg tables for Singular:
AppendToAhomalgTable( CommonHomalgTableForSingularTools, GradedRingTableForSingularTools );
AppendTohomalgTablesOfCreatedExternalRings( GradedRingTableForSingularTools, IsHomalgExternalRingInSingularRep );

####################################
#
# methods for operations:
#
####################################

##
InstallOtherMethod( HomalgQRingInSingular,
        "constructor for homalg rings",
        [ IsHomalgGradedRingRep, IsHomalgRingRelations ],
        
  function( S, ring_rel )
    local R, RR, result, A;
    
    R := UnderlyingNonGradedRing( S );
    
    RR := HomalgQRingInSingular( R, R * ring_rel );
    
    result := GradedRing( RR : pre_graded_ring := true );
    
    if HasContainsAField( S ) and ContainsAField( S ) then
        SetContainsAField( result, true );
        if HasCoefficientsRing( S ) then
            SetCoefficientsRing( result, CoefficientsRing( S ) );
        fi;
    fi;
    
    if HasAmbientRing( S ) then
        A := AmbientRing( S );
    elif HasAmbientRing( R ) then
        A := GradedRing( AmbientRing( R ) );
    else
        A := S;
    fi;
    
    SetAmbientRing( result, A );
    SetRingRelations( result, A * RingRelations( RR ) );
    
    return result;
    
end );

##
InstallOtherMethod( HomalgQRingInSingular,
        "constructor for homalg rings",
        [ IsHomalgGradedRingRep and HasAmbientRing ],
        
  function( S )
    
    return HomalgQRingInSingular( AmbientRing( S ), RingRelations( S ) );
    
end );

##
InstallMethod( MatrixOfWeightsOfIndeterminates,
        "for external rings in Singular",
        [ IsHomalgExternalRingInSingularRep, IsList ],
        
  function( R, weights )
    local n, m, ext_obj;
    
    if IsHomalgElement( weights[1] ) then
        
        ## this should be handled with care, as it will eventually fail if the module is not over the ring of integers
        weights := List( weights, UnderlyingListOfRingElementsInCurrentPresentation );
        
    fi;
    
    n := Length( weights );
    
    if n > 0 and IsList( weights[1] ) then
        m := Length( weights[1] );
        weights := Flat( TransposedMat( weights ) );
    else
        m := 1;
    fi;
    
    ext_obj := homalgSendBlocking( [ "CreateListListOfIntegers(intvec(", weights, "),", m, n, ")"  ], [ "list" ], R, HOMALG_IO.Pictograms.CreateList );
    
    ## CAUTION: ext_obj is not a pointer to a matrix in Singular but to an intvec;
    ## use with care
    return HomalgMatrix( ext_obj, m, n, R );
    
end );

##
InstallMethod( AreLinearSyzygiesAvailable,
        "for homalg rings in Singular",
        [ IsHomalgExternalRingInSingularRep and IsExteriorRing ],
        
  function( R )
    
    return homalgSendBlocking( "defined(LinSyzForHomalgExterior)",
               "need_output", R, HOMALG_IO.Pictograms.initialize ) = "1";
    
end );
