---
layout: post
title:  "Solving Einstein's Problem with SMT"
date:   2021-11-17 16:23:28 -0700
category: code
tags: [smt, python]
---

I recently became interested in learning about [boolean satisfiability (SAT)](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) and [satisfiability modulo theories (SMT)](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) as a novel way to answer questions. SAT/SMT seems to be a pretty well-kept secret - at least in the circles I run in.

I am at the very early stages of learning about SAT/SMT, and [as a way to help me learn it myself](https://www.psychologytoday.com/us/blog/how-be-brilliant/201206/the-prot-g-effect), I'm writing this post - with the additional hope that it might help others. For the purpose of this post, I'm conflating the terms SAT and SMT, and I don't define them here. The very high-level description of SAT is that we declare constraints over some boolean propositions and let the SMT solver figure it out; this is in contrast to trying to write some complicated or brute-force algorithm to figure it out for us. We declare these constraints using [s-expressions](https://en.wikipedia.org/wiki/S-expression) comprising the [SMT-LIB language](http://smt-lib.org/).

You can find the the final script and the generated input SMT-LIB and output model from this post [here](https://github.com/aeshirey/learn-sat-smt/tree/main/examples/einsteins-problem).

## Einstein's Problem
"Einstein's Problem" is the kind of logical thinking puzzle I used to do in high school: there are five houses, each of a different color, with an owner of a different nationality, etc. Each such property is unique; that is, exactly one house must be blue, exactly one owner drinks milk, exactly one owner keeps birds, and so on. There are also hints as to who lives in which house -- the owner of the blue house also drinks milk; the owner of the red house is neighbors with the beer drinker.

I did a search for Einstein's Problem and found [this website](http://www.chessandpoker.com/einsteins-problem-solution.html) as the first hit. So I copied all of the text of this problem as my input. It looks like this:

1. There are 5 houses (in a row) painted 5 different colors: Blue, Green, Red, White and Yellow.
2. In each house there lives a person of a different nationality: Brit, Dane, German, Norwegian or Swede.
3. These 5 owners each drink a certain beverage: Beer, Coffee, Milk, Tea or Water.
4. They also smoke a certain brand of cigar: Bluemaster, Dunhill, Pall Mall, Prince or Blend.
5. Additionally, they also keep a certain type of pet: Cats, Birds, Dogs, Fish or Horses.
6. The owners DO NOT have the same pet, smoke the same brand of cigar or drink the same beverage.

Then there are some clues:

1. The Brit lives in a Red house.
2. The Swede keeps Dogs as pets.
3. The Dane drinks Tea.
4. The Green house is on the left of the White house.
5. The Green house owner drinks Coffee.
6. The owner who smokes Pall Mall rears Birds.
7. The owner of the Yellow house smokes Dunhill.
8. The owner living in the center house drinks Milk.
9. The Norwegian lives in the first house.
10. The owner who smokes Blend lives next to the one who keeps Cats.
11. The owner who keeps horses lives next to the man who smokes Dunhill.
12. The owner who smokes Bluemaster drinks Beer.
13. The German smokes Prince.
14. The Norwegian lives next to the Blue house.
15. The owner who smokes Blend has a neighbor who drinks Water.

## Setting up the solution
To solve this puzzle, I wanted to stick with creating an .smt2 file fed to an SMT solver -- specifically, [Z3](https://github.com/Z3Prover/z3/) -- instead of using the [Python API](https://github.com/Z3Prover/z3/tree/master/src/api/python), for example. I did, however, make use of Python to generate all the s-exprs.

I started by creating functions for each property (blue, green, red, dog, horse, beer, Norwegian, etc.):

```
(declare-fun blue (Int) Bool)
(declare-fun green (Int) Bool)
(declare-fun red (Int) Bool)
(declare-fun white (Int) Bool)
(declare-fun yellow (Int) Bool)
```

This is done for all properties. The idea is to be able to call each of these functions with the house number, from 1 to 5 inclusive. For example, clue 9 says that the Norwegian lives in the first house, so we can constrain the solution to require this fact:

```
(assert (norwegian 1))
```

I programmatically generated these function declarations in Python by printing the generated s-exprs to stdout:

```python
parameters = {
    'colors': ['blue', 'green', 'red', 'white', 'yellow'],
    'nationalities': ['brit', 'dane', 'german', 'norwegian', 'swede'],
    'beverage': ['beer', 'coffee', 'milk', 'tea', 'water'],
    'cigar': ['bluemaster', 'dunhill', 'pallmall', 'prince', 'blend'],
    'pet': ['cat', 'bird', 'dog', 'fish', 'horse']
}

for (k, vs) in parameters.items():
    print(f'; functions for {k}:')
    for v in vs:
        print(f'(declare-fun {v} (Int) Bool)')
    print()
```

## Initial constraints
The definition of the puzzle is that each such parameter (or property) applies to exactly one house. That means that the function `blue` must be true for house 1, house 2, house 3, house 4, or house 5. This can be created as the boolean `or` of multiple functions:

```
(assert (or
    (blue 1)
    (blue 2)
    (blue 3)
    (blue 4)
    (blue 5)
))
```

This constrains the solution such that `blue` must be true for at least one of the houses. But we need to further constrain it so that it's true for _only_ one house. The way to do this is to generate a lot more constraints that require that it's not the case that `(blue i)` and `(blue j)` for each i and j such that i != j:

```
(assert (not (and (blue 1) (blue 2))))
(assert (not (and (blue 1) (blue 3))))
(assert (not (and (blue 1) (blue 4))))
(assert (not (and (blue 1) (blue 5))))
(assert (not (and (blue 2) (blue 3))))
(assert (not (and (blue 2) (blue 4))))
(assert (not (and (blue 2) (blue 5))))
(assert (not (and (blue 3) (blue 4))))
(assert (not (and (blue 3) (blue 5))))
(assert (not (and (blue 4) (blue 5))))
```

Note that adding multiple separate constraints (`assert` s-exprs) is the same as having a single s-expr as the conjunction (boolean `and`) of multiple s-exprs.

There's a further restriction -- this one bit me as I was debugging my nearly complete solution -- that once a property holds for a house, all other related properties must not hold. That is, if `(blue 4)` is true, then `(red 4)` must _not_ be true (which is the same as `(not (red 4))` must hold true). I then generated all of these s-exprs in Python:

```python
for (k, vs) in parameters.items():
    for v in vs:
        print(f'; at least one {v} house')
        ors = ' '.join(f'({v} {i})' for i in range(1, 6))
        print(f'(assert (or {ors}))')

        print(f'; but not more than one {v} house')
        for i in range(1, 5):
            for j in range(i+1, 6):
                print(f'(assert (not (and ({v} {i}) ({v} {j}))))')
        print()

    print(f'; A house can only match one {k} proposition')
    for v1 in vs:
        for v2 in vs:
            if v1 != v2:
                for i in range(1, 6):
                    print(f"(assert (not (and ({v1} {i}) ({v2} {i}))))")
    print()
```

Running these ~30 lines of Python generates almost 900 lines of SMT-LIB, and this sets up the baseline constraints.

## Adding the clues
The simplest clues are 8 and 9:

8. The owner living in the center house drinks Milk.
9. The Norwegian lives in the first house.

These are written as assertions that the `milk` function must hold true when invoked with `3`, the middle position, and that `norwegian` must hold when invoked with `1`:

```
(assert (milk 3))
(assert (norwegian 1))
```

Why do we not need to assert `(not (milk 2))`, `(not (brit 1))`, `(not (norwegian 4))`, and so on? Because The above constraints already do that for us: we're constraining such that `(milk 3)`, and we already have constraints that require exactly one house holds true for `milk` and that no other drink functions hold true for house 3.

Clue four is also quite easy:

4. The Green house is on the left of the White house.

If we knew that the white house was the third one (`(white 3)`), then we'd know that `(green 2)` must hold. Knowing _either_ of the properties here tells us what we need about the other, so it's not deducing white from green but constraining that both conditions must hold together. But we don't know which house it's in, so we can disjoin the four possibilities:

```
(assert (or
    (and (green 1) (white 2))
    (and (green 2) (white 3))
    (and (green 3) (white 4))
    (and (green 4) (white 5))
))
```

This combined constraint describes clue four.

## If and only if
The first clue is that the Brit lives in the red house, but we don't know which one it is. Using bidirectional implication -- if and only if, written as `iff` -- we can simply constrain:

```
(assert (iff (brit 1) (red 1)))
(assert (iff (brit 2) (red 2)))
(assert (iff (brit 3) (red 3)))
(assert (iff (brit 4) (red 4)))
(assert (iff (brit 5) (red 5)))
```

Colloquially, this says that if the Brit is in house 1 then house 1 must also be red, _and_ if house 1 is red then the Brit must live there. The two sides of the `iff` must match. This is all we need for the first clue, and this type of constraint applies to clues 2, 3, 5, 6, 7, 12, and 13. These are very simply generated in Python:

```python
for i in range(1, 6):
    print(f'(assert (iff (brit {i}) (red {i})))')
```

## Neighbor clues
The four remaining clues relate neighbors, such as

10. The owner who smokes Blend lives next to the one who keeps Cats.

This requires we relate previous and next neighbors, if they exist. For example:

```
(assert (or
    (and (blend 1) (cat 2)) ; house 1 has no 'previous' neighbor, check the next
    (and (blend 2) (cat 1)) ; check previous...
    (and (blend 2) (cat 3)) ; ...and next neighbor
    (and (blend 3) (cat 2))
    (and (blend 3) (cat 4))
    (and (blend 4) (cat 3)) ; etc
    (and (blend 4) (cat 5))
    (and (blend 5) (cat 4))))
```

I generate these with a helper function:

```python
def has_neighbor(prop1: str, prop2: str) -> str:
    ands = []
    for i in range(1, 6):
        for j in range(1, 6):
            if abs(i-j) == 1:
                ands.append(f'    (and ({prop1} {i}) ({prop2} {j}))')

    return '(assert (or\n'  + '\n'.join(ands) + '))\n'

print(has_neighbor('blend', 'cat'))
print(has_neighbor('horse', 'dunhill'))
print(has_neighbor('norwegian', 'blue'))
print(has_neighbor('blend', 'water'))
```

## Checking satisfiability
That's all we need to constrain the model! The last two s-expressions will check for satisfiability and will return the model:

```
(check-sat)
(get-model)
```

I print these out in Python and run the script, generating just over 1000 lines of SMT-LIB code. When I run that through Z3 using `z3 einstein-generated.smt2`, I get the following output:

```
sat
(
  (define-fun brit ((x!0 Int)) Bool
    (= x!0 3))
  (define-fun bluemaster ((x!0 Int)) Bool
    (= x!0 5))
  (define-fun dunhill ((x!0 Int)) Bool
    (= x!0 1))
  (define-fun cat ((x!0 Int)) Bool
    (= x!0 1))
  (define-fun norwegian ((x!0 Int)) Bool
    (= x!0 1))
  (define-fun coffee ((x!0 Int)) Bool
  ...
)
```

The first line, `sat`, is the result of `(check-sat)`, and it tells us that the constraints we've applied are satisfiable. The rest shows us a model that satisfies the constraints. For example, the first s-expr `(define-fun brit ((x!0 Int)) Bool (= x!0 3))` tells us that the `brit` function (which takes an int argument represented as `x!0` and returns a bool) is satisfied when its argument equals `3`; in other words, the `(brit 3)` constraint must evaluate to true in order for the model to hold. So the Brit lives in the third house.

Cleaning up the rest of these s-expressions gives the following details:

```
cat 1
dunhill 1
norwegian 1
water 1
yellow 1
blend 2
blue 2
dane 2
horse 2
tea 2
bird 3
brit 3
milk 3
pallmall 3
red 3
coffee 4
fish 4
german 4
green 4
prince 4
beer 5
bluemaster 5
dog 5
swede 5
white 5
```

Which can just be represented in a table as:

|       | House 1 | House 2 | House 3   | House 4 | House 5 |
|-------|---------|---------|-----------|---------|---------|
| Color | Yellow  | Blue    | Red       | Green   | White   |
| Pet   | Cat     | Horse   | Bird      | Fish    | Dog     |
| Cigar | Dunhill | Blend   | Pall Mall | Prince  | Bluemaster|
| Nation| Norwegian| Dane    | Brit      | German  | Swede   |
| Drink | Water   | Tea     | Milk      | Coffee  | Beer    |

And this is exactly the solution at the bottom of the linked page.

## Who keeps fish?
The direct question posed by this problem is, "Who keeps fish?" This table makes it easy to look it up -- the fish is at house 4, which is owned by the German. But presumably there's a way to ask this directly of the SAT solver: declare a variable, `owns_fish`, constrain that `(fish owns_fish)` must hold (which should bind this value to whatever house owns it). Then assert that `owns_fish` should be a value from 1 to 5:

```
(declare-const owns_fish Int)
(assert (fish owns_fish))

(assert (or
    (= 1 owns_fish)
    (= 2 owns_fish)
    (= 3 owns_fish)
    (= 4 owns_fish)
    (= 5 owns_fish)
))
(eval owns_fish) ; displays '4' when run
```

And we can further constrain a declared String to be returned by asserting that `natl_owns_fish` is equal to `"brit"` if `(brit owns_fish)` (which will hold only if the `brit` function is true for `owns_fish`), and so on:

```
(declare-const natl_owns_fish String)
(assert (= natl_owns_fish
    (ite (brit owns_fish) "brit"
    (ite (dane owns_fish) "dane"
    (ite (german owns_fish) "german"
    (ite (norwegian owns_fish) "norwegian" "swede"))))
))
(eval natl_owns_fish) ; "german"
```
