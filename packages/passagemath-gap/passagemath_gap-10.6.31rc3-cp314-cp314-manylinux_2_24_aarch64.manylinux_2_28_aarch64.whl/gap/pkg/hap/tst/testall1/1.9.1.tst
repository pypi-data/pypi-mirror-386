#
gap> START_TEST("HAP library");
gap> x:=(1,2)(5,6)(7,8)(11,12);; y:=(2,3)(4,5)(8,9)(10,11);;
gap> z:=(3,4)(5,7)(6,8)(9,10);; G:=Group(x,y,z);;
gap> #CayleyGraphOfGroupDisplay(G,[x,y,z]);
gap> Y:=EquivariantTwoComplex(G);
Equivariant CW-complex of dimension 2

gap> F:=FundamentalGroupOfQuotient(Y);
<fp group on the generators [ x, y, z ]>
gap> RelatorsOfFpGroup(F);
[ x^2, y^2, z^2, z^-1*x^-1*z*x, z^-1*y^-1*z*y*z*y^-1, 
  y^-1*x^-1*(y*x)^2*y*x^-1*y^-1*x^-1 ]
gap> H:=Group(x*y,x*z,y*z);;
gap> W:=RestrictedEquivariantCWComplex(Y,H);
Equivariant CW-complex of dimension 2

gap> FH:=FundamentalGroupOfQuotient(W);
<fp group on the generators [ v, w, x, y, z ]>
gap> RelatorsOfFpGroup(FH);
[ v, v, w*x, x*w, y*z, z*y, z^-1*y*v, y^-1*v^-1*z, z^-1*w^-1*y*x*y*w^-1, 
  y^-1*x^-1*z*w*z*x^-1, x^-1*(w*v)^2*w*x^-1, w^-1*v^-1*x^3*v^-1*w^-1*v^-1 ]
gap> xz:=(1,2)(3,4)(5,8)(6,7)(9,10)(11,12);;
gap> yz:=(2,4,7,5,3)(6,8,10,11,9);;
gap> H:=Group(xz, yz);;
gap> W:=EquivariantTwoComplex(H);
Equivariant CW-complex of dimension 2

gap> FH:=FundamentalGroupOfQuotient(W);
<fp group on the generators [ x, y ]>
gap> RelatorsOfFpGroup(FH);
[ y^2, x^5, y^-1*(x*y)^2*x ]
gap> STOP_TEST( "tst.tst", 1000 );


