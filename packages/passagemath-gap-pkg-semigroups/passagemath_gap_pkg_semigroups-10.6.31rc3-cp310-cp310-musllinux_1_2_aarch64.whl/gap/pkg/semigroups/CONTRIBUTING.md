## Contributing to the Semigroups package for GAP

#### Copyright (C) 2011-2022 James D. Mitchell
#### Licensing information is available in the LICENSE file.   

We invite everyone to contribute by submitting patches, pull requests, and bug
reports. We would like to make the contributing process as easy as possible.

## Issue reporting and code contributions

* Before you report an issue, or wish to add functionality, please try
  and check to see if there are existing
  [issues](https://github.com/semigroups/Semigroups/issues) or
  [pull requests](https://github.com/semigroups/Semigroups/pulls).
  We do not want you wasting your time duplicating somebody else's work.
* For substantial changes it is also advisable to contact us before
  you start work to discuss your ideas.
* To help increase the chance of your pull request being accepted:
  * Run the tests.
  * Update the documentation, tests, examples, guides, and whatever
    else is affected by your contribution.
  * Use appropriate code formatting for both C and GAP (more details below).
* *The Campsite Rule*
  A basic rule when contributing to GAP is the **campsite rule**:
  leave the codebase in better condition than you found it.
  Please clean up any messes that you find, and don't
  leave behind new messes for the next contributor.

### Branches for contributions

Bugfixes and technical changes should be made in branches off the next release
branch, in a fork of the repository.  Releases are currently made from
`stable-3.1` branch.  If there is more than one open branch with this type of
name, then please use the lowest numbered such branch.

New features should be developed in branches off the `master` branch, in
a fork of the repository. You should regularly merge/rebase the `master` branch
into your feature branch.

When you think your changes are ready to go into
a release, please make a pull request.

Before asking us to merge your code please ensure that: 

* your code is documented and tested
* all of the tests run without errors
* you have used the coding conventions below

### Coding conventions

* 2 spaces for indentation
* continuation of lines containing `if`, `for`, `while` should be indented by
  an extra 2 spaces
* continuation of lines containing an opening bracket but not the matching
  closed bracket should be indented so that the content of the next line is
  aligned with the opening bracket. 
* no tabs
* no trailing whitespace
* no line containing more than one semicolon `;`
* no lines exceeding 80 characters
* the operators `+`, `:=`, `*` and so on, should be immediately preceded and
  followed by a space
* there should be no whitespace after an opening bracket or before a closing
  bracket
* there should be exactly one space after a comma `,` except if it is at the end
  of line
* there should not be adjacent empty lines
* there should not be variables which are declared but not used
* everything declared in the file `gap/blah.gd` should be documented in the file
  `doc/blah.xml`.  If a function or method is for internal use only, then its
  name should have the prefix `SEMIGROUPS_` or it should have the suffix `NC`.
  If a function or method is for use in one file only, then it should be
  assigned using `BindGlobal` in that file. 
* functions should only be assigned using the `foo := function()` syntax if they
  are local variables inside another function; all other functions should be global.
* error messages should give enough information for the user to know what they need
  to change. For example, if a function has received the wrong input type, an
  appropriate error to return is: `ErrorNoReturn("expected [something] as 2nd
  argument, found [something else]")`.
* functions and variables which will be unbound after they are read must have
 an underscore '_' at the start.
* non-user operations must start SEMIGROUPS_
* other non-user functions, variables etc should be stored inside the
 SEMIGROUPS global record (so that they do not pollute GAP with lots of
 internal names of functions). Remember that record look up can be expensive so
 if you need to use a function in SEMIGROUPS in a tight loop, then put it into
 a local variable.

Adapted from the contributing files for
[GAP](https://github.com/gap-system/gap/blob/master/CONTRIBUTING.md)

