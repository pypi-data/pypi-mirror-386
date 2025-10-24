# SPDX-License-Identifier: GPL-2.0-or-later
# RingsForHomalg: Dictionaries of external rings
#
# Implementations
#

##  Implementations for the rings provided by the ring packages
##  of the Maple implementation of homalg.

####################################
#
# global variables:
#
####################################

BindGlobal( "CommonHomalgTableForMapleHomalgTools",
        
        rec(
               Zero := HomalgExternalRingElement( function( R ) homalgSendBlocking( [ "`homalg/homalg_options`(", R, "[-1])" ], "need_command", "initialize" );
                                                                return homalgSendBlocking( [ R, "[-1][Zero]()" ], "Zero" ); end, "Maple", IsZero ),
               
               One := HomalgExternalRingElement( R -> homalgSendBlocking( [ R, "[-1][One]" ], "One" ), "Maple", IsOne ),
               
               MinusOne := HomalgExternalRingElement( R -> homalgSendBlocking( [ R, "[-1][Minus](", Zero( R ), One( R ), R, "[1])" ], "MinusOne" ), "Maple", IsMinusOne ),
               
               ## ring elements in Maple do not know their ring,
               ## this is a source of bugs: 1+1=2<>0 in char 2;
               ## so avoid using ring arithmetics in Maple
               RingElement := R -> r -> homalgSendBlocking( [ r ], R, "define" ),
               
               IsZero := r -> homalgSendBlocking( [ "evalb( ", r, " = ",  Zero( r ), " )" ] , "need_output", "IsZero" ) = "true",
               
               IsOne := r -> homalgSendBlocking( [ "evalb( ", r, " = ",  One( r ), " )" ] , "need_output", "IsOne" ) = "true",
               
               Minus :=
                 function( a, b )
                   local R;
                   
                   R := HomalgRing( a );
                   
                   return homalgSendBlocking( [ R, "[-1][Minus](", a, ",", b, ",", R, "[1])" ], "Minus" ); ## do not delete "," in case a and b are passed as strings
                   
                 end,
               
               DivideByUnit :=
                 function( a, u )
                   local R;
                   
                   R := HomalgRing( a );
                   
                   return homalgSendBlocking( [ R, "[-1][DivideByUnit](", a, ",", u, ",", R, "[1])" ], "DivideByUnit" ); ## do not delete "," in case a and b are passed as strings
                   
                 end,
               
               IsUnit :=
                 function( R, r )
                   
                   return homalgSendBlocking( [ "evalb( `homalg/InverseElement`(", r, R, ") <> FAIL )" ], "need_output", "IsUnit" ) = "true";
                   
                 end,
               
               Gcd :=
                 function( a, b )
                   
                   return homalgSendBlocking( [ "gcd(", a, ",", b, ")" ], "Gcd" ); ## do not delete "," in case a and b are passed as strings
                   
                 end,
               
               CancelGcd :=
                 function( a, b )
                   local a_g, b_g;
                   
                   homalgSendBlocking( [ "g := gcd(", a, ",", b, ")" ], "need_command", "Gcd" ); ## do not delete "," in case a and b are passed as strings
                   a_g := homalgSendBlocking( [ "normal((", a, ") / g)" ], "CancelGcd" );
                   b_g := homalgSendBlocking( [ "normal((", b, ") / g)" ], "CancelGcd" );
                   
                   return [ a_g, b_g ];
                   
                 end,
               
               LaTeXString :=
                 function( poly )
                    local l;
                    
                    l := homalgSendBlocking( [ "latex(", poly, ")" ], "need_display", "homalgLaTeX" );
                    
                    RemoveCharacters( l, "$" );
                    
                    return l;
                    
                end,
               
               ShallowCopy := C -> homalgSendBlocking( [ "copy( ", C, " )" ], "CopyMatrix" ),
               
               CopyMatrix :=
                 function( C, R )
                   
                   return homalgSendBlocking( [ R, "[-1][matrix](copy( ", C, " ))" ], "CopyMatrix" );
                   
                 end,
               
               ZeroMatrix :=
                 function( C )
                   local R;
                   
                   R := HomalgRing( C );
                   
                   return homalgSendBlocking( [ "`homalg/ZeroMap`(", NumberRows( C ), NumberColumns( C ), R, ")" ], "ZeroMatrix" );
                   
                 end,
               
               IdentityMatrix :=
                 function( C )
                   local R;
                   
                   R := HomalgRing( C );
                   
                   return homalgSendBlocking( [ "`homalg/IdentityMap`(", NumberRows( C ), R, ")" ], "IdentityMatrix" );
                   
                 end,
               
               AreEqualMatrices :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "linalg[iszero](`homalg/SubMat`(", A, B, R, "))" ], "need_output" , "AreEqualMatrices" ) = "true";
                   
                 end,
               
               Involution :=
                 function( M )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return homalgSendBlocking( [ "`homalg/Involution`(", M, R, ")" ], "Involution" );
                   
                 end,
               
               CertainRows :=
                 function( M, plist )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return homalgSendBlocking( [ R, "[-1][CertainRows](", M, plist, ")" ], "CertainRows" );
                   
                 end,
               
               CertainColumns :=
                 function( M, plist )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return homalgSendBlocking( [ R, "[-1][CertainColumns](", M, plist, ")" ], "CertainColumns" );
                   
                 end,
               
               UnionOfRowsPair :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ R, "[-1][matrix](", R, "[-1][UnionOfRows](", A, B, "))" ], "UnionOfRows" );
                   
                 end,
               
               UnionOfColumnsPair :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ R, "[-1][matrix](", R, "[-1][UnionOfColumns](", A, B, "))" ], "UnionOfColumns" );
                   
                 end,
               
               DiagMat :=
                 function( e )
                   local R, f;
                   
                   R := HomalgRing( e[1] );
                   
                   f := Concatenation( [ "`homalg/DiagMat`(" ], e, [ R, "[-1])" ] );
                   
                   return homalgSendBlocking( f, "DiagMat" );
                   
                 end,
               
               KroneckerMat :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "`homalg/KroneckerMat`(", A, B, R, ")" ], "KroneckerMat" );
                   
                 end,
               
               MulMat :=
                 function( a, A )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "`homalg/MulMat`(", a, A, R, ")" ], "MulMat" );
                   
                 end,
               
               AddMat :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "`homalg/AddMat`(", A, B, R, ")" ], "AddMat" );
                   
                 end,
               
               SubMat :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "`homalg/SubMat`(", A, B, R, ")" ], "SubMat" );
                   
                 end,
               
               Compose :=
                 function( A, B )
                   local R;
                   
                   R := HomalgRing( A );
                   
                   return homalgSendBlocking( [ "`homalg/Compose`(", A, B, R, ")" ], "Compose" );
                   
                 end,
               
               NumberRows :=
                 function( C )
                   local R;
                   
                   R := HomalgRing( C );
                   
                   return StringToInt( homalgSendBlocking( [ R, "[-1][NumberOfRows](", C, ")" ], "need_output", "NumberRows" ) );
                   
                 end,
               
               NumberColumns :=
                 function( C )
                   local R;
                   
                   R := HomalgRing( C );
                   
                   return StringToInt( homalgSendBlocking( [ R, "[-1][NumberOfGenerators](", C, ")" ], "need_output", "NumberColumns" ) );
                   
                 end,
               
               Determinant :=
                 function( C )
                   
                   return homalgSendBlocking( [ "linalg[det](", C, ")" ], "Determinant" );
                   
                 end,
               
               IsZeroMatrix :=
                 function( M )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return homalgSendBlocking( [ "linalg[iszero](`homalg/ReduceRingElements`(", M, R, "))" ], "need_output", "IsZeroMatrix" ) = "true";
                   
                 end,
               
               ZeroRows :=
                 function( C )
                   local R, list_string;
                   
                   R := HomalgRing( C );
                   
                   list_string := homalgSendBlocking( [ "`homalg/ZeroRows`(", C, R, ")" ], "need_output", "ZeroRows" );
                   return StringToIntList( list_string );
                   
                 end,
               
               ZeroColumns :=
                 function( C )
                   local R, list_string;
                   
                   R := HomalgRing( C );
                   
                   list_string := homalgSendBlocking( [ "`homalg/ZeroColumns`(", C, R, ")" ], "need_output", "ZeroColumns" );
                   return StringToIntList( list_string );
                   
                 end,
               
               GetColumnIndependentUnitPositions :=
                 function( M, pos_list )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return StringToDoubleIntList( homalgSendBlocking( [ "`homalg/GetColumnIndependentUnitPositions`(", M, pos_list, R, ")" ], "need_output", "GetColumnIndependentUnitPositions" ) );
                   
                 end,
               
               GetRowIndependentUnitPositions :=
                 function( M, pos_list )
                   local R;
                   
                   R := HomalgRing( M );
                   
                   return StringToDoubleIntList( homalgSendBlocking( [ "`homalg/GetRowIndependentUnitPositions`(", M, pos_list, R, ")" ], "need_output", "GetRowIndependentUnitPositions" ) );
                   
                 end,
               
               GetUnitPosition :=
                 function( M, pos_list )
                   local R, list_string;
                   
                   R := HomalgRing( M );
                   
                   list_string := homalgSendBlocking( [ "`homalg/GetUnitPosition`(", M, pos_list, R, ")" ], "need_output", "GetUnitPosition" );
                   
                   if list_string = "" then
                       return fail;
                   else
                       return StringToIntList( list_string );
                   fi;
                   
                 end,
               
               GetCleanRowsPositions :=
                 function( M, clean_columns )
                   local R, list_string;
                   
                   R := HomalgRing( M );
                   
                   list_string := homalgSendBlocking( [ "`homalg/GetCleanRowsPositions`(", M, clean_columns, R, ")" ], "need_output", "GetCleanRowsPositions" );
                   
                   if list_string = "" then
                       return [ ];
                   else
                       return StringToIntList( list_string );
                   fi;
                   
                 end,
               
               ConvertRowToTransposedMatrix :=
                 function( M, r, c )
                   local R;
                   
                   R := HomalgRing( M );

                   ## `homalg/ConvertRowToMatrix` is correct
                   return homalgSendBlocking( [ "`homalg/ConvertRowToMatrix`(", M, r, c, R, ")" ], "ConvertRowToMatrix" );
                   
                 end,
               
               ConvertColumnToTransposedMatrix :=
                 function( M, r, c )
                   local R;
                   
                   R := HomalgRing( M );

                   ## `homalg/ConvertColumnToMatrix` is correct
                   return homalgSendBlocking( [ "`homalg/ConvertColumnToMatrix`(", M, r, c, R, ")" ], "ConvertColumnToMatrix" );
                   
                 end,
                
               CoefficientsOfUnreducedNumeratorOfHilbertPoincareSeries :=
                 function( mat )
                   local R, n, s, hilb;
                   
                   R := HomalgRing( mat );
                   
                   n := Length( Indeterminates( R ) );
                   
                   s := "'homalg_variable_for_HP'";
                   
                   hilb := homalgSendBlocking( [ "CoefficientsOfUnreducedNumeratorOfHilbertPoincareSeries(", mat, R, "[1],", s, ",", n, ")"  ], "need_output", "HilbertPoincareSeries" );
                   
                   return StringToIntList( hilb );
                   
                 end,
                
               CoefficientsOfUnreducedNumeratorOfWeightedHilbertPoincareSeries :=
                 function( mat, weights, degrees )
                   local R, var, var_string, s, denom, hilb;
                   
                   R := HomalgRing( mat );
                   
                   var := Indeterminates( R );
                   
                   var_string := ListN( var, weights,
                                        function( v, w ) return Concatenation( String( v ), "=", String( w ) ); end );
                   
                   Append( var_string,
                           ListN( [ 1 .. NumberColumns( mat ) ], degrees,
                                  function( i, d ) return Concatenation( String( i ), "=", String( d ) ); end ) );
                   
                   var_string := JoinStringsWithSeparator( var_string );
                   
                   s := "'homalg_variable_for_HP'";
                   
                   denom := List( weights, i -> Concatenation( "(1-", s, "^", String( i ), ")" ) );
                   
                   denom := JoinStringsWithSeparator( denom, "*" );
                   
                   hilb := homalgSendBlocking( [ "CoefficientsOfUnreducedNumeratorOfWeightedHilbertPoincareSeries(", mat, ",[", var_string, "],", s, ",", denom, ")"  ], "need_output", "HilbertPoincareSeries" );
                   
                   return StringToIntList( hilb );
                   
                 end,
               
               Eliminate :=
                 function( rel, indets, R )
                   
                   return homalgSendBlocking( [ R, "[-1][matrix](map(a->[a],Eliminate(", rel, indets, R, "[1])))" ], "Eliminate" );
                   
                 end,
               
               Coefficients :=
                 function( poly, var )
                   local R, v, vars, coeffs;
                   
                   R := HomalgRing( poly );
                   
                   v := homalgStream( R )!.variable_name;
                   
                   homalgSendBlocking( [ v, "m := coeffs(sort(collect(", poly, ",", var, ",'distributed')),", var, ",'", v, "t')" ], "need_command", "Coefficients" );
                   vars := homalgSendBlocking( [ R, "[-1][matrix](map(a->[a],MyReverse([", v, "t])))"  ], R, "Coefficients" );
                   coeffs := homalgSendBlocking( [ R, "[-1][matrix](map(a->[a],MyReverse([", v, "m])))" ], R, "Coefficients" );
                   
                   return [ vars, coeffs ];
                   
                 end,
               
               DegreeOfRingElement :=
                 function( r, R )
                   local deg;
                   
                   if IsBound( R!.AssociatedPolynomialRing ) then
                       return Degree( r / R!.AssociatedPolynomialRing );
                   fi;
                   
                   deg := Int( homalgSendBlocking( [ "degree( ", r, " )" ], "need_output", "DegreeOfRingElement" ) );
                   
                   if deg <> fail then
                       return deg;
                   fi;
                   
                   return -1;
                   
                 end,
               
               CoefficientsOfUnivariatePolynomial :=
                 function( r, var )
                   local R;
                   
                   R := HomalgRing( r );
                   
                   return homalgSendBlocking( [ R, "[-1][matrix]([CoefficientsOfPolynomial(", r, var, ")])" ], "Coefficients" );
                   
                 end,
               
               MonomialMatrix :=
                 function( i, vars, R )
                   
                   return homalgSendBlocking( [ "`homalg/MonomialMatrix`(", i, vars, R, ")" ], "MonomialMatrix" );
                   
                 end,
               
               NumeratorAndDenominatorOfPolynomial :=
                 function( p )
                   local R, v, numer, denom;
                   
                   R := HomalgRing( p );
                   
                   v := homalgStream( R )!.variable_name;
                   
                   homalgSendBlocking( [ v, "p:=simplify(", p, ")" ], "need_command", "Numerator" );
                   
                   numer := homalgSendBlocking( [ "numer(", v, "p)" ], R, "Numerator" );
                   denom := homalgSendBlocking( [ "denom(", v, "p)" ], R, "Numerator" );
                   
                   numer := HomalgExternalRingElement( numer, R );
                   denom := HomalgExternalRingElement( denom, R );
                   
                   return [ numer, denom ];
                   
                 end,
               
        )
 );
