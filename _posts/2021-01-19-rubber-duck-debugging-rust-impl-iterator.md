---
layout: post
title:  "Rubber duck debugging & Rust `impl Iterator`"
date:   2021-01-19 22:35:51 -0700
category: code
tags: [blog, rust]
---

Years ago, I learned about [rubber duck debugging](https://hwrnmnbsol.livejournal.com/148664.html)\*. I told my boss about it, and she got such a kick out of it that when I arrived at work the next day, there was an actual, bathtub-style rubber duckie sitting on my desk.

**TLDR**: When you run into a problem, ask the rubber duck. Just by talking to the duck (read: yourself), you can often find the answer.

I ran into an issue in dealing with iterators in Rust that I couldn't quite wrap my head around. Given some immutable data, I wanted to create an iterator (using `.iter()` and **not** `.into_iter()`), pass that iterator around, and have my application very efficiently, lazily evaluate the iterator. If I were writing some code in C# using `IEnumerable<T>`, it would be drop-dead easy:

```csharp
public static void Main()
{
    int[] myData = new int[] { 1, 2, 3, 4, 5, 6 };
    var p1 = plus1(myData);
    var x2 = times2(p1);
    printData(x2);
}

private static IEnumerable<int> plus1(IEnumerable<int> data)
{
    return data.Select(i => i + 1);
}

private static IEnumerable<int> times2(IEnumerable<int> data)
{
    return data.Select(i => i * 2);
}

private static void printData(IEnumerable<int> data)
{
    foreach (int i in data)
    {
        Console.WriteLine(i);
    }
}
```

Here, we can pass around an `IEnumerable` that isn't evaluated until we force it in the `printData` function. Easy peasy.

It's less obvious in Rust, though. I couldn't figure it out, and as I started writing up a question for StackOverflow, I started to 'rubber duck' the problem. It took me about an hour to write, rewrite, debug, rewrite again, scratch my head, and eventually figure out how to do this reasonably well in Rust.

The first thing to know is that you might use `impl Iterator<Item = T>`. The [`impl Trait` syntax](https://doc.rust-lang.org/edition-guide/rust-2018/trait-system/impl-trait-for-returning-complex-types-with-ease.html) lets us specify that we're passing some unspecified but concrete type that implements the `Iterator<Item = T>` trait. With the above example from C#, we'd be using `Iterator<Item = i32>`.

The other thing to know is that C# will automatically resolve the `int[]` to `IEnumerable<int>` – an array `T[]` is itself an `IEnumerable<T>` – so you can simply call `plus1(myData)` without explicitly casting/converting between the types. Not so in Rust.

I started with a simple translation like so:

```rust
fn main() {
    let my_data = vec![1, 2, 3, 4, 5, 6];
    let it = my_data.iter(); // 'it' for 'iterator'
    let p1 = plus1(it);
    let x2 = times2(p1);
    print_data(x2);
}

fn plus1(it: impl Iterator<Iter = i32>) -> impl Iterator<Iter = i32> {
    it.map(|i| i + 1)
}

fn times2(it: impl Iterator<Iter = i32>) -> impl Iterator<Iter = i32> {
    it.map(|i| i * 2)
}

fn print_data(it: impl Iterator<Iter = i32>) {
    for i in it {
        println!("{}", i);
    }
}
```

This fails with:

```
4 |     let p1 = plus1(it);
  |              ^^^^^ expected `i32`, found reference
...
9 | fn plus1<'a>(it: impl Iterator<Item = i32>) -> impl Iterator<Item = i32> {
  |                                ---------- required by this bound in `plus1`
  |
  = note:   expected type `i32`
          found reference `&{integer}`
```

This is because the iterator, `it`, doesn't own the data to which it's referring, so instead of `T`, each element is `&T`. There are two different ways to work around this (as far as I know).

## Dereference the borrowed &T
If you identify the type returned by our `Vec`'s `.iter()` method, you'll see that it's a [`std::slice::Iter<i32>`](https://doc.rust-lang.org/std/slice/struct.Iter.html). Subsequent calls on the iterator – such as `.map` or `.filter` – always result in an `impl Iterator<Item = T>` with `T` changing depending on the operation:

```rust
let it = my_data.iter(); // it : std::slice::Iter<i32>
let it = it.map(|i| i);  // it : impl Iterator<Item = &i32>; i is &i32
let it = it.filter(|i| **i > 2); // it unchanged; i : &&i32
let it = it.map(|i| *i * 10); // it : impl Iterator<Item = i32>
```

This means we can dereference each element, changing `it` from an `Iter<i32>` to an `impl Iterator<Item = i32>`:

```rust
fn main() {
    let my_data = vec![1, 2, 3, 4, 5, 6];
    let it = my_data.iter();
    let it = it.map(|i| *i); // <-- Deref &i

    let p1 = plus1(it);
    let x2 = times2(p1);
    print_data(x2);
}
```

But what is this _doing_? Were we to use a different type here instead of `i32` – for example, `struct MyNum(i32)` – we'd get a new error:

```rust
#[derive(Debug)]
struct MyNum(i32);

fn main() {
    let my_data = vec![MyNum(1), MyNum(2), MyNum(3), MyNum(4), MyNum(5), MyNum(6)];
    let it = my_data.iter();
    let it = it.map(|i| *i);
    //                  ^^ move occurs because `*i` has type `MyNum`, which does not implement the `Copy` trait
}
```

The deref is just copying our data. Maybe that's fine – it's still only copied lazily – but maybe we want to avoid this unnecessary copy depending on what other iterations we're doing.

## Use std::slice::Iter<T>
Instead of trying to change `it` from a `slice::Iter` to an `impl Iterator`, we can change the signature of the first function, `plus1`, to accept a `slice::Iter`:

```rust
fn plus1(it: std::slice::Iter<i32>) -> impl Iterator<Item = i32> {
    it.map(|i| i + 1)
}
```

This immediately leads to the next compiler error:

```
9  | fn plus1(it: std::slice::Iter<i32>) -> impl Iterator<Item = i32> {
   |              --------------------- this data with an anonymous lifetime `'_`...
10 |     it.map(|i| i + 1)
   |        ^^^ ...is captured here...
   |
note: ...and is required to live as long as `'static` here
  --> src/main.rs:9:40
   |
9  | fn plus1(it: std::slice::Iter<i32>) -> impl Iterator<Item = i32> {
   |                                        ^^^^^^^^^^^^^^^^^^^^^^^^^
help: to declare that the `impl Trait` captures data from argument `it`, you can add an explicit `'_` lifetime bound
   |
9  | fn plus1(it: std::slice::Iter<i32>) -> impl Iterator<Item = i32> + '_ {
   |                                                                  ^^^^
```

Here, rustc is being extremely helpful in telling us what to do, so we simply append the [anonymous lifetime](https://doc.rust-lang.org/nightly/edition-guide/rust-2018/ownership-and-lifetimes/the-anonymous-lifetime.html):

```rust
fn plus1(it: std::slice::Iter<i32>) -> impl Iterator<Item = i32> + '_ {
    it.map(|i| i + 1)
}
```

This version works just fine. The trade-off here is that our first function accepts a different type than other functions do, but we avoid a copy. Of course, `plus1` and `times2` themselves are copying data.

## Box and .into\_iter()

An alternate approach is to allow our iterators to take ownership of the input data. This requires boxing the iterator, which is more syntactically verbose: instead of `impl Trait`, we now use [`Box<dyn Trait>`](https://doc.rust-lang.org/edition-guide/rust-2018/trait-system/dyn-trait-for-trait-objects.html) and have to call `Box::new()` with values here and there.

More importantly, this approach consumes `my_data`, so it can't be used afterward.

```rust
fn main() {
    let my_data = vec![1, 2, 3, 4, 5, 6];
    let it = my_data.into_iter(); // <-- .iter becomes .into_iter
    let boxed = Box::new(it); // <-- Put our iterator on the heap

    let p1 = plus1(boxed);
    let x2 = times2(p1);
    print_data(x2);
    // println!("{:?}", my_data); // This would fail with...
    //                  ^^^^^^^ value borrowed here after move
}

// 'impl Iterator<...>' becomes 'Box<dyn Iterator<...>>'
fn plus1(it: Box<dyn Iterator<Item = i32>>) -> Box<dyn Iterator<Item = i32>> {
    let it = it.map(|i| i + 1);
    Box::new(it)
}

fn times2(it: Box<dyn Iterator<Item = i32>>) -> Box<dyn Iterator<Item = i32>> {
    let it = it.map(|i| i * 2);
    Box::new(it)
}

fn print_data(it: Box<dyn Iterator<Item = i32>>) {
    for i in it {
        println!("{}", i);
    }
}
```

## No multiple enumeration
In both Rust examples – with owned or borrowed data – we aren't allowed to enumerate the data twice. In C#, you can do so:

```csharp
public static void Main()
{
    int[] myData = new int[] { 1, 2, 3, 4, 5, 6 };
    var p1 = plus1(myData);
    printData(p1);
    printData(p1); // no problem
}
```

But Rust won't compile the second invocation:

```rust
fn main() {
    let my_data = vec![1, 2, 3, 4, 5, 6];
    let it = my_data.iter();
    let it = it.map(|i| *i);

    let p1 = plus1(it);
    //  -- move occurs because `p1` has type `impl Iterator`, which does not implement the `Copy` trait
    print_data(p1);
    //         -- value moved here
    print_data(p1);
    //         ^^ value used here after move
}
```

\*The linked blog post is dated 2012, though I certainly read it a few years before that. Where the _original_ post is, I don't know.
