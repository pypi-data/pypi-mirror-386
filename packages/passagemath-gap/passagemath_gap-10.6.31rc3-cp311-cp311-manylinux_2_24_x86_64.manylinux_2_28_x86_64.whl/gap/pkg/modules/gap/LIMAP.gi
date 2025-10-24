# SPDX-License-Identifier: GPL-2.0-or-later
# Modules: A homalg based package for the Abelian category of finitely presented modules over computable rings
#
# Implementations
#

##         LIMAP = Logical Implications for homalg ring MAPs

####################################
#
# representations:
#
####################################

####################################
#
# methods for properties:
#
####################################

##
InstallMethod( IsMonomorphism,
        "LIMAP: for homalg ring maps",
        [ IsHomalgRingMapRep ],
        
  function( phi )
    
    return IsMorphism( phi ) and IsZero( Kernel( phi ) );
    
end );

####################################
#
# methods for attributes:
#
####################################

##
InstallMethod( KernelSubobject,
        "for homalg ring maps",
        [ IsHomalgRingMap ],
        
  function( phi )
    local rel, S;
    
    rel := GeneratorsOfKernelOfRingMap( phi );
    
    S := HomalgRing( rel );
    
    if IsBound( phi!.left ) and phi!.left = false then
        S := S * 1;
    else
        S := 1 * S; ## the default
    fi;
    
    return Subobject( rel, S );
    
end );

##
InstallMethod( KernelEmb,
        "for homalg ring maps",
        [ IsHomalgRingMap ],
        
  function( phi )
    
    return EmbeddingInSuperObject( KernelSubobject( phi ) );
    
end );

##
InstallMethod( IdealContainedInKernelViaEliminateOverBaseRing,
        [ IsHomalgRingMap ],
        
  function( phi )
    local T, mat, indetsT, lT, S, indetsS, lS, imgs, elim, zero, indets, iota;
    
    T := Range( phi );
    
    mat := MatrixOfRelations( T );
    
    T := AmbientRing( T );
    
    indetsT := Indeterminates( T );
    
    lT := Length( indetsT );
    
    S := Source( phi );
    
    indetsS := Indeterminates( S );
    
    lS := Length( indetsS );
    
    imgs := ImagesOfRingMap( phi );
    
    elim := Difference( indetsT, imgs );
    
    if not Length( elim ) = lT - lS then
        Error( imgs, " is not a sublist of ", indetsT, "\n" );
    fi;
    
    mat := EliminateOverBaseRing( mat, elim );
    
    ## computing a basis might be expensive (delaying the output)
    ## so leave it to the user or the next procedure
    #mat := BasisOfRows( mat );
    
    zero := Zero( S );
    
    indets := ListWithIdenticalEntries( lT, zero );
    
    imgs := PositionsProperty( indetsT, a -> a in imgs );
    
    indets{imgs} := indetsS;
    
    iota := RingMap( indets, T, S );
    
    mat := Pullback( iota, mat );
    
    if IsBound( phi!.left ) and phi!.left = false then
        S := S * 1;
    else
        S := 1 * S; ## the default
    fi;
    
    return Subobject( mat, S );
    
end );

####################################
#
# methods for operations:
#
####################################

##  <#GAPDoc Label="Kernel:ringmap">
##  <ManSection>
##    <Meth Arg="phi" Name="Kernel" Label="for ring maps"/>
##    <Returns>a &homalg; module</Returns>
##    <Description>
##      The kernel ideal of the ring map <A>phi</A> as an abstract module.
##    </Description>
##  </ManSection>
##  <#/GAPDoc>
##
InstallMethod( Kernel,
        "for homalg ring maps",
        [ IsHomalgRingMap ],
        
  function( phi )
    
    return UnderlyingObject( KernelSubobject( phi ) );
    
end );

