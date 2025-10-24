gap> SetInfoLevel(InfoMajorana, 0);

##
## Test each part of main loop on A5 shape 4
##
gap> ex := MAJORANA_Example_A5();;
gap> rep := MAJORANA_SetUp(ex, 4, rec( axioms := "AllAxioms"));;
gap> MAJORANA_FindInnerProducts(rep);;
gap> AsSet(rep.innerproducts) = AsSet([ 1, 1/8, 13/256, 3/128, 3/128, 1/4, 8/5, 0, 875/524288, 1/9, 1/18, 1/18, 49/16384, -49/16384, false, 16/405, 35/4608, -35/4608, 203/524288 ]);
true
gap> MAJORANA_Fusion(rep);;
gap> Nrows(rep.evecs[1].("0"));
9
gap> dim := Size(rep.setup.coords);;
gap> mat := SparseMatrix(0, 0, [], [], Rationals);;
gap> vec := SparseMatrix(0, dim, [], [], Rationals);;
gap> unknowns := [];;
gap> system := rec( mat := mat, vec := vec, unknowns := unknowns );;
gap> MAJORANA_EigenvectorsAlgebraUnknowns(system, rep);;
gap> MajoranaAlgebraTest(rep);
true
gap> MAJORANA_FindInnerProducts(rep);;
gap> MAJORANA_Fusion(rep);;
gap> MAJORANA_FindAlgebraProducts(rep);;
gap> MajoranaAlgebraTest(rep);
true

##
## Now test all of the smaller components on A5 shape 4
##
gap> ex := MAJORANA_Example_A5();;
gap> rep := MAJORANA_SetUp(ex, 4, rec(axioms := "AllAxioms"));;

##
## Test bad indices func
##
gap> u := SparseMatrix( 1, 21, [[16]], [[1]], Rationals);;
gap> Size(MAJORANA_FindBadIndices(u, rep));
27

##
## Test add evec func
##
gap> mat := SparseIdentityMatrix(5, Rationals);;
gap> u := SparseMatrix( 1, 5, [[1]], [[2]], Rationals);;
gap> MAJORANA_AddEvec(mat, u);;
gap> Nrows(mat);
5
gap> u := SparseMatrix( 1, 5, [[1, 2]], [[1, 1]], Rationals);;
gap> MAJORANA_AddEvec(mat, u);;
gap> Nrows(mat);
5

##
## Test conjugate vec func
##
gap> v := rep.algebraproducts[8];;
gap> g := rep.setup.pairconjelts[55];;
gap> v := MAJORANA_ConjugateVec( v, g );;
gap> v!.indices;
[ [ 1, 5, 9, 15, 26 ] ]
gap> v!.entries;
[ [ -7/4096, 7/4096, -7/4096, 7/4096, 7/32 ] ]

##
## Test algebra product func
##
gap> u := SparseMatrix( 1, 21, [[1]], [[1]], Rationals);;
gap> v := SparseMatrix( 1, 21, [[19]], [[1]], Rationals);;
gap> MAJORANA_AlgebraProduct(u, v, rep.algebraproducts, rep.setup);
false
gap> v := SparseMatrix( 1, 21, [[16]], [[1]], Rationals);;
gap> v := MAJORANA_AlgebraProduct(u, v, rep.algebraproducts, rep.setup) ;;
gap> v!.indices;
[ [ 1, 4, 7, 16 ] ]
gap> v!.entries;
[ [ 2/9, -1/9, -1/9, 5/32 ] ]

##
## Test inner product func
##
gap> u := SparseMatrix( 1, 21, [[1]], [[1]], Rationals);;
gap> v := SparseMatrix( 1, 21, [[19]], [[1]], Rationals);;
gap> MAJORANA_InnerProduct(u, v, rep.innerproducts, rep.setup);
false
gap> v := SparseMatrix( 1, 21, [[16]], [[1]], Rationals);;
gap> MAJORANA_InnerProduct(u, v, rep.innerproducts, rep.setup);
1/4

##
## Test fill Gram matrix function
##
gap> gram := MAJORANA_FillGramMatrix( [1..15], rep.innerproducts, rep.setup);;
gap> Determinant( ConvertSparseMatrixToMatrix(gram) );
242191370790963017483378115234375/324518553658426726783156020576256

##
## Test IntersectEigenspaces
##
gap> ex := MAJORANA_Example_S4T1();;
gap> rep := MAJORANA_SetUp(ex, 2, rec( axioms := "AllAxioms"));;
gap> MAJORANA_IntersectEigenspaces(rep);;
gap> MAJORANA_Dimension(rep);
0

##
## Test the unknown inner product functions
##
gap> mat := SparseMatrix( 1, 5, [ [ 1, 4 ] ], [ [ 1, -1 ] ], Rationals );;
gap> vec := SparseMatrix( 1, 1, [ [ 1 ] ], [ [ 7123/518400 ] ], Rationals );;
gap> unknowns := [1..5];;
gap> innerproducts := [false, 289/57600, 1321/518400, false, 23/5184 ];;
gap> system := rec(mat := mat, vec := vec, unknowns := unknowns);;
gap> MAJORANA_RemoveKnownInnProducts(system, innerproducts);;
gap> system.unknowns;
[ 1, 4 ]
gap> eq := [ SparseMatrix( 1, 3, [ [ 1 ] ], [ [ -1 ] ], Rationals ), SparseMatrix( 1, 1, [ [ 1 ] ], [ [ -1/8192 ] ], Rationals ) ];;
gap> mat := SparseMatrix( 0, 3, [  ], [  ], Rationals );;
gap> vec := SparseMatrix( 0, 1, [  ], [  ], Rationals );;
gap> unknowns := [ 1, 2, 3 ];;
gap> system := rec(mat := mat, vec := vec, unknowns := unknowns);;
gap> innerproducts := [ false, false, false ];;
gap> MAJORANA_SingleInnerSolution( eq, system, innerproducts );;
gap> innerproducts;
[ 1/8192, false, false ]
gap> mat := SparseMatrix( 1, 1, [ [ 1 ] ], [ [ 1 ] ], Rationals );;
gap> vec := SparseMatrix( 1, 1, [ [ 1 ] ], [ [ 1/2 ] ], Rationals );;
gap> unknowns := [ 1 ];;
gap> innerproducts := [ false ];;
gap> system := rec(mat := mat, vec := vec, unknowns := unknowns);;
gap> MAJORANA_SolutionInnerProducts(system, innerproducts);;
gap> innerproducts;
[ 1/2 ]
