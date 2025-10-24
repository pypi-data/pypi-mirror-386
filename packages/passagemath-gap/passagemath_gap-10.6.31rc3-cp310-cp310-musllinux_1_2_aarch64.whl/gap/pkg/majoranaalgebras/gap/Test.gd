#! @Chapter Functions for testing Majorana representations
#! @Section The main function

#! @Arguments rep
#! @Returns <A>true</A> if the algebra given by <A>rep</A> is indeed a Majorana algebra.
#! @Description Note: does not check that the algebra obeys axiom M2 (Norton's inequality), this can be separately tested using <Ref Func="MAJORANA_TestAxiomM2"/>.
DeclareGlobalFunction( "MajoranaAlgebraTest" );

DeclareGlobalFunction( "MAJORANA_TestOrthogonality" );

DeclareGlobalFunction( "MAJORANA_TestFusion" );

#! @Section Other functions

#! @Arguments rep
#! @Returns <A>true</A> if the inner product given by <A>rep.innerproducts</A> is a Frobenius form, otherwise returns false.
DeclareGlobalFunction( "MAJORANA_TestFrobeniusForm" );

#! @Arguments rep
#! @Returns <A>true</A> if the inner product given by <A>rep.innerproducts</A> is positive definite, otherwise returns false.
DeclareGlobalFunction( "MAJORANA_TestInnerProduct" );

#! @Arguments rep
#! @Returns <A>true</A> if the inner product given by <A>rep.innerproducts</A> obeys axiom M2 (Norton's inequality), otherwise returns false.
DeclareGlobalFunction( "MAJORANA_TestAxiomM2" );

DeclareGlobalFunction( "MAJORANA_TestEvecs" );

#! @Arguments rep
#! @Returns <A>true</A> if the 1-eigenspaces of all axes are 1-dimensional, otherwise returns false.
DeclareGlobalFunction( "MAJORANA_TestPrimitivity" );

DeclareGlobalFunction( "MAJORANA_TestSetup");

#! @BeginExampleSession
#! gap> G := AlternatingGroup(5);;
#! gap> T := AsList( ConjugacyClass(G, (1,2)(3,4)));;
#! gap> input := ShapesOfMajoranaRepresentation(G,T);;
#! gap> rep := MajoranaRepresentation(input, 2);;
#! gap> NClosedMajoranaRepresentation(rep);;
#! gap> MAJORANA_IsComplete(rep);
#! true
#! gap> MajoranaAlgebraTest(rep);
#! true
#! gap> MAJORANA_TestFrobeniusForm(rep);
#! true
#! gap> MAJORANA_TestInnerProduct(rep);
#! true
#! gap> MAJORANA_TestAxiomM2(rep);
#! true
#! gap> MAJORANA_TestPrimitivity(rep);
#! true
#! @EndExampleSession
