This file describes changes in the `InduceReduce` package.

1.3 (2025-10-16)
  - Set power maps in the character tables whose irreducibles have been
    computed by the `Irr` method that calls `IrrUnger`.

1.2 (2025-10-15)
  - In the `Irr` method that calls `IrrUnger`,
    delegate to `IrrBaumClausen` if the group is abelian-by-supersolvable;
    this is usually faster.

1.1 (2025-07-16)
  - Added `IrrUnger` function which is also installed as method for `Irr`,
    so that the code in this package is automatically used when applicable
  - Some code cleanup & refactoring, minor speed ups for some functionality
  - Fixed the test suite and set up continuous integration tests
  - Added Thomas Breuer and Max Horn as co-maintainers
  - Moved package to `gap-packages` organization
  - Various janitorial updates

1.0 (2018-09-04)
  - First public release
