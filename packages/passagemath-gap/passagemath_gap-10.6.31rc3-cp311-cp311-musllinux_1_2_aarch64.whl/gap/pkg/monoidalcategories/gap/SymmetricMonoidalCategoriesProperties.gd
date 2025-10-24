# SPDX-License-Identifier: GPL-2.0-or-later
# MonoidalCategories: Monoidal and monoidal (co)closed categories
#
# Declarations
#

#! @Description
#!  The property of the category <A>C</A> being symmetric monoidal.
#! @Arguments C
DeclareProperty( "IsSymmetricMonoidalCategory", IsCapCategory );

AddCategoricalProperty( [ "IsSymmetricMonoidalCategory", "IsSymmetricMonoidalCategory" ] );
