# SPDX-License-Identifier: GPL-2.0-or-later
# MatricesForHomalg: Matrices for the homalg project
#
# Implementations
#

####################################
#
# methods for operations:
#
####################################

##  <#GAPDoc Label="BasisOfRows">
##  <ManSection>
##    <Oper Arg="M" Name="BasisOfRows" Label="for matrices"/>
##    <Oper Arg="M, T" Name="BasisOfRows" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="BasisOfRowModule" Label="for matrices"/>.
##      with two arguments it is a synonym of <Ref Oper="BasisOfRowsCoeff" Label="for matrices"/>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( BasisOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  BasisOfRowModule );

##
InstallMethod( BasisOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix and IsVoidMatrix ],
        
  BasisOfRowsCoeff );

##  <#GAPDoc Label="BasisOfColumns">
##  <ManSection>
##    <Oper Arg="M" Name="BasisOfColumns" Label="for matrices"/>
##    <Oper Arg="M, T" Name="BasisOfColumns" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="BasisOfColumnModule" Label="for matrices"/>.
##      with two arguments it is a synonym of <Ref Oper="BasisOfColumnsCoeff" Label="for matrices"/>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( BasisOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  BasisOfColumnModule );

##
InstallMethod( BasisOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix and IsVoidMatrix ],
        
  BasisOfColumnsCoeff );

##
InstallMethod( DecideZero,
        "for a ring element and a homalg ring element",
        [ IsRingElement, IsHomalgRingElement ],
        
  function( r, rel )
    local red;
    
    rel := HomalgMatrix( [ rel ], 1, 1, HomalgRing( rel ) );
    
    return DecideZero( r, rel );
    
end );

##
InstallMethod( DecideZero,
        "for homalg matrices",
        [ IsRingElement, IsHomalgMatrix ],
        
  function( r, rel )
    local red;
    
    r := HomalgMatrix( [ r ], 1, 1, HomalgRing( rel ) );
    
    if NumberColumns( rel ) = 1 then
        red := DecideZeroRows( r, rel );
    elif NumberRows( rel ) = 1 then
        red := DecideZeroColumns( r, rel );
    else
        Error( "either the number of columns or the number of rows of the matrix of relations must be 1\n" );
    fi;
    
    return red[ 1, 1 ];
    
end );

##
InstallMethod( DecideZero,
        "for homalg matrices",
        [ IsRingElement, IsHomalgRingRelations ],
        
  function( r, rel )
    
    return DecideZero( r, MatrixOfRelations( rel ) );
    
end );

##
InstallMethod( DecideZero,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ], 1001,
        
  function( M, rel )
    
    if IsEmptyMatrix( M ) then
        return M;
    fi;
    
    if NumberColumns( rel ) = 1 then
        rel := DiagMat( ListWithIdenticalEntries( NumberColumns( M ), rel ) );
        return DecideZeroRows( M, rel );
    elif NumberRows( rel ) = 1 then
        rel := DiagMat( ListWithIdenticalEntries( NumberRows( M ), rel ) );
        return DecideZeroColumns( M, rel );
    fi;
    
    Error( "either the number of columns or the number of rows of the matrix of relations must be 1\n" );
    
end );

##
InstallMethod( DecideZero,
        "for homalg matrices",
        [ IsHomalgMatrix, IsList ],
        
  function( M, rel )
    local R;
    
    R := HomalgRing( M );
    
    rel := List( rel,
                 function( r )
                   if IsString( r ) then
                       return HomalgRingElement( r, R );
                   elif IsRingElement( r ) then
                       return r;
                   else
                       Error( r, " is neither a string nor a ring element\n" );
                   fi;
                 end );
    
    ## we prefer (to reduce the) rows
    rel := HomalgMatrix( rel, Length( rel ), 1, R );
    
    return DecideZero( M, rel );
    
end );

##
InstallMethod( DecideZero,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( M )
    
    IsZero( M );
    
    return M;
    
end );

##  <#GAPDoc Label="SyzygiesOfRows">
##  <ManSection>
##    <Oper Arg="M" Name="SyzygiesOfRows" Label="for matrices"/>
##    <Oper Arg="M, M2" Name="SyzygiesOfRows" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="SyzygiesGeneratorsOfRows" Label="for matrices"/>.
##      with two arguments it is a synonym of <Ref Oper="SyzygiesGeneratorsOfRows" Label="for pairs of matrices"/>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SyzygiesOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  SyzygiesGeneratorsOfRows );

##
InstallMethod( SyzygiesOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  SyzygiesGeneratorsOfRows );

##
InstallMethod( SyzygiesOfRows,
        "for a list of two homalg matrices",
        [ IsList ],
        
  L -> CallFuncList( SyzygiesGeneratorsOfRows, L ) );

##
InstallMethod( LazySyzygiesOfRows,
        "for two homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, N )
    
    return HomalgMatrixWithAttributes( [
                   EvalSyzygiesOfRows, [ M, N ],
                   NumberColumns, NumberRows( M )
                   ], HomalgRing( M ) );
    
end );

##
InstallMethod( IsZero,
        "for homalg matrices (HasEvalSyzygiesOfRows)",
        [ IsHomalgMatrix and HasEvalSyzygiesOfRows ], 100,
        
  function( C )
    local e;
    
    e :=  EvalSyzygiesOfRows( C );
    
    return IsZero( SyzygiesOfRows( e[1], e[2] ) );
    
end );

##
InstallMethod( Eval,
        "for homalg matrices (HasEvalSyzygiesOfRows)",
        [ IsHomalgMatrix and HasEvalSyzygiesOfRows ],
        
  function( C )
    local e;
    
    e :=  EvalSyzygiesOfRows( C );
    
    return Eval( SyzygiesOfRows( e[1], e[2] ) );
    
end );

##  <#GAPDoc Label="SyzygiesOfColumns">
##  <ManSection>
##    <Oper Arg="M" Name="SyzygiesOfColumns" Label="for matrices"/>
##    <Oper Arg="M, M2" Name="SyzygiesOfColumns" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="SyzygiesGeneratorsOfColumns" Label="for matrices"/>.
##      with two arguments it is a synonym of <Ref Oper="SyzygiesGeneratorsOfColumns" Label="for pairs of matrices"/>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SyzygiesOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  SyzygiesGeneratorsOfColumns );

##
InstallMethod( SyzygiesOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  SyzygiesGeneratorsOfColumns );

##
InstallMethod( SyzygiesOfColumns,
        "for a list of two homalg matrices",
        [ IsList ],
        
  L -> CallFuncList( SyzygiesGeneratorsOfColumns, L ) );

##
InstallMethod( LazySyzygiesOfColumns,
        "for two homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, N )
    
    return HomalgMatrixWithAttributes( [
                   EvalSyzygiesOfColumns, [ M, N ],
                   NumberRows, NumberColumns( M )
                   ], HomalgRing( M ) );
    
end );

##
InstallMethod( IsZero,
        "for homalg matrices (HasEvalSyzygiesOfColumns)",
        [ IsHomalgMatrix and HasEvalSyzygiesOfColumns ], 100,
        
  function( C )
    local e;
    
    e :=  EvalSyzygiesOfColumns( C );
    
    return IsZero( SyzygiesOfColumns( e[1], e[2] ) );
    
end );

##
InstallMethod( Eval,
        "for homalg matrices (HasEvalSyzygiesOfColumns)",
        [ IsHomalgMatrix and HasEvalSyzygiesOfColumns ],
        
  function( C )
    local e;
    
    e :=  EvalSyzygiesOfColumns( C );
    
    return Eval( SyzygiesOfColumns( e[1], e[2] ) );
    
end );

##  <#GAPDoc Label="ReducedSyzygiesOfRows">
##  <ManSection>
##    <Oper Arg="M" Name="ReducedSyzygiesOfRows" Label="for matrices"/>
##    <Oper Arg="M, M2" Name="ReducedSyzygiesOfRows" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="ReducedSyzygiesGeneratorsOfRows" Label="for matrices"/>.
##      With two arguments it calls <C>ReducedBasisOfRowModule</C>( <C>SyzygiesGeneratorsOfRows</C>( <A>M</A>, <A>M2</A> ) ).
##      (&see; <Ref Oper="ReducedBasisOfRowModule" Label="for matrices"/> and
##       <Ref Oper="SyzygiesGeneratorsOfRows" Label="for pairs of matrices"/>)
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( ReducedSyzygiesOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  ReducedSyzygiesGeneratorsOfRows );

##
InstallMethod( ReducedSyzygiesOfRows,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, M2 )
    
    ## a LIMAT method takes care of the case when M2 is _known_ to be zero
    ## checking IsZero( M2 ) causes too many obsolete calls
    
    ## a priori computing a basis of the syzygies matrix
    ## causes obsolete computations, at least in general
    return ReducedBasisOfRowModule( BasisOfRowModule( SyzygiesGeneratorsOfRows( M, M2 ) ) );
    
end );

##  <#GAPDoc Label="ReducedSyzygiesOfColumns">
##  <ManSection>
##    <Oper Arg="M" Name="ReducedSyzygiesOfColumns" Label="for matrices"/>
##    <Oper Arg="M, M2" Name="ReducedSyzygiesOfColumns" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      With one argument it is a synonym of <Ref Oper="ReducedSyzygiesGeneratorsOfColumns" Label="for matrices"/>.
##      With two arguments it calls <C>ReducedBasisOfColumnModule</C>( <C>SyzygiesGeneratorsOfColumns</C>( <A>M</A>, <A>M2</A> ) ).
##      (&see; <Ref Oper="ReducedBasisOfColumnModule" Label="for matrices"/> and
##       <Ref Oper="SyzygiesGeneratorsOfColumns" Label="for pairs of matrices"/>)
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( ReducedSyzygiesOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  ReducedSyzygiesGeneratorsOfColumns );

##
InstallMethod( ReducedSyzygiesOfColumns,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, M2 )
    
    ## a LIMAT method takes care of the case when M2 is _known_ to be zero
    ## checking IsZero( M2 ) causes too many obsolete calls
    
    ## a priori computing a basis of the syzygies matrix
    ## causes obsolete computations, at least in general
    return ReducedBasisOfColumnModule( BasisOfColumnModule( SyzygiesGeneratorsOfColumns( M, M2 ) ) );
    
end );

##
InstallMethod( SyzygiesBasisOfRows, ### defines: SyzygiesBasisOfRows (SyzygiesBasis)
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( M )
    local S;
    
    S := SyzygiesOfRows( M );
    
    return BasisOfRows( S );
    
end );

##
InstallMethod( SyzygiesBasisOfRows, ### defines: SyzygiesBasisOfRows (SyzygiesBasis)
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M1, M2 )
    local S;
    
    S := SyzygiesOfRows( M1, M2 );
    
    return BasisOfRows( S );
    
end );

##
InstallMethod( SyzygiesBasisOfColumns, ### defines: SyzygiesBasisOfColumns (SyzygiesBasis)
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( M )
    local S;
    
    S := SyzygiesOfColumns( M );
    
    return BasisOfColumns( S );
    
end );

##
InstallMethod( SyzygiesBasisOfColumns, ### defines: SyzygiesBasisOfColumns (SyzygiesBasis)
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M1, M2 )
    local S;
    
    S := SyzygiesOfColumns( M1, M2 );
    
    return BasisOfColumns( S );
    
end );

##  <#GAPDoc Label="RightDivide">
##  <ManSection>
##    <Oper Arg="B, A" Name="RightDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      Let <A>B</A> and <A>A</A> be matrices having the same number of columns and defined over the same ring.
##      The matrix <C>RightDivide</C>( <A>B</A>, <A>A</A> ) is a particular solution of the inhomogeneous (one sided) linear system
##      of equations <M>X<A>A</A>=<A>B</A></M> in case it is solvable. Otherwise <C>fail</C> is returned.
##      The name <C>RightDivide</C> suggests <Q><M>X=<A>B</A><A>A</A>^{-1}</M></Q>.
##      This generalizes <Ref Attr="LeftInverse" Label="for matrices"/> for which <A>B</A> becomes the identity matrix.
##      (&see; <Ref Oper="SyzygiesGeneratorsOfRows" Label="for matrices"/>)
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( RightDivide, ### defines: RightDivide (RightDivideF)
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( B, A ) ## CAUTION: Do not use lazy evaluation here!!!
    local R, T, B_;
    
    R := HomalgRing( B );
    
    ## B_ = B + T * A
    T := HomalgVoidMatrix( R );
    B_ := DecideZeroRowsEffectively( B, A, T );
    
    ## if B_ does not vanish
    if not IsZero( B_ ) then
        ## A is not a right factor of B, i.e.
        ## the rows of A are not a generating set
        return fail;
    fi;
    
    ## check assertion
    Assert( 5, IsZero( B + T * A ) );
    
    return -T;
    
end );

##  <#GAPDoc Label="LeftDivide">
##  <ManSection>
##    <Oper Arg="A, B" Name="LeftDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      Let <A>A</A> and <A>B</A> be matrices having the same number of rows and defined over the same ring.
##      The matrix <C>LeftDivide</C>( <A>A</A>, <A>B</A> ) is a particular solution of the inhomogeneous (one sided) linear system
##      of equations <M><A>A</A>X=<A>B</A></M> in case it is solvable. Otherwise <C>fail</C> is returned.
##      The name <C>LeftDivide</C> suggests <Q><M>X=<A>A</A>^{-1}<A>B</A></M></Q>.
##      This generalizes <Ref Attr="RightInverse" Label="for matrices"/> for which <A>B</A> becomes the identity matrix.
##      (&see; <Ref Oper="SyzygiesGeneratorsOfColumns" Label="for matrices"/>)
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( LeftDivide, ### defines: LeftDivide (LeftDivideF)
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( A, B ) ## CAUTION: Do not use lazy evaluation here!!!
    local R, T, B_;
    
    R := HomalgRing( B );
    
    ## B_ = B + A * T
    T := HomalgVoidMatrix( R );
    B_ := DecideZeroColumnsEffectively( B, A, T );
    
    ## if B_ does not vanish
    if not IsZero( B_ ) then
        ## A is not a left factor of B, i.e.
        ## the columns of A are not a generating set
        return fail;
    fi;
    
    ## check assertion
    Assert( 5, IsZero( B + A * T ) );
    
    return -T;
    
end );

##  <#GAPDoc Label="RelativeRightDivide">
##  <ManSection>
##    <Oper Arg="B, A, L" Name="RightDivide" Label="for triples of matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      Let <A>B</A>, <A>A</A> and <A>L</A> be matrices having the same number of columns and defined over the same ring.
##      The matrix <C>RightDivide</C>( <A>B</A>, <A>A</A>, <A>L</A> ) is a particular solution of the inhomogeneous (one sided)
##      linear system of equations <M>X<A>A</A>+Y<A>L</A>=<A>B</A></M> in case it is solvable (for some <M>Y</M> which is forgotten).
##      Otherwise <C>fail</C> is returned. The name <C>RightDivide</C> suggests <Q><M>X=<A>B</A><A>A</A>^{-1}</M> modulo <A>L</A></Q>.
##      (Cf. <Cite Key="BR" Where="Subsection 3.1.1"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( RightDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix, IsHomalgMatrix ],
        
  function( B, A, L ) ## CAUTION: Do not use lazy evaluation here!!!
    local R, BL, ZA, AL, ZB, T, B_;
    
    R := HomalgRing( B );
    
    BL := BasisOfRows( L );
    
    ## first reduce A modulo L
    ZA := DecideZeroRows( A, BL );
    
    AL := UnionOfRows( ZA, BL );
    
    ## also reduce B modulo L
    ZB := DecideZeroRows( B, BL );
    
    ## B_ = ZB + T * AL
    T := HomalgVoidMatrix( R );
    B_ := DecideZeroRowsEffectively( ZB, AL, T );
    
    ## if B_ does not vanish
    if not IsZero( B_ ) then
        return fail;
    fi;
    
    T := CertainColumns( T, [ 1 .. NumberRows( A ) ] );
    
    ## check assertion
    Assert( 5, IsZero( DecideZeroRows( B + T * A, BL ) ) );
    
    return -T;
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##  <#GAPDoc Label="RelativeLeftDivide">
##  <ManSection>
##    <Oper Arg="A, B, L" Name="LeftDivide" Label="for triples of matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      Let <A>A</A>, <A>B</A> and <A>L</A> be matrices having the same number of columns and defined over the same ring.
##      The matrix <C>LeftDivide</C>( <A>A</A>, <A>B</A>, <A>L</A> ) is a particular solution of the inhomogeneous (one sided)
##      linear system of equations <M><A>A</A>X+<A>L</A>Y=<A>B</A></M> in case it is solvable (for some <M>Y</M> which is forgotten).
##      Otherwise <C>fail</C> is returned. The name <C>LeftDivide</C> suggests <Q><M>X=<A>A</A>^{-1}<A>B</A></M> modulo <A>L</A></Q>.
##      (Cf. <Cite Key="BR" Where="Subsection 3.1.1"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( LeftDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix, IsHomalgMatrix ],
        
  function( A, B, L ) ## CAUTION: Do not use lazy evaluation here!!!
    local R, BL, ZA, AL, ZB, T, B_;
    
    R := HomalgRing( B );
    
    BL := BasisOfColumns( L );
    
    ## first reduce A modulo L
    ZA := DecideZeroColumns( A, BL );
    
    AL := UnionOfColumns( ZA, BL );
    
    ## also reduce B modulo L
    ZB := DecideZeroColumns( B, BL );
    
    ## B_ = ZB + AL * T
    T := HomalgVoidMatrix( R );
    B_ := DecideZeroColumnsEffectively( ZB, AL, T );
    
    ## if B_ does not vanish
    if not IsZero( B_ ) then
        return fail;
    fi;
    
    T := CertainRows( T, [ 1 .. NumberColumns( A ) ] );
    
    ## check assertion
    Assert( 5, IsZero( DecideZeroColumns( B + A * T, BL ) ) );
    
    return -T;
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##  <#GAPDoc Label="SafeRightDivide">
##  <ManSection>
##    <Oper Arg="B, A" Name="SafeRightDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      Same as <Ref Oper="RightDivide" Label="for pairs of matrices"/>, but asserts that the result is not <C>fail</C>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SafeRightDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( B, A )
    local T;
    
    T := RightDivide( B, A );
    
    Assert( 0, T <> fail );
    
    return T;
    
end );

##  <#GAPDoc Label="SafeLeftDivide">
##  <ManSection>
##    <Oper Arg="A, B" Name="SafeLeftDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      Same as <Ref Oper="LeftDivide" Label="for pairs of matrices"/>, but asserts that the result is not <C>fail</C>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SafeLeftDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( A, B )
    local T;
    
    T := LeftDivide( A, B );
    
    Assert( 0, T <> fail );
    
    return T;
    
end );

##  <#GAPDoc Label="UniqueRightDivide">
##  <ManSection>
##    <Oper Arg="B, A" Name="UniqueRightDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      Same as <Ref Oper="SafeRightDivide" Label="for pairs of matrices"/>, but asserts
##      at assertion level 5 that the solution is unique.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( UniqueRightDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( B, A )
    
    ## check uniqueness of the solution
    Assert( 5, IsZero( SyzygiesOfRows( A ) ) );
    
    return SafeRightDivide( B, A );
    
end );

##  <#GAPDoc Label="UniqueLeftDivide">
##  <ManSection>
##    <Oper Arg="A, B" Name="UniqueLeftDivide" Label="for pairs of matrices"/>
##    <Returns>a &homalg; matrix</Returns>
##    <Description>
##      Same as <Ref Oper="SafeLeftDivide" Label="for pairs of matrices"/>, but asserts
##      at assertion level 5 that the solution is unique.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( UniqueLeftDivide,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( A, B )
    
    ## check uniqueness of the solution
    Assert( 5, IsZero( SyzygiesOfColumns( A ) ) );
    
    return SafeLeftDivide( A, B );
    
end );

##  <#GAPDoc Label="LeftInverse:method">
##  <ManSection>
##    <Meth Arg="RI" Name="LeftInverse" Label="for matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      The left inverse of the matrix <A>RI</A>. The lazy version of this operation is
##      <Ref Meth="LeftInverseLazy" Label="for matrices"/>.
##      (&see; <Ref Oper="RightDivide" Label="for pairs of matrices"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( LeftInverse,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( RI )
    local Id, LI;
    
    Id := HomalgIdentityMatrix( NumberColumns( RI ), HomalgRing( RI ) );
    
    LI := RightDivide( Id, RI ); ## ( cf. [BR08, Subsection 3.1.3] )
    
    ## CAUTION: for the following SetXXX RightDivide is assumed
    ## NOT to be lazy evaluated!!!
    
    SetIsLeftInvertibleMatrix( RI, IsHomalgMatrix( LI ) );
    
    if IsBool( LI ) then
        return fail;
    fi;
    
    if HasIsInvertibleMatrix( RI ) and IsInvertibleMatrix( RI ) then
        SetIsInvertibleMatrix( LI, true );
    else
        SetIsRightInvertibleMatrix( LI, true );
    fi;
    
    SetRightInverse( LI, RI );
    
    SetNumberColumns( LI, NumberRows( RI ) );
    
    if NumberRows( RI ) = NumberColumns( RI ) then
        ## a left inverse of a ring element is unique
        ## and coincides with the right inverse
        SetRightInverse( RI, LI );
        SetLeftInverse( LI, RI );
    fi;
    
    return LI;
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##  <#GAPDoc Label="RightInverse:method">
##  <ManSection>
##    <Meth Arg="LI" Name="RightInverse" Label="for matrices"/>
##    <Returns>a &homalg; matrix or fail</Returns>
##    <Description>
##      The right inverse of the matrix <A>LI</A>. The lazy version of this operation is
##      <Ref Meth="RightInverseLazy" Label="for matrices"/>.
##      (&see; <Ref Oper="LeftDivide" Label="for pairs of matrices"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( RightInverse,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( LI )
    local Id, RI;
    
    Id := HomalgIdentityMatrix( NumberRows( LI ), HomalgRing( LI ) );
    
    RI := LeftDivide( LI, Id ); ## ( cf. [BR08, Subsection 3.1.3] )
    
    ## CAUTION: for the following SetXXX LeftDivide is assumed
    ## NOT to be lazy evaluated!!!
    
    SetIsRightInvertibleMatrix( LI, IsHomalgMatrix( RI ) );
    
    if IsBool( RI ) then
        return fail;
    fi;
    
    if HasIsInvertibleMatrix( LI ) and IsInvertibleMatrix( LI ) then
        SetIsInvertibleMatrix( RI, true );
    else
        SetIsLeftInvertibleMatrix( RI, true );
    fi;
    
    SetLeftInverse( RI, LI );
    
    SetNumberRows( RI, NumberColumns( LI ) );
    
    if NumberRows( LI ) = NumberColumns( LI ) then
        ## a right inverse of a ring element is unique
        ## and coincides with the left inverse
        SetLeftInverse( LI, RI );
        SetRightInverse( RI, LI );
    fi;
    
    return RI;
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##
InstallMethod( IsRightInvertibleMatrix,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( M )
    
    return not IsBool( RightInverse( M ) );
    
end );

##
InstallMethod( IsLeftInvertibleMatrix,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
  function( M )
    
    return not IsBool( LeftInverse( M ) );
    
end );

##  <#GAPDoc Label="GenerateSameRowModule">
##  <ManSection>
##    <Oper Arg="M, N" Name="GenerateSameRowModule" Label="for pairs of matrices"/>
##    <Returns><C>true</C> or <C>false</C></Returns>
##    <Description>
##      Check if the row span of <A>M</A> and of <A>N</A> are identical or not
##      (&see; <Ref Oper="RightDivide" Label="for pairs of matrices"/>).
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( GenerateSameRowModule,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, N )
    
    return not ( IsBool( RightDivide( N, M ) ) or IsBool( RightDivide( M, N ) ) );
    
end );

##  <#GAPDoc Label="GenerateSameColumnModule">
##  <ManSection>
##    <Oper Arg="M, N" Name="GenerateSameColumnModule" Label="for pairs of matrices"/>
##    <Returns><C>true</C> or <C>false</C></Returns>
##    <Description>
##      Check if the column span of <A>M</A> and of <A>N</A> are identical or not
##      (&see; <Ref Oper="LeftDivide" Label="for pairs of matrices"/>).
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( GenerateSameColumnModule,
        "for homalg matrices",
        [ IsHomalgMatrix, IsHomalgMatrix ],
        
  function( M, N )
    
    return not ( IsBool( LeftDivide( M, N ) ) or IsBool( LeftDivide( N, M ) ) );
    
end );

##---------------------
##
## the lazy evaluation:
##
##---------------------

##  <#GAPDoc Label="Eval:HasEvalLeftInverse">
##  <ManSection>
##    <Meth Arg="LI" Name="Eval" Label="for matrices created with LeftInverseLazy"/>
##    <Returns>see below</Returns>
##    <Description>
##      In case the matrix <A>LI</A> was created using
##      <Ref Meth="LeftInverseLazy" Label="for matrices"/>
##      then the filter <C>HasEvalLeftInverse</C> for <A>LI</A> is set to true and the method listed below
##      will be used to set the attribute <C>Eval</C>. (&see; <Ref Oper="LeftInverse" Label="for matrices"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( Eval,
        "for homalg matrices",
        [ IsHomalgMatrix and HasEvalLeftInverse ],
        
  function( LI )
    local left_inv;
    
    left_inv := LeftInverse( EvalLeftInverse( LI ) );
    
    if IsBool( left_inv ) then
        return false;
    fi;
    
    return Eval( left_inv );
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##  <#GAPDoc Label="Eval:HasEvalRightInverse">
##  <ManSection>
##    <Meth Arg="RI" Name="Eval" Label="for matrices created with RightInverseLazy"/>
##    <Returns>see below</Returns>
##    <Description>
##      In case the matrix <A>RI</A> was created using
##      <Ref Meth="RightInverseLazy" Label="for matrices"/>
##      then the filter <C>HasEvalRightInverse</C> for <A>RI</A> is set to true and the method listed below
##      will be used to set the attribute <C>Eval</C>. (&see; <Ref Oper="RightInverse" Label="for matrices"/>)
##    <Listing Type="Code"><![CDATA[
InstallMethod( Eval,
        "for homalg matrices",
        [ IsHomalgMatrix and HasEvalRightInverse ],
        
  function( RI )
    local right_inv;
    
    right_inv := RightInverse( EvalRightInverse( RI ) );
    
    if IsBool( right_inv ) then
        return false;
    fi;
    
    return Eval( right_inv );
    
end );
##  ]]></Listing>
##    </Description>
##  </ManSection>
##  <#/GAPDoc>

##
InstallGlobalFunction( BestBasis, ### defines: BestBasis
  function( arg )
    local M, R, RP, nargs, m, n, B, U, V;
    
    if not IsHomalgMatrix( arg[1] ) then
        Error( "expecting a homalg matrix as a first argument, but received ", arg[1], "\n" );
    fi;
    
    M := arg[1];
    
    R := HomalgRing( M );
    
    RP := homalgTable( R );
    
    if IsBound(RP!.BestBasis) then
        
        return CallFuncList( RP!.BestBasis, arg );
        
    elif IsBound(RP!.ReducedRowEchelonForm) then
        
        nargs := Length( arg );
        
        m := NumberRows( M );
        n := NumberColumns( M );
        
        if nargs > 1 and IsHomalgMatrix( arg[2] ) then ## not BestBasis( M, "", V )
            B := ReducedRowEchelonForm( M, arg[2] );
        else
            B := ReducedRowEchelonForm( M );
        fi;
        
        if nargs > 2 and IsHomalgMatrix( arg[3] ) then ## not BestBasis( M, U, "" )
            B := ReducedColumnEchelonForm( B, arg[3] );
        else
            B := ReducedColumnEchelonForm( B );
        fi;
        
        if m - NumberRows( B ) = 0 and n - NumberColumns( B ) = 0 then
            return B;
        elif m - NumberRows( B ) = 0 and n - NumberColumns( B ) > 0 then
            return UnionOfColumns( B, HomalgZeroMatrix( m, n - NumberColumns( B ), R ) );
        elif m - NumberRows( B ) > 0 and n - NumberColumns( B ) = 0 then
            return UnionOfRows( B, HomalgZeroMatrix( m - NumberRows( B ), n, R ) );
        else
            return DiagMat( [ B, HomalgZeroMatrix( m - NumberRows( B ), n - NumberColumns( B ), R ) ] );
        fi;
        
    fi;
    
    TryNextMethod( );
    
end );

##
InstallGlobalFunction( SimplerEquivalentMatrix, ### defines: SimplerEquivalentMatrix (BetterGenerators) (incomplete)
  function( arg )
    local M, R, RP, nargs, compute_U, compute_V, compute_UI, compute_VI,
          nar_U, nar_V, nar_UI, nar_VI, MM, m, n, finished, U, V, UI, VI, u, v,
          barg, one, clean_rows, unclean_rows, clean_columns, unclean_columns,
          M_orig, modified, eliminate_units, unit_free, a;
    
    if not IsHomalgMatrix( arg[1] ) then
        Error( "expecting a homalg matrix as a first argument, but received ", arg[1], "\n" );
    fi;
    
    M := arg[1];
    
    R := HomalgRing( M );
    
    RP := homalgTable( R );
  
    if IsBound(RP!.SimplerEquivalentMatrix) then
        return RP!.SimplerEquivalentMatrix( arg );
    fi;
    
    nargs := Length( arg );
    
    if nargs = 1 then
        ## SimplerEquivalentMatrix(M)
        compute_U := false;
        compute_V := false;
        compute_UI := false;
        compute_VI := false;
    elif nargs = 2 and IsHomalgMatrix( arg[2] ) then
        ## SimplerEquivalentMatrix(M,V)
        compute_U := false;
        compute_V := true;
        compute_UI := false;
        compute_VI := false;
        nar_V := 2;
    elif nargs = 3 and IsHomalgMatrix( arg[2] ) and IsString( arg[3] ) then
        ## SimplerEquivalentMatrix(M,VI,"")
        compute_U := false;
        compute_V := false;
        compute_UI := false;
        compute_VI := true;
        nar_VI := 2;
    elif nargs = 6 and IsHomalgMatrix( arg[2] ) and IsHomalgMatrix( arg[3] )
      and IsString( arg[4] ) and IsString( arg[5] ) and IsString( arg[6] ) then
        ## SimplerEquivalentMatrix(M,U,UI,"","","")
        compute_U := true;
        compute_V := false;
        compute_UI := true;
        compute_VI := false;
        nar_U := 2;
        nar_UI := 3;
    elif nargs = 5 and IsHomalgMatrix( arg[2] ) and IsHomalgMatrix( arg[3] )
      and IsString( arg[4] ) and IsString( arg[5] ) then
        ## SimplerEquivalentMatrix(M,V,VI,"","")
        compute_U := false;
        compute_V := true;
        compute_UI := false;
        compute_VI := true;
        nar_V := 2;
        nar_VI := 3;
    elif nargs = 4 and IsHomalgMatrix( arg[2] ) and IsHomalgMatrix( arg[3] )
      and IsString( arg[4] ) then
        ## SimplerEquivalentMatrix(M,UI,VI,"")
        compute_U := false;
        compute_V := false;
        compute_UI := true;
        compute_VI := true;
        nar_UI := 2;
        nar_VI := 3;
    elif nargs = 5 and IsHomalgMatrix( arg[2] ) and IsHomalgMatrix( arg[3] )
      and IsHomalgMatrix( arg[4] ) and IsHomalgMatrix( arg[5] ) then
        ## SimplerEquivalentMatrix(M,U,V,UI,VI)
        compute_U := true;
        compute_V := true;
        compute_UI := true;
        compute_VI := true;
        nar_U := 2;
        nar_V := 3;
        nar_UI := 4;
        nar_VI := 5;
    elif IsHomalgMatrix( arg[2] ) and IsHomalgMatrix( arg[3] ) then
        ## SimplerEquivalentMatrix(M,U,V)
        compute_U := true;
        compute_V := true;
        compute_UI := false;
        compute_VI := false;
        nar_U := 2;
        nar_V := 3;
    else
        Error( "Wrong input!\n" );
    fi;
    
    m := NumberRows( M );
    n := NumberColumns( M );
    
    finished := false;
    
    #=====# begin of the core procedure #=====#
    
    if compute_U then
        U := HomalgIdentityMatrix( m, R );
    fi;
    
    if compute_V then
        V := HomalgIdentityMatrix( n, R );
    fi;
    
    if compute_UI then
        UI := HomalgIdentityMatrix( m, R );
    fi;
    
    if compute_VI then
        VI := HomalgIdentityMatrix( n, R );
    fi;
    
    if IsZero( M ) then
        finished := true;
    fi;
    
    if not finished
       and ( IsBound( RP!.BestBasis )
             or IsBound( RP!.ReducedRowEchelonForm )
             or IsBound( RP!.ReducedColumnEchelonForm ) ) then
        
        if compute_U or compute_UI then
            U := HomalgVoidMatrix( R );
        fi;
        
        if compute_V or compute_VI then
            V := HomalgVoidMatrix( R );
        fi;
        
        if not ( compute_U or compute_UI or compute_V or compute_VI ) then
            barg := [ M ];
        elif ( compute_U or compute_UI ) and not ( compute_V or compute_VI ) then
            barg := [ M, U ];
        elif ( compute_V or compute_VI ) and not ( compute_U or compute_UI ) then
            barg := [ M, "", V ];
        else
            barg := [ M, U, V ];
        fi;
        
        M := CallFuncList( BestBasis, barg );
        
        ## FIXME:
        #if ( compute_V or compute_VI ) then
        #    if IsList( V ) and V <> [] and IsString( V[1] ) then
        #        if LowercaseString( V[1]{[1..3]} ) = "inv" then
        #            VI := V[2];
        #            if compute_V then
        #                V := LeftInverse( VI, arg[1], "NO_CHECK" );
        #            fi;
        #        else
        #            Error( "Cannot interpret the first string in V ", V[1], "\n" );
        #        fi;
        #    fi;
        #fi;
        
        if compute_UI then
            UI := RightInverseLazy( U );
        fi;
        
        if compute_VI then
            VI := LeftInverseLazy( V ); ## this is indeed a LeftInverse
        fi;
        
        ## don't compute a "basis" here, since it is not clear if to do it for rows or for columns!
        ## this differs from the Maple code, where we only worked with left modules
        
        if IsEmptyMatrix( M ) then
            finished := true;
        fi;
        
    fi;
    
    if not finished and
       ( ( ( compute_V or compute_VI ) and not ( compute_U or compute_UI ) ) or
         ( ( compute_U or compute_UI ) and not ( compute_V or compute_VI ) ) ) then
        
        M := GetRidOfRowsAndColumnsWithUnits( M );
        
        if compute_U then
            U := M[1] * U;
        fi;
        
        if compute_UI then
            UI := UI * M[2];
        fi;
        
        if compute_VI then
            VI := M[4] * VI;
        fi;
        
        if compute_V then
            V := V * M[5];
        fi;
        
        M := M[3];
        
        if IsEmptyMatrix( M ) then
            finished := true;
        fi;
        
    elif not finished and
      not ( IsBound( RP!.BestBasis )
            or IsBound( RP!.ReducedRowEchelonForm )
            or IsBound( RP!.ReducedColumnEchelonForm ) ) then
        
        M_orig := M;
        
        MM := MutableCopyMat( M );
        
        modified := false;
        
        if IsIdenticalObj( MM, M ) then
            Error( "unable to get a real copy of the matrix\n" );
        fi;
        
        ## CAUTION: since MM is mutable the code below
        ##          should be aware of not introducing units
        if HasIsUnitFree( M ) and IsUnitFree( M ) then
            SetIsUnitFree( MM, true );
        fi;
        
        M := MM;
        
        m := NumberRows( M );
        n := NumberColumns( M );
        
        if compute_U then
            U := HomalgInitialIdentityMatrix( m, R );
        fi;
        if compute_UI then
            UI := HomalgInitialIdentityMatrix( m, R );
        fi;
        
        if compute_V then
            V := HomalgIdentityMatrix( n, R );
        fi;
        if compute_VI then
            VI := HomalgIdentityMatrix( n, R );
        fi;
        
        one := One( R );
        
        clean_rows := [ ];
        unclean_rows := [ 1 .. m ];
        clean_columns := [ ];
        unclean_columns := [ 1 .. n ];
        
        eliminate_units := function( arg )
            local pos, i, j, r, q, v, vi, u, ui;
            
            unit_free := true;
            
            if Length( arg ) > 0 then
                pos := arg[1];
            else
                pos := GetUnitPosition( M, clean_columns );
            fi;
            
            if pos = fail then
                clean_rows := GetCleanRowsPositions( M, clean_columns );
                unclean_rows := Filtered( [ 1 .. m ], a -> not a in clean_rows );
                
                return clean_columns;
            else
                modified := true;
                unit_free := false;
            fi;
            
            while true do
                i := pos[1];
                j := pos[2];
                
                Add( clean_columns, j );
                Remove( unclean_columns, Position( unclean_columns, j ) );
                
                ## divide the i-th row by the unit M[i][j]
                
                r := M[ i, j ];
                
                if not IsOne( r ) then
                    
                    M := DivideRowByUnit( M, i, r, j );
                    
                    if compute_U then
                        U := DivideRowByUnit( U, i, r, 0 );
                    fi;
                    
                    if compute_UI then
                        q := one / r;
                        UI := DivideColumnByUnit( UI, i, q, 0 );
                    fi;
                fi;
                
                ## cleanup the i-th row
                
                v := HomalgInitialIdentityMatrix( n, R );
                
                if compute_VI then
                    vi := HomalgInitialIdentityMatrix( n, R );
                else
                    vi := "";
                fi;
                
                CopyRowToIdentityMatrix( M, i, [ v, vi ], j );
                
                if compute_V then
                    ResetFilterObj( v, IsMutable );
                    V := V * v;
                fi;
                
                if compute_VI then
                    ResetFilterObj( vi, IsMutable );
                    VI := vi * VI;
                fi;
                
                ## caution: M will now have two attributes EvalCompose and Eval
                M := M * v;
                
                ## attributes do not get saved for mutable objects since GAP 4.11
                ## so we MUST evaluate M before making it mutable
                Eval( M ); SetIsMutableMatrix( M, true );
                
                ## cleanup the j-th column
                
                if compute_U then
                    u := HomalgInitialIdentityMatrix( NumberRows( U ), R );
                else
                    u := "";
                fi;
                
                if compute_UI then
                    ui := HomalgInitialIdentityMatrix( NumberColumns( UI ), R );
                else
                    ui := "";
                fi;
                
                if compute_U or compute_UI then
                    CopyColumnToIdentityMatrix( M, j, [ u, ui ], i );
                fi;
                
                if compute_U then
                    ResetFilterObj( u, IsMutable );
                    ResetFilterObj( U, IsMutable );
                    U := u * U;
                fi;
                
                if compute_UI then
                    ResetFilterObj( ui, IsMutable );
                    ResetFilterObj( UI, IsMutable );
                    UI := UI * ui;
                fi;
                
                # an M := u * M would simply cause:
                M := SetColumnToZero( M, i, j );
                
                pos := GetUnitPosition( M, clean_columns );
                
                if pos = fail then
                    break;
                fi;
                
                ## attributes do not get saved for mutable objects since GAP 4.11
                ## so we MUST evaluate M before making it mutable
                Eval( M ); SetIsMutableMatrix( M, true );
                
                if compute_U then
                    U := MutableCopyMat( U );
                fi;
                
                if compute_UI then
                    UI := MutableCopyMat( UI );
                fi;
                
            od;
            
            clean_rows := GetCleanRowsPositions( M, clean_columns );
            unclean_rows := Filtered( [ 1 .. m ], a -> not a in clean_rows );
            
            return clean_columns;
        end;
        
        unit_free := false;
        
        while not unit_free do
            
            ## don't compute a "basis" here, since it is not clear if to do it for rows or for columns!
            ## this differs from the Maple code, where we only worked with left modules
            
            m := NumberRows( M );
            n := NumberColumns( M );
            
            ## eliminate_units alters unit_free
            eliminate_units();
            
            ## FIXME: add heuristics
            
        od;
        
        if not modified then
            M := M_orig;
        fi;
        
        SetIsUnitFree( M, true );
        MakeImmutable( M );
        
        if IsEmptyMatrix( M ) then
            finished := true;
        fi;
        
    fi;
    
    if compute_U then
        SetPreEval( arg[nar_U], U );
        ResetFilterObj( arg[nar_U], IsVoidMatrix );
        Assert( 6, IsHomalgMatrix( LeftDivide( M, U * arg[1] ) ) );
    fi;
    
    if compute_V then
        SetPreEval( arg[nar_V], V );
        ResetFilterObj( arg[nar_V], IsVoidMatrix );
        Assert( 6, IsHomalgMatrix( RightDivide( arg[1] * V, M ) ) );
    fi;
    
    if compute_UI then
        if not IsBound( UI ) then
            UI := HomalgIdentityMatrix( NumberRows( M ), R );
        fi;
        SetPreEval( arg[nar_UI], UI );
        ResetFilterObj( arg[nar_UI], IsVoidMatrix );
        Assert( 6, IsHomalgMatrix( LeftDivide( arg[1], UI * M ) ) );
    fi;
    
    if compute_VI then
        if not IsBound( VI ) then
            VI := HomalgIdentityMatrix( NumberColumns( M ), R );
        fi;
        SetPreEval( arg[nar_VI], VI );
        ResetFilterObj( arg[nar_VI], IsVoidMatrix );
        Assert( 6, IsHomalgMatrix( RightDivide( M * VI, arg[1] ) ) );
    fi;
    
    return M;
    
end );

##  <#GAPDoc Label="SimplifyHomalgMatrixByLeftAndRightMultiplicationWithInvertibleMatrices">
##  <ManSection>
##    <Oper Arg="M" Name="SimplifyHomalgMatrixByLeftAndRightMultiplicationWithInvertibleMatrices" Label="for matrices"/>
##    <Returns>a list of 5 &homalg; matrices</Returns>
##    <Description>
##      The input is a &homalg; matrix <A>M</A>.
##      The output is a 5-tuple of &homalg; matrices <A>S</A>, <A>U</A>, <A>V</A>, <A>UI</A>, <A>VI</A>,
##      such that <A> U M V = S</A>. Moreover, <A>U</A> and <A>V</A> are invertible with inverses <A>UI</A>, <A>VI</A>, respectively.
##      The idea is that the matrix <A>S</A> should look "simpler" than <A>M</A>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SimplifyHomalgMatrixByLeftAndRightMultiplicationWithInvertibleMatrices,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
    function( M )
        local ring, U, V, UI, VI, S;
        
        ring := HomalgRing( M );
        
        U := HomalgVoidMatrix( ring );
        
        V := HomalgVoidMatrix( ring );
        
        UI := HomalgVoidMatrix( ring );
        
        VI := HomalgVoidMatrix( ring );
        
        S := SimplerEquivalentMatrix( M, U, V, UI, VI );
        
        return [ S, U, V, UI, VI ];
        
end );

##  <#GAPDoc Label="SimplifyHomalgMatrixByLeftMultiplicationWithInvertibleMatrix">
##  <ManSection>
##    <Oper Arg="M" Name="SimplifyHomalgMatrixByLeftMultiplicationWithInvertibleMatrix" Label="for matrices"/>
##    <Returns>a list of 3 &homalg; matrices</Returns>
##    <Description>
##      The input is a &homalg; matrix <A>M</A>.
##      The output is a 3-tuple of &homalg; matrices <A>S</A>, <A>T</A>, <A>TI</A>
##      such that <A> T M = S</A>. Moreover, <A>T</A> is invertible with inverse <A>TI</A>.
##      The idea is that the matrix <A>S</A> should look "simpler" than <A>M</A>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SimplifyHomalgMatrixByLeftMultiplicationWithInvertibleMatrix,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
    function( M )
        local R, RP, T, S;
        
        R := HomalgRing( M );
        
        RP := homalgTable( R );
        
        if IsBound(RP!.ReducedRowEchelonForm) or IsBound(RP!.ReducedColumnEchelonForm) then
            
            T := HomalgVoidMatrix( R );
            
            S := ReducedRowEchelonForm( M, T );
            
        else
            
            T := HomalgIdentityMatrix( NumberRows( M ), R );
            
            S := M;
            
        fi;
        
        return [ S, T, LeftInverseLazy( T ) ];
        
end );

##  <#GAPDoc Label="SimplifyHomalgMatrixByRightMultiplicationWithInvertibleMatrix">
##  <ManSection>
##    <Oper Arg="M" Name="SimplifyHomalgMatrixByRightMultiplicationWithInvertibleMatrix" Label="for matrices"/>
##    <Returns>a list of 3 &homalg; matrices</Returns>
##    <Description>
##      The input is a &homalg; matrix <A>M</A>.
##      The output is a 3-tuple of &homalg; matrices <A>S</A>, <A>T</A>, <A>TI</A>
##      such that <A> M T = S</A>. Moreover, <A>T</A> is invertible with inverse <A>TI</A>.
##      The idea is that the matrix <A>S</A> should look "simpler" than <A>M</A>.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( SimplifyHomalgMatrixByRightMultiplicationWithInvertibleMatrix,
        "for homalg matrices",
        [ IsHomalgMatrix ],
        
    function( M )
        local R, RP, T, S;
        
        R := HomalgRing( M );
        
        RP := homalgTable( R );
        
        if IsBound(RP!.ReducedRowEchelonForm) or IsBound(RP!.ReducedColumnEchelonForm) then
            
            T := HomalgVoidMatrix( R );
            
            S := ReducedColumnEchelonForm( M, T );
            
        else
            
            T := HomalgIdentityMatrix( NumberColumns( M ), R );
            
            S := M;
            
        fi;
        
        return [ S, T, LeftInverseLazy( T ) ];
        
end );
