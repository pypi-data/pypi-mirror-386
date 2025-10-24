############################################################################
##
#W  manual.tst 			The LPRES-package	        René Hartung
##

gap> START_TEST("Checking the examples from the manual...");

############################################################################
##
##  Section II An Introduction to L-presented groups
##
gap> Unbind(a); Unbind(b); Unbind(c); Unbind(d);
gap> F:=FreeGroup( "a", "b", "c", "d" );
<free group on the generators [ a, b, c, d ]>
gap> AssignGeneratorVariables( F );
#I  Assigned the global variables [ a, b, c, d ]
gap> frels:=[ a^2, b^2, c^2, d^2, b*c*d ];;
gap> endos:=[ GroupHomomorphismByImagesNC( F, F, [ a, b, c, d ], [ c^a, d, b, c ]) ];;
gap> irels:=[ Comm( d, d^a ), Comm( d, d^(a*c*a*c*a) ) ];;
gap> G:=LPresentedGroup( F, frels, endos, irels );
<LpGroup on the generators [ a, b, c, d ]>
gap> Unbind(a);Unbind(b);Unbind(c);Unbind(d);

gap> LamplighterGroup( IsLpGroup, 2 );
<LpGroup on the generators [ a, t, u ]>
gap> LamplighterGroup( IsLpGroup, CyclicGroup(3) );
<LpGroup on the generators [ a, t, u ]>

gap> F:=FreeGroup( 2 );;
gap> G:=LPresentedGroup( F, [ F.1^2 ], [ IdentityMapping( F ) ], [ F.2 ] );;
gap> FreeGroupOfLpGroup( G ) = F;
true
gap> GeneratorsOfGroup( G );
[ f1, f2 ]
gap> FreeGeneratorsOfLpGroup( G );
[ f1, f2 ]
gap> last = last2;
false
gap> UnderlyingElement( G.1 );
f1
gap> last in F;
true
gap> ElementOfLpGroup( ElementsFamily( FamilyObj( G ) ), last2 ) in G;
true

gap> F:=FreeGroup( 2 );;
gap> G:=LPresentedGroup( F, [ F.1^2 ], [ IdentityMapping( F ) ], [ F.2 ] );
<LpGroup on the generators [ f1, f2 ]>
gap> FixedRelatorsOfLpGroup( G );
[ f1^2 ]
gap> IteratedRelatorsOfLpGroup( G );
[ f2 ]
gap> EndomorphismsOfLpGroup( G );
[ IdentityMapping( <free group on the generators [ f1, f2 ]> ) ]

gap> F:=FreeGroup( "a", "b", "c", "d" );;
gap> AssignGeneratorVariables( F );
#I  Assigned the global variables [ a, b, c, d ]
gap> frels:=[ a^2, b^2, c^2, d^2, b*c*d ];;
gap> endos:=[ GroupHomomorphismByImagesNC( F, F, [ a, b, c, d ], [ c^a, d, b, c ]) ];;
gap> irels:=[ Comm( d, d^a ), Comm( d, d^(a*c*a*c*a) ) ];;
gap> G:=LPresentedGroup( F, frels, endos, irels );
<LpGroup on the generators [ a, b, c, d ]>
gap> SetUnderlyingInvariantLPresentation( G, G );;
gap> Unbind(a);Unbind(b);Unbind(c);Unbind(d);

gap> F := FreeGroup( "a" );
<free group on the generators [ a ]>
gap> H := F / [ F.1^3 ];
<fp group on the generators [ a ]>
gap> U := ExamplesOfLPresentations( 8 );
<invariant LpGroup of size infinity on the generators [ t, u, v ]>
gap> aut:=GroupHomomorphismByImagesNC( U, U, [ U.1, U.2, U.3 ], [ U.2, U.3, U.1 ] );
[ t, u, v ] -> [ u, v, t ]
gap> SplitExtensionByAutomorphismsLpGroup( U, H, [ aut ] );
<LpGroup on the generators [ t, u, v, a ]>

gap> F:=FreeGroup( 2 );
<free group on the generators [ f1, f2 ]>
gap> G:=F/[ F.1^2, F.2^2, Comm( F.1, F.2 ) ];
<fp group on the generators [ f1, f2 ]>
gap> IsomorphismLpGroup( G );
[ f1, f2 ] -> [ f1, f2 ]
gap> Range(last);
<invariant LpGroup on the generators [ f1, f2 ]>
gap> Display(last);
generators = [ f1, f2 ]
fixed relators = [ ]
endomorphism = [
IdentityMapping( <free group on the generators [ f1, f2 ]> ) ]
iterated relators = [
f1^2,
f2^2,
f1^-1*f2^-1*f1*f2 ]

############################################################################
## 
##  Section III Nilpotent Quotients of L-presented groups
##
gap> G := ExamplesOfLPresentations( 1 );;
gap> H := NilpotentQuotient( G, 5 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> lcs := LowerCentralSeries( H );
[ Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ],
  Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2 ],
  Pcp-group with orders [ 2, 2, 2, 2, 2 ], Pcp-group with orders [ 2, 2, 2 ],
  Pcp-group with orders [ 2, 2 ], Pcp-group with orders [  ] ]
gap> List( [ 1..5 ], x -> lcs[ x ] / lcs[ x+1 ] );
[ Pcp-group with orders [ 2, 2, 2 ], Pcp-group with orders [ 2, 2 ],
  Pcp-group with orders [ 2, 2 ], Pcp-group with orders [ 2 ],
  Pcp-group with orders [ 2, 2 ] ]

gap> G := ExamplesOfLPresentations( 1 );
<invariant LpGroup of size infinity on the generators [ a, b, c, d ]>
gap> epi := NqEpimorphismNilpotentQuotient( G, 5 );
[ a, b, c, d ] -> [ g1, g2*g3, g2, g3 ]
gap> H := Image( epi );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> NilpotencyClassOfGroup( H );
5
gap> H := NilpotentQuotient( G, 7 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> NilpotentQuotient( G, 10 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> NqEpimorphismNilpotentQuotient( G, H );
[ a, b, c, d ] -> [ g1, g2*g3, g2, g3 ]
gap> Image( last );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]

gap> G := ExamplesOfLPresentations( 1 );;
gap> AbelianInvariants( G );
[ 2, 2, 2 ]

gap> F := FreeGroup( "a", "b", "c", "d" );
<free group on the generators [ a, b, c, d ]>
gap> AssignGeneratorVariables( F );
#I  Assigned the global variables [ a, b, c, d ]
gap> rels := [ a^2, b^2, c^2, d^2, b*d*c ];;
gap> endos := [ GroupHomomorphismByImagesNC( F, F, [ a, b, c, d ], [ c^a, d, b, c ]) ];;
gap> itrels := [ Comm( d, d^a ), Comm( d, d^(a*c*a*c*a) ) ];;
gap> G := LPresentedGroup( F, rels, endos, itrels );
<LpGroup on the generators [ a, b, c, d ]>
gap> List( rels, x -> x^endos[1] );
[ a^-1*c^2*a, d^2, b^2, c^2, d*c*b ]

gap> SetIsInvariantLPresentation( G, true );
gap> NilpotentQuotient( G, 4 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> Unbind(a); Unbind(b); Unbind(c); Unbind(d);

gap> F := FreeGroup( "a", "b", "c", "d" );
<free group on the generators [ a, b, c, d ]>
gap> AssignGeneratorVariables( F );
#I  Assigned the global variables [ a, b, c, d ]
gap> rels := [ a^2, b^2, c^2, d^2, b*d*c ];;
gap> endos := [ GroupHomomorphismByImagesNC( F, F, [ a, b, c, d ], [ c^a, d, b, c ]) ];;
gap> itrels := [ Comm( d, d^a ), Comm( d, d^(a*c*a*c*a) ) ];;
gap> G := LPresentedGroup( F, rels, endos, itrels );
<LpGroup on the generators [ a, b, c, d ]>
gap> List( rels, x -> x^endos[1] );
[ a^-1*c^2*a, d^2, b^2, c^2, d*c*b ]

gap> U := LPresentedGroup( F, rels, endos, itrels );
<LpGroup on the generators [ a, b, c, d ]>
gap> SetUnderlyingInvariantLPresentation( G, U );
gap> NilpotentQuotient( G, 4 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> Unbind(a); Unbind(b); Unbind(c); Unbind(d);

gap> F := FreeGroup( "a", "b", "c", "d" );
<free group on the generators [ a, b, c, d ]>
gap> AssignGeneratorVariables( F );
#I  Assigned the global variables [ a, b, c, d ]
gap> rels := [ a^2, b^2, c^2, d^2, b*d*c ];;
gap> endos := [ GroupHomomorphismByImagesNC( F, F, [ a, b, c, d ], [ c^a, d, b, c ]) ];;
gap> itrels := [ Comm( d, d^a ), Comm( d, d^(a*c*a*c*a) ) ];;
gap> G := LPresentedGroup( F, rels, endos, itrels );
<LpGroup on the generators [ a, b, c, d ]>
gap> List( rels, x -> x^endos[1] );
[ a^-1*c^2*a, d^2, b^2, c^2, d*c*b ]

gap> SetUnderlyingInvariantLPresentation( G, UnderlyingAscendingLPresentation( G ) );
gap> NilpotentQuotient( G, 4 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> Unbind(a); Unbind(b); Unbind(c); Unbind(d);

############################################################################
##
##  Section IV The underlying functions
##
gap> G := ExamplesOfLPresentations( 1 );
<invariant LpGroup of size infinity on the generators [ a, b, c, d ]>
gap> Q := InitQuotientSystem( G );
rec( Definitions := [ 1, 3, 4 ], Epimorphism := [ a, b, c, d ] ->
    [ g1, g2*g3, g2, g3 ], Imgs := [ 1, [ 2, 1, 3, 1 ], 2, 3 ],
  Lpres := <invariant LpGroup of size infinity on the generators
    [ a, b, c, d ]>, Pccol := <<from the left collector with 3 generators>>,
  Weights := [ 1, 1, 1 ] )
gap> ExtendQuotientSystem( Q );
rec( Definitions := [ 1, 3, 4, [ 2, 1 ], [ 3, 1 ] ],
  Epimorphism := [ a, b, c, d ] -> [ g1, g2*g3, g2, g3 ],
  Imgs := [ 1, [ 2, 1, 3, 1 ], 2, 3 ],
  Lpres := <invariant LpGroup of size infinity on the generators
    [ a, b, c, d ]>, Pccol := <<from the left collector with 5 generators>>,
  Weights := [ 1, 1, 1, 2, 2 ] )
gap> G := ExamplesOfLPresentations( 1 );;
gap> NilpotentQuotient( G, 5 );
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 ]
gap> NilpotentQuotientSystem( G );
rec( Definitions := [ 1, 3, 4, [ 2, 1 ], [ 3, 1 ], [ 4, 2 ], [ 4, 3 ],
      [ 7, 1 ], [ 8, 2 ], [ 8, 3 ] ], Epimorphism := [ a, b, c, d ] ->
    [ g1, g2*g3, g2, g3 ], Imgs := [ 1, [ 2, 1, 3, 1 ], 2, 3 ],
  Lpres := <invariant LpGroup of size infinity on the generators
    [ a, b, c, d ]>, Pccol := <<from the left collector with 10 generators>>,
  Weights := [ 1, 1, 1, 2, 2, 3, 3, 4, 5, 5 ] )
gap> NilpotencyClassOfGroup( PcpGroupByCollectorNC( last.Pccol ) );
5

gap> G:=ExamplesOfLPresentations( 3 );;
gap> HasIsInvariantLPresentation( G );
false
gap> NilpotentQuotient( G, 3 );
Pcp-group with orders [ 0, 2, 2, 2 ]
gap> NilpotentQuotients( G );
[ [ a, t, u ] -> [ g2, g1, g2 ], [ a, t, u ] -> [ g2, g1, g2 ],
  [ a, t, u ] -> [ g2, g1, g2 ] ]
gap> Range( last[2] );
Pcp-group with orders [ 0, 2, 2 ]

gap> NilpotentQuotientSystem( UnderlyingInvariantLPresentation( G ) );
rec( Definitions := [ 1, 2, 3, [ 2, 1 ], [ 3, 2 ], [ 4, 1 ], [ 4, 2 ],
      [ 5, 2 ], [ 5, 3 ] ], Epimorphism := [ a, t, u ] -> [ g1, g2, g3 ],
  Imgs := [ 1, 2, 3 ], Lpres := <invariant LpGroup on the generators
    [ a, t, u ]>, Pccol := <<from the left collector with 9 generators>>,
  Weights := [ 1, 1, 1, 2, 2, 3, 3, 3, 3 ] )

gap> IL := InfoLevel(InfoLPRES);;
gap> SetInfoLevel( InfoLPRES, 1 );;
gap> G:=ExamplesOfLPresentations( 1 );
#I  The Grigorchuk group on 4 generators from [Lys85]
<invariant LpGroup of size infinity on the generators [ a, b, c, d ]>
gap> NilpotentQuotient( G, 3 );
#I  Class 1: 3 generators with relative orders: [ 2, 2, 2 ]
#I  Class 2: 2 generators with relative orders: [ 2, 2 ]
#I  Class 3: 2 generators with relative orders: [ 2, 2 ]
Pcp-group with orders [ 2, 2, 2, 2, 2, 2, 2 ]
gap> SetInfoLevel(InfoLPRES, IL);

################################################################
# L-presentation of IA subgroup
gap> f := FreeGroup(3);
<free group on the generators [ f1, f2, f3 ]>
gap> a := AutomorphismGroup(f);;
gap> map := EmbeddingOfIASubgroup(a);;
gap> ia := Source(map);
<invariant LpGroup on the generators [ C(1,2), C(1,3), C(2,1), C(2,3), C(3,1), C(3,2), M(1,[2,3]),
  M(2,[1,3]), M(3,[1,2]) ]>
gap> freemap := GroupHomomorphismByFunction(FreeGroupOfLpGroup(ia),a,x->ElementOfLpGroup(FamilyObj(One(ia)),x)^map);;
gap> ForAll(IteratedRelatorsOfLpGroup(ia),x->IsOne(x^freemap));
true
gap> endos := EndomorphismsOfLpGroup(ia);;
gap> ForAll([1..Length(endos)],i->ForAll(GeneratorsOfGroup(FreeGroupOfLpGroup(ia)),x->(x^endos[i])^freemap=(x^freemap)^ia!.Gendos[i]));
true

gap> STOP_TEST( "ManualExamples.tst", 100000);
