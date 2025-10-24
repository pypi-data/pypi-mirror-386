############################################################################
##
##  elements/maxplusmat.gi
##  Copyright (C) 2015-2022                              James D. Mitchell
##
##  Licensing information can be found in the README file of this package.
##
#############################################################################
##

#############################################################################
## This file contains declarations for max-plus, min-plus, tropical max-plus,
## tropical min-plus matrices, projective.
##
## It is organized as follows:
##
##   1. Max-plus matrices
##
##   2. Min-plus matrices
##
##   3. Tropical matrices
##
##   4. Tropical max-plus matrices
##
##   5. Tropical min-plus matrices
##
##   6. Projective max-plus matrices
##
##   7. NTP matrices
##
##   8. Integer matrices TODO(later) remove integer matrix stuff to its own
##      file
##
#############################################################################

SEMIGROUPS.PlusMinMax := function(x, y)
  if x = infinity or y = infinity then
    return infinity;
  elif x = -infinity or y = -infinity then
    return -infinity;
  fi;
  return x + y;
end;

SEMIGROUPS.IdentityMat := function(x, zero, one)
  local n, id, i;
  n := Length(x![1]);
  id := List([1 .. n], x -> [1 .. n] * zero);
  for i in [1 .. n] do
    id[i][i] := one;
  od;
  return id;
end;

SEMIGROUPS.RandomIntegerMatrix := function(n, source)
  local out, i, j;

  out := List([1 .. n], x -> EmptyPlist(n));
  for i in [1 .. n] do
    for j in [1 .. n] do
      out[i][j] := Random(Integers);
      if out[i][j] = 0 and source <> false then
        out[i][j] := source;
      elif out[i][j] < 0 then
        out[i][j] := out[i][j] + 1;
      fi;
    od;
  od;
  return out;
end;

#############################################################################
## 1. Max-plus matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a max-plus matrix",
[IsMaxPlusMatrix], x -> "max-plus");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a max-plus matrix",
[IsMaxPlusMatrix], x -> IsMaxPlusMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons, "for IsMaxPlusMatrix",
[IsMaxPlusMatrix], x -> MaxPlusMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsMaxPlusMatrix", [IsMaxPlusMatrix],
{_} -> x -> IsInt(x) or x = -infinity);

InstallMethod(\*, "for max-plus matrices", [IsMaxPlusMatrix, IsMaxPlusMatrix],
function(x, y)
  local n, xy, val, i, j, k, PlusMinMax;

  n := Minimum(Length(x![1]), Length(y![1]));

  xy := List([1 .. n], x -> EmptyPlist(n));
  PlusMinMax := SEMIGROUPS.PlusMinMax;

  for i in [1 .. n] do
    for j in [1 .. n] do
      val := -infinity;
      for k in [1 .. n] do
        val := Maximum(val, PlusMinMax(x![i][k], y![k][j]));
      od;
      xy[i][j] := val;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a max-plus matrix",
[IsMaxPlusMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, -infinity, 0)));

InstallMethod(RandomMatrixCons, "for IsMaxPlusMatrix and pos int",
[IsMaxPlusMatrix, IsPosInt],
function(filter, n)
  return MatrixNC(filter,
                  SEMIGROUPS.RandomIntegerMatrix(n, -infinity));
end);

InstallMethod(AsMatrix,
"for IsMaxPlusMatrix and a tropical max-plus matrix",
[IsMaxPlusMatrix, IsTropicalMaxPlusMatrix],
{filter, mat} -> MatrixNC(filter, AsList(mat)));

InstallMethod(AsMatrix,
"for IsMaxPlusMatrix and a projective max-plus matrix",
[IsMaxPlusMatrix, IsProjectiveMaxPlusMatrix],
{filter, mat} -> MatrixNC(filter, AsList(mat)));

InstallMethod(AsMatrix,
"for IsMaxPlusMatrix, transformation",
[IsMaxPlusMatrix, IsTransformation],
{filter, x} -> AsMatrix(filter, x, DegreeOfTransformation(x)));

InstallMethod(AsMatrix,
"for IsMaxPlusMatrix, transformation, pos int",
[IsMaxPlusMatrix, IsTransformation, IsPosInt],
{filter, x, dim}
-> MatrixNC(filter, SEMIGROUPS.MatrixTrans(x, dim, -infinity, 0)));

## Method based on theorem 2, page 19, of:
## K.G. Farlow, Max-plus Algebra, Thesis.
## https://tinyurl.com/zzs38s4

InstallMethod(InverseOp, "for a max-plus matrix", [IsMaxPlusMatrix],
function(mat)
  local dim, seen_rows, seen_cols, out, row, col;
  dim := DimensionOfMatrixOverSemiring(mat);
  seen_rows := BlistList([1 .. dim], []);
  seen_cols := BlistList([1 .. dim], []);
  out := List([1 .. dim], x -> List([1 .. dim], y -> -infinity));
  for row in [1 .. dim] do
    for col in [1 .. dim] do
      if mat[row][col] <> -infinity then
        if seen_rows[row] or seen_cols[col] then
          return fail;
        fi;
        seen_rows[row] := true;
        seen_cols[col] := true;
        out[col][row] := -mat[row][col];
      fi;
    od;
  od;
  return Matrix(IsMaxPlusMatrix, out);
end);

## Method from lemma 3.1, page 3, in:
## S. Gaubert, On the burnside problem for semigroups of matrices in the
## (max, +) algebra, Semigroup Forum, Volume 52, pp 271-292, 1996.
## https://tinyurl.com/znhk52m

InstallMethod(SpectralRadius, "for a max-plus matrix", [IsMaxPlusMatrix],
function(mat)
  local dim, cm, mk, k, max;
  # Check for -infinity case
  if IsEmpty(DigraphAllSimpleCircuits(UnweightedPrecedenceDigraph(mat))) then
    return -infinity;
  fi;
  # Calculate the maximum cycle mean.
  dim := Length(AsList(mat)[1]);
  cm := [];
  mk := mat;
  for k in [1 .. dim] do
    max := Maximum(List([1 .. dim], x -> mk[x][x]));
    if max <> -infinity then
      Add(cm, max / k);
    fi;
    mk := mk * mat;
  od;
  return Maximum(cm);
end);

InstallMethod(UnweightedPrecedenceDigraph, "for a max-plus matrix",
[IsMaxPlusMatrix],
function(mat)
  # Generate and return digraph object
  return Digraph([1 .. DimensionOfMatrixOverSemiring(mat)],
                 {i, j} -> mat[i][j] <> -infinity);
end);

## Method from lemma 19, page 36, of:
## K.G. Farlow, Max-plus Algebra, Thesis.
## https://tinyurl.com/zzs38s4

InstallMethod(RadialEigenvector, "for a max-plus matrix", [IsMaxPlusMatrix],
function(m)
  local dim, pows, crit, out, n, i, k;

  dim := DimensionOfMatrixOverSemiring(m);
  # Method only valid for SpectralRadius = 0.
  if SpectralRadius(m) <> 0 then
    TryNextMethod();
  fi;

  pows := List([1 .. 2 * dim], k -> m ^ k);

  # Find first power of <m> with 0 in the diagonal and find the position of 0
  # in the diagonal
  for n in pows do
    crit := Position(List([1 .. dim], i -> n[i][i]), 0);
    if crit <> fail then
      break;
    fi;
  od;

  out := [1 .. dim] * -infinity;

  for i in [1 .. dim] do
    for k in [1 .. 2 * dim] do
      if pows[k][i][crit] > out[i] then
        out[i] := pows[k][i][crit];
      fi;
    od;
  od;

  if out[crit] < 0 then
    out[crit] := 0;
  fi;

  return out;
end);

#############################################################################
## 2. Min-plus matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a min-plus matrix",
[IsMinPlusMatrix], x -> "min-plus");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a min-plus matrix",
[IsMinPlusMatrix], x -> IsMinPlusMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons, "for IsMinPlusMatrix",
[IsMinPlusMatrix], x -> MinPlusMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsMinPlusMatrix", [IsMinPlusMatrix],
{filter} -> x -> IsInt(x) or x = infinity);

InstallMethod(\*, "for min-plus matrices", [IsMinPlusMatrix, IsMinPlusMatrix],
function(x, y)
  local n, xy, val, i, j, k, PlusMinMax;

  n := Minimum(Length(x![1]), Length(y![1]));

  xy := List([1 .. n], x -> EmptyPlist(n));
  PlusMinMax := SEMIGROUPS.PlusMinMax;

  for i in [1 .. n] do
    for j in [1 .. n] do
      val := infinity;
      for k in [1 .. n] do
        val := Minimum(val, PlusMinMax(x![i][k], y![k][j]));
      od;
      xy[i][j] := val;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a min-plus matrix",
[IsMinPlusMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, infinity, 0)));

InstallMethod(RandomMatrixCons, "for IsMinPlusMatrix and pos int",
[IsMinPlusMatrix, IsPosInt],
function(filter, n)
  return MatrixNC(filter,
                  SEMIGROUPS.RandomIntegerMatrix(n, infinity));
end);

InstallMethod(AsMatrix,
"for IsMinPlusMatrix and a tropical min-plus matrix",
[IsMinPlusMatrix, IsTropicalMinPlusMatrix],
{filter, mat} -> MatrixNC(filter, AsList(mat)));

InstallMethod(AsMatrix,
"for IsMinPlusMatrix, transformation",
[IsMinPlusMatrix, IsTransformation],
{filter, x} -> AsMatrix(filter, x, DegreeOfTransformation(x)));

InstallMethod(AsMatrix,
"for IsMinPlusMatrix, transformation, pos int",
[IsMinPlusMatrix, IsTransformation, IsPosInt],
{filter, x, dim}
-> MatrixNC(filter, SEMIGROUPS.MatrixTrans(x, dim, infinity, 0)));

#############################################################################
## 3. Tropical matrices
#############################################################################

InstallMethod(ThresholdTropicalMatrix, "for a tropical matrix",
[IsTropicalMatrix], x -> x![Length(x![1]) + 1]);

#############################################################################
## 4. Tropical max-plus matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a tropical max-plus matrix",
[IsTropicalMaxPlusMatrix], x -> "tropical max-plus");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a tropical max-plus matrix",
[IsTropicalMaxPlusMatrix], x -> IsTropicalMaxPlusMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons,
"for IsTropicalMaxPlusMatrix",
[IsTropicalMaxPlusMatrix], x -> TropicalMaxPlusMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsTropicalMaxPlusMatrix and pos int",
[IsTropicalMaxPlusMatrix, IsPosInt],
{filter, threshold}
-> x -> (IsInt(x) and x >= 0 and x <= threshold) or x = -infinity);

InstallMethod(\*, "for tropical max-plus matrices",
[IsTropicalMaxPlusMatrix, IsTropicalMaxPlusMatrix],
function(x, y)
  local n, threshold, xy, PlusMinMax, val, i, j, k;

  n := Minimum(Length(x![1]), Length(y![1]));
  threshold := ThresholdTropicalMatrix(x);
  if threshold <> ThresholdTropicalMatrix(y) then
    ErrorNoReturn("the arguments (tropical max-plus matrices)",
                  "do not have the same threshold");
  fi;
  xy := List([1 .. n], x -> EmptyPlist(n));
  PlusMinMax := SEMIGROUPS.PlusMinMax;

  for i in [1 .. n] do
    for j in [1 .. n] do
      val := -infinity;
      for k in [1 .. n] do
        val := Maximum(val, PlusMinMax(x![i][k], y![k][j]));
      od;
      if val > threshold then
        val := threshold;
      fi;
      xy[i][j] := val;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a tropical max-plus matrix",
[IsTropicalMaxPlusMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, -infinity, 0)));

InstallMethod(RandomMatrixCons,
"for IsTropicalMaxPlusMatrix, pos int, pos int",
[IsTropicalMaxPlusMatrix, IsPosInt, IsPosInt],
function(filter, dim, threshold)
  local mat;
  mat := SEMIGROUPS.RandomIntegerMatrix(dim, -infinity);
  mat := SEMIGROUPS.TropicalizeMat(mat, threshold);
  return MatrixNC(filter, mat);
end);

InstallMethod(AsMatrix,
"for IsTropicalMaxPlusMatrix, max-plus matrix, and pos int",
[IsTropicalMaxPlusMatrix, IsMaxPlusMatrix, IsPosInt],
function(filter, mat, threshold)
  return MatrixNC(filter, SEMIGROUPS.TropicalizeMat(AsMutableList(mat),
                                                    threshold));
end);

InstallMethod(AsMatrix,
"for IsTropicalMaxPlusMatrix, projective max-plus matrix, and pos int",
[IsTropicalMaxPlusMatrix, IsProjectiveMaxPlusMatrix, IsPosInt],
function(filter, mat, threshold)
  return MatrixNC(filter, SEMIGROUPS.TropicalizeMat(AsMutableList(mat),
                                                    threshold));
end);

# change the threshold

InstallMethod(AsMatrix,
"for IsTropicalMaxPlusMatrix, max-plus matrix, and pos int",
[IsTropicalMaxPlusMatrix, IsTropicalMaxPlusMatrix, IsPosInt],
function(filter, mat, threshold)
  return MatrixNC(filter, SEMIGROUPS.TropicalizeMat(AsMutableList(mat),
                                                    threshold));
end);

InstallMethod(AsMatrix,
"for IsTropicalMaxPlusMatrix, transformation, IsPosInt",
[IsTropicalMaxPlusMatrix, IsTransformation, IsPosInt],
{filter, x, threshold}
-> AsMatrix(filter, x, DegreeOfTransformation(x), threshold));

InstallMethod(AsMatrix,
"for IsTropicalMaxPlusMatrix, transformation, pos int, pos int",
[IsTropicalMaxPlusMatrix, IsTransformation, IsPosInt, IsPosInt],
function(filter, x, dim, threshold)
  local mat;
  mat := SEMIGROUPS.MatrixTrans(x, dim, -infinity, 0);
  return MatrixNC(filter,
                  SEMIGROUPS.TropicalizeMat(mat, threshold));
end);

#############################################################################
## 5. Tropical min-plus matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a tropical min-plus matrix",
[IsTropicalMinPlusMatrix], x -> "tropical min-plus");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a tropical min-plus matrix",
[IsTropicalMinPlusMatrix], x -> IsTropicalMinPlusMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons,
"for IsTropicalMinPlusMatrix",
[IsTropicalMinPlusMatrix], x -> TropicalMinPlusMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsTropicalMinPlusMatrix and pos int",
[IsTropicalMinPlusMatrix, IsPosInt],
{filter, threshold}
-> x -> (IsInt(x) and x >= 0 and x <= threshold) or x = infinity);

InstallMethod(\*, "for tropical min-plus matrices",
[IsTropicalMinPlusMatrix, IsTropicalMinPlusMatrix],
function(x, y)
  local n, threshold, xy, PlusMinMax, val, i, j, k;

  n := Minimum(Length(x![1]), Length(y![1]));
  threshold := ThresholdTropicalMatrix(x);
  if threshold <> ThresholdTropicalMatrix(y) then
    ErrorNoReturn("the arguments (tropical min-plus matrices) ",
                  "do not have the same threshold");
  fi;

  xy := List([1 .. n], x -> EmptyPlist(n));
  PlusMinMax := SEMIGROUPS.PlusMinMax;

  for i in [1 .. n] do
    for j in [1 .. n] do
      val := infinity;
      for k in [1 .. n] do
        val := Minimum(val, PlusMinMax(x![i][k], y![k][j]));
      od;
      if val <> infinity and val > threshold then
        val := threshold;
      fi;
      xy[i][j] := val;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a tropical min-plus matrix",
[IsTropicalMinPlusMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, infinity, 0)));

InstallMethod(RandomMatrixCons,
"for IsTropicalMinPlusMatrix, pos int, pos int",
[IsTropicalMinPlusMatrix, IsPosInt, IsPosInt],
function(filter, dim, threshold)
  local mat;
  mat := SEMIGROUPS.RandomIntegerMatrix(dim, infinity);
  mat := SEMIGROUPS.TropicalizeMat(mat, threshold);
  return MatrixNC(filter, mat);
end);

InstallMethod(AsMatrix,
"for IsTropicalMinPlusMatrix, min-plus matrix, and pos int",
[IsTropicalMinPlusMatrix, IsMinPlusMatrix, IsPosInt],
function(filter, mat, threshold)
  return MatrixNC(filter, SEMIGROUPS.TropicalizeMat(AsMutableList(mat),
                                                    threshold));
end);

# change the threshold

InstallMethod(AsMatrix,
"for IsTropicalMinPlusMatrix, min-plus matrix, and pos int",
[IsTropicalMinPlusMatrix, IsTropicalMinPlusMatrix, IsPosInt],
function(filter, mat, threshold)
  return MatrixNC(filter, SEMIGROUPS.TropicalizeMat(AsMutableList(mat),
                                                    threshold));
end);

InstallMethod(AsMatrix,
"for IsTropicalMinPlusMatrix, transformation, IsPosInt",
[IsTropicalMinPlusMatrix, IsTransformation, IsPosInt],
{filter, x, threshold}
-> AsMatrix(filter, x, DegreeOfTransformation(x), threshold));

InstallMethod(AsMatrix,
"for IsTropicalMinPlusMatrix, transformation, pos int, pos int",
[IsTropicalMinPlusMatrix, IsTransformation, IsPosInt, IsPosInt],
function(filter, x, dim, threshold)
  local mat;
  mat := SEMIGROUPS.MatrixTrans(x, dim, infinity, 0);
  return MatrixNC(filter,
                  SEMIGROUPS.TropicalizeMat(mat, threshold));
end);

#############################################################################
## 6. Projective max-plus matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a projective max-plus matrix",
[IsProjectiveMaxPlusMatrix], x -> "projective max-plus");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a projective max-plus matrix",
[IsProjectiveMaxPlusMatrix], x -> IsProjectiveMaxPlusMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons,
"for IsProjectiveMaxPlusMatrix",
[IsProjectiveMaxPlusMatrix], x -> ProjectiveMaxPlusMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsProjectiveMaxPlusMatrix",
[IsProjectiveMaxPlusMatrix],
{filter} -> x -> IsInt(x) or x = -infinity);

InstallMethod(\*, "for projective max-plus matrices",
[IsProjectiveMaxPlusMatrix, IsProjectiveMaxPlusMatrix],
function(x, y)
  local n, xy, norm, PlusMinMax, val, i, j, k;

  n := Minimum(Length(x![1]), Length(y![1]));
  xy := List([1 .. n], x -> EmptyPlist(n));
  norm := -infinity;
  PlusMinMax := SEMIGROUPS.PlusMinMax;

  for i in [1 .. n] do
    for j in [1 .. n] do
      val := -infinity;
      for k in [1 .. n] do
        val := Maximum(val, PlusMinMax(x![i][k], y![k][j]));
      od;
      xy[i][j] := val;
      if val > norm then
        norm := val;
      fi;
    od;
  od;

  for i in [1 .. n] do
    for j in [1 .. n] do
      if xy[i][j] <> -infinity then
        xy[i][j] := xy[i][j] - norm;
      fi;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a projective max-plus matrix",
[IsProjectiveMaxPlusMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, -infinity, 0)));

InstallMethod(RandomMatrixCons, "for IsProjectiveMaxPlusMatrix and pos int",
[IsProjectiveMaxPlusMatrix, IsPosInt],
function(filter, n)
  return MatrixNC(filter,
                  SEMIGROUPS.RandomIntegerMatrix(n, -infinity));
end);

InstallMethod(AsMatrix,
"for IsProjectiveMaxPlusMatrix, max-plus matrix",
[IsProjectiveMaxPlusMatrix, IsMaxPlusMatrix],
{filter, mat} -> MatrixNC(filter, AsList(mat)));

InstallMethod(AsMatrix,
"for IsProjectiveMaxPlusMatrix, tropical max-plus matrix",
[IsProjectiveMaxPlusMatrix, IsTropicalMaxPlusMatrix],
{filter, mat} -> MatrixNC(filter, AsList(mat)));

InstallMethod(AsMatrix,
"for IsProjectiveMaxPlusMatrix, transformation",
[IsProjectiveMaxPlusMatrix, IsTransformation],
{filter, x} -> AsMatrix(filter, x, DegreeOfTransformation(x)));

InstallMethod(AsMatrix,
"for IsProjectiveMaxPlusMatrix, transformation, pos int",
[IsProjectiveMaxPlusMatrix, IsTransformation, IsPosInt],
{filter, x, dim}
-> MatrixNC(filter, SEMIGROUPS.MatrixTrans(x, dim, -infinity, 0)));

#############################################################################
## 7. NTP matrices
#############################################################################

InstallMethod(ThresholdNTPMatrix, "for a natural matrix",
[IsNTPMatrix], x -> x![DimensionOfMatrixOverSemiring(x) + 1]);

InstallMethod(PeriodNTPMatrix, "for a natural matrix",
[IsNTPMatrix], x -> x![DimensionOfMatrixOverSemiring(x) + 2]);

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a natural number matrix",
[IsNTPMatrix], x -> "ntp");

InstallMethod(SEMIGROUPS_FilterOfMatrixOverSemiring,
"for a ntp matrix",
[IsNTPMatrix], x -> IsNTPMatrix);

InstallMethod(SEMIGROUPS_TypeOfMatrixOverSemiringCons, "for IsNTPMatrix",
[IsNTPMatrix], x -> NTPMatrixType);

InstallMethod(SEMIGROUPS_MatrixOverSemiringEntryCheckerCons,
"for IsNTPMatrix, pos int, pos int", [IsNTPMatrix, IsInt, IsInt],
function(_, threshold, period)
  if threshold < 0  then
    ErrorNoReturn("the 2nd argument (a pos. int.) is not >= 0");
  elif period <= 0 then
    ErrorNoReturn("the 3rd argument (a pos. int.) is not > 0");
  fi;
  return x -> (IsInt(x) and x >= 0 and x <= threshold + period - 1);
end);

InstallMethod(\*, "for natural number matrices",
[IsNTPMatrix, IsNTPMatrix],
function(x, y)
  local n, period, threshold, xy, i, j, k;

  n := Minimum(Length(x![1]), Length(y![1]));
  period := PeriodNTPMatrix(x);
  threshold := ThresholdNTPMatrix(x);

  if period <> PeriodNTPMatrix(y) or threshold <> ThresholdNTPMatrix(y) then
    ErrorNoReturn("the arguments (ntp matrices) are not over the same ",
                  "semiring");
  fi;

  xy := List([1 .. n], x -> EmptyPlist(n));

  for i in [1 .. n] do
    for j in [1 .. n] do
      xy[i][j] := 0;
      for k in [1 .. n] do
        xy[i][j] := xy[i][j] + x![i][k] * y![k][j];
      od;
      if xy[i][j] > threshold then
        xy[i][j] := threshold + (xy[i][j] - threshold) mod period;
      fi;
    od;
  od;
  return MatrixNC(x, xy);
end);

InstallMethod(OneImmutable, "for a ntp matrix",
[IsNTPMatrix],
x -> MatrixNC(x, SEMIGROUPS.IdentityMat(x, 0, 1)));

InstallMethod(RandomMatrixCons, "for IsNTPMatrix, pos int, pos int, pos int",
[IsNTPMatrix, IsPosInt, IsInt, IsInt],
function(filter, dim, threshold, period)
  local mat;
  mat := SEMIGROUPS.RandomIntegerMatrix(dim, false);
  mat := SEMIGROUPS.NaturalizeMat(mat, threshold, period);
  return MatrixNC(filter, mat);
end);

InstallMethod(AsMatrix,
"for IsNTPMatrix, ntp matrix, pos int, pos int",
[IsNTPMatrix, IsNTPMatrix, IsPosInt, IsPosInt],
function(filter, mat, threshold, period)
  return MatrixNC(filter, SEMIGROUPS.NaturalizeMat(AsMutableList(mat),
                                                   threshold,
                                                   period));
end);

InstallMethod(AsMatrix,
"for IsNTPMatrix, ntp matrix, pos int, pos int",
[IsNTPMatrix, IsMatrixObj, IsPosInt, IsPosInt],
function(filter, mat, threshold, period)
  if BaseDomain(mat) <> Integers then
    TryNextMethod();
  fi;
  return MatrixNC(filter, SEMIGROUPS.NaturalizeMat(Unpack(mat),
                                                   threshold,
                                                   period));
end);

InstallMethod(AsMatrix,
"for IsNTPMatrix, transformation, pos int, pos int",
[IsNTPMatrix, IsTransformation, IsPosInt, IsPosInt],
{filter, x, threshold, period}
-> AsMatrix(filter, x, DegreeOfTransformation(x), threshold, period));

InstallMethod(AsMatrix,
"for IsNTPMatrix, transformation, pos int, pos int, pos int",
[IsNTPMatrix, IsTransformation, IsPosInt, IsPosInt, IsPosInt],
function(filter, x, dim, threshold, period)
  local mat;
  mat := SEMIGROUPS.MatrixTrans(x, dim, 0, 1);
  return MatrixNC(filter,
                  SEMIGROUPS.NaturalizeMat(mat, threshold, period));
end);

#############################################################################
## 8. Integer matrices
#############################################################################

InstallMethod(SEMIGROUPS_TypeViewStringOfMatrixOverSemiring,
"for a matrix obj",
[IsMatrixObj],
function(x)
  if BaseDomain(x) = Integers then
    return "integer";
  fi;
  TryNextMethod();
end);

InstallMethod(OneImmutable, "for an integer matrix obj",
[IsMatrixObj],
function(x)
  if BaseDomain(x) <> Integers or IsList(x) then
    TryNextMethod();
  fi;
  return Matrix(x, SEMIGROUPS.IdentityMat(x, 0, 1));
end);

InstallMethod(RandomMatrixOp, "for Integers and pos int",
[IsIntegers, IsPosInt],
{semiring, n} -> Matrix(semiring, SEMIGROUPS.RandomIntegerMatrix(n, false)));

# TODO(MatrixObj-later) this method should be in the GAP library
InstallMethod(Order, "for an integer matrix obj",
[IsMatrixObj],
function(mat)
  if not IsIntegers(BaseDomain(mat)) then
    TryNextMethod();
  fi;
  return Order(Unpack(mat));
end);

InstallMethod(IsTorsion, "for an integer matrix obj",
[IsMatrixObj],
function(mat)
  if not IsIntegers(BaseDomain(mat)) then
    TryNextMethod();
  fi;
  return Order(mat) <> infinity;
end);

InstallMethod(Matrix,
"for Integers and transformation",
[IsIntegers, IsTransformation],
{semiring, x} -> Matrix(semiring, x, DegreeOfTransformation(x)));

InstallMethod(Matrix,
"for Integers, transformation, pos int",
[IsIntegers, IsTransformation, IsPosInt],
function(semiring, x, dim)
  return Matrix(semiring,
                SEMIGROUPS.MatrixTrans(x, dim, 0, 1));
end);
