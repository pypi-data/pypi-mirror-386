############################################################################
##
#W misc.gi			LPRES				René Hartung
##

############################################################################
##
#F  LPRES_WordsOfLengthAtMostN( <list>, <n> )
##   
## returns a list of all words of <list> of length at most <n>
##
InstallGlobalFunction( LPRES_WordsOfLengthAtMostN,
  function ( list, n )
  local Words,	# list of all words
	i,g;	# loop variables

# Words:=[ [ list[1]^0 ], list ];
  Words:=[ [ One( list[1] ) ], list ];
  for i in [ 3 .. n+1 ] do 
    Add( Words, [] );
    for g in list do 
      Append( Words[i], List( Words[i-1], x -> x*g ) );
    od;
  od;
  return( Concatenation( Words ) );
  end);

############################################################################
##
##  FrattiniSubgroup( <Pcp> )
## 
##  returns the Frattini subgroup of a nilpotent PcpGroup
## 
############################################################################
InstallMethod( FrattiniSubgroup,
  "for a nilpotent PcpGroup",
  [ IsPcpGroup ], 0,
  function(H)
  local DH,	# derived subgroup of <H>	
	delta,	# epimorphism into the abelian quotient of <H>
	T,	# Torsion subgroup of the abelian quotient 
	phi,	# isomorphism into the PcGroup
	Pc,	# PcGroup of the torsion group <T>
	Ff,F;   # Frattini subgroups of the abelian quotient
  
  if not IsNilpotent(H) then 
    TryNextMethod();
  fi;

  DH:=DerivedSubgroup(H);
  delta:=NaturalHomomorphismByNormalSubgroup(H,DH);
  T:=TorsionSubgroup(Range(delta));
  phi:=IsomorphismPcGroup(T);
  F:=FrattiniSubgroup(Range(phi));
  Ff:=PreImage(phi,F);

  return(PreImage(delta,Ff));
  end);

############################################################################
##
#F  LPRES_LowerCentralSeriesSections( <PcpGroup> )
## 
## returns either the p-ranks of the lower central series sections of 
## <PcpGroup> or its abelian invariants.
##
InstallGlobalFunction( LPRES_LowerCentralSeriesSections,
  function(H)
  local lcs,	# lower central series of <H>
	sec,	# a lower central series section
	A,	# ranks/abelian invariants
	i;	# loop variable

  if not HasLowerCentralSeriesOfGroup(H) then 
    Info(InfoLPRES, 1, "computing the lower central series first");
  fi;
  lcs:=LowerCentralSeries(H);

  A:=[];
  for i in [Length(lcs),Length(lcs)-1..2] do
    sec:=lcs[i-1]/lcs[i];
    if IsElementaryAbelian(sec) then 
      Info(InfoLPRES,1,"The ",i-1,"-th section has rank ",RankPGroup(sec));
      Add(A,RankPGroup(sec));
    else
      Info(InfoLPRES,1,"The ",i-1,"-th section has abelian invariants ",
                         AbelianInvariants(sec));
      Add(A,AbelianInvariants(sec));
    fi;
  od;
  return(Reversed(A));
  end);

############################################################################
##
#F  LPRES_LCSofGuptaSidki( <PcpGroup>, <prime> )
##
## computes the lower central series sections of the Gupta-Sidki group
## from an index-3 subgroup which is invariantly L-presented.
##
InstallGlobalFunction( LPRES_LCSofGuptaSidki,
  function( H )
  local lcs, 	# lower central series
	aut, 	# automorphism induced by the action of the cyclic group
	p,	# a prime 
	gens,	# first <p> generators of <H>
	C,	# cyclic group of order <p>
 	T;	# split extension via T

  if HasLowerCentralSeriesOfGroup(H) then 
    lcs:=LowerCentralSeries(H);
  else
    Error("must compute the lower central series first!");
  fi;
 
  p:=Exponent(lcs[Length(lcs)-1]/lcs[Length(lcs)]);

  gens:=GeneratorsOfGroup(H){[1..p]};

  Info(InfoLPRES,3,"determine automorphism induced by the action");
  aut:=GroupHomomorphismByImagesNC(H,H,gens,
                                   Concatenation(gens{[2..p]},[gens[1]]));

  C:=Range(IsomorphismPcpGroup(CyclicGroup(p)));
  T:=SplitExtensionByAutomorphisms(H,C,[aut]);

  Info(InfoLPRES,3,"split extension is \n",T);
  Info(InfoLPRES,3,"compute the lower central series");

  if IsFinite(T) then 
    lcs:=LowerCentralSeries(Range(IsomorphismPcGroup(T)));
  else
    lcs:=LowerCentralSeries(T);
  fi;

  if not HasLowerCentralSeriesOfGroup(T) then 
    SetLowerCentralSeriesOfGroup(T,lcs);
  fi;
  Info(InfoLPRES,3," done");

  return(LPRES_LowerCentralSeriesSections(T));
  end);
