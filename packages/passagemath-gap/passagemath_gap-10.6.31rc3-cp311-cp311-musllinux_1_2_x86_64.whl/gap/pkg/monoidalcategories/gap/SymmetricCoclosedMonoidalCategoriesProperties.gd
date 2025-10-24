# SPDX-License-Identifier: GPL-2.0-or-later
# MonoidalCategories: Monoidal and monoidal (co)closed categories
#
# Declarations
#

#! @Description
#!  The property of the category <A>C</A> being symmetric coclosed monoidal.
#! @Arguments C
DeclareProperty( "IsSymmetricCoclosedMonoidalCategory", IsCapCategory );

AddCategoricalProperty( [ "IsSymmetricCoclosedMonoidalCategory", "IsSymmetricClosedMonoidalCategory" ] );
