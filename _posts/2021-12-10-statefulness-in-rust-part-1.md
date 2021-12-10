---
layout: post
title:  "Statefulness in Rust, part 1"
date:   2021-12-10 06:15:57 -0700
category: code
tags: [rust]
---

I've been reading [Jon Gjengset](https://twitter.com/jonhoo)'s [_Rust for Rustaceans_](https://nostarch.com/rust-rustaceans) and recently hit the section on marker types. It helped me understand a little bit better something that I'm working on in another project. This post is to help me organize my thoughts on state transitions with and without marker types and to go over nuances before I go into deeper detail on marker types.

## A Simple State Transition
Let's start with a very simple state transition: stoplights. A stoplight has exactly three states and a simple, circular state diagram: `green -> yellow -> red -> green -> ...`, which we can represent as:

```rust
#[derive(Debug, PartialEq)]
enum Stoplight {
    Red,
    Yellow,
    Green,
}

impl Stoplight {
    pub fn next(&self) -> Stoplight {
        match *self {
            Stoplight::Green => Stoplight::Yellow,
            Stoplight::Yellow => Stoplight::Red,
            Stoplight::Red => Stoplight::Green,
        }
    }
}

fn test_stoplight() {
    let mut stoplight = Stoplight::Green;
    stoplight = stoplight.next(); // yellow
    stoplight = stoplight.next(); // red
    stoplight = stoplight.next(); // green
    assert_eq!(stoplight, Stoplight::Green);
}
```

Easy peasy. But we're not storing any data or doing anything particularly interesting yet.

## Shopping Cart
A better example might be a shopping cart. We might also have three states to a cart: `Empty`, `InProgress`, and `Completed`. (We could have more, such as `Shipped` and `Delivered`, but I'm keeping three for simplicity.) Again, we could represent this as an enum but this time with data as appropriate:

```rust
use std::time::Instant;

#[derive(Debug)]
pub enum ShoppingCart {
    Empty,
    InProgress {
        started: Instant,
        products: Vec<String>,
    },
    Completed {
        started: Instant,
        completed: Instant,
        products: Vec<String>,
        total: f32,
    },
}

impl ShoppingCart {
    // TODO
}
```

This gives us three possible states. An empty cart has no data. It doesn't "start" until a product is added, at which point we'll know the start time and have a non-empty list of `products`. (For simplicity, I'm using `Instant` instead of something like [`chrono::DateTime`](https://docs.rs/chrono/latest/chrono/struct.DateTime.html).) A completd cart has the start time and list of products but also a completed time and the calculated total cost.

What functionality does this need in the `impl`? Well, we need to create a new cart:


```rust
pub fn new() -> ShoppingCart {
    ShoppingCart::Empty
}
```

And we need to be able to add a product. An `Empty` cart needs to change into an `InProgress` with the one item; an `InProgress` needs to just add the item:

```rust
pub fn add(&mut self, product: String) {
    match self {
        ShoppingCart::Empty => {
            *self = ShoppingCart::InProgress {
                started: Instant::now(),
                products: vec![product],
            };
        }
        ShoppingCart::InProgress { products, .. } => {
            products.push(product);
        }
        ShoppingCart::Completed { .. } => panic!("Cannot add to a completed cart"),
    }
}
```

Here's where we see problems arise: if a cart has been completed, what should happen when `.add()` is called? In this code, we panic. Alternately, we could return a `Result` to propagate errors. But let's continue the `checkout` function, which applies to non-empty carts:

```rust
pub fn checkout(self) -> Self {
    match self {
        ShoppingCart::Empty => panic!("Can't checkout an empty cart"),
        ShoppingCart::InProgress { started, products } => {
            let total = products
                .iter()
                .map(|p| match &p[..] {
                    "Apple" => 1.10,
                    "Orange" => 0.75,
                    _ => todo!("Handle other products here"),
                })
                .sum();

            ShoppingCart::Completed {
                started,
                completed: Instant::now(),
                products,
                total,
            }
        }
        ShoppingCart::Completed { .. } => panic!("Can't checkout a completed cart"),
    }
}
```

Again, more errors. But we can now test this and everything works:

```rust
pub fn test_cart_enum() {
    let mut cart = ShoppingCart::new();
    cart.add("Apple".to_string());
    cart.add("Orange".to_string());
    let cart = cart.checkout();
    println!("{:?}", cart);
}
```

An aside: `.add()` takes `&mut self` and will simply modify the existing value (or, in the case of an empty cart, will replace `self` with an updated discriminant) while `.checkout()` consumes `self` and returns a new value. The reason for this difference is that `.checkout()` consuming and returning can use move semantics to maintain the existing list of values. In order to remain `&mut self`, it would have to either clone the product list or do some wonky `mem::replace` to guarantee that `self` is always valid. Probably not a great API design.

The above code isn't great from a safety/correctness perspective. We _can_ gracefully handle runtime errors with `Result`, but wouldn't it be better to make it impossible to hit them?

## Marker Types
Ideally, an empty cart shouldn't ever be able to call `.checkout()`. That is, we'd like to do something like this:

```rust
let cart = ShoppingCart::new();
let done = cart.checkout(); // this *should* fail to compile
```

Let's start with the states we need but instead of specifying them as an enum, they are unit structs. We'll also define the shopping cart that can be of some type `T` and will contain all the data we need:

```rust
struct Empty;
struct InProgress;
struct Complete;

struct ShoppingCart<T> {
    started: Instant,
    completed: Instant,
    products: Vec<String>,
    total: f32,
    phantom: PhantomData<T>,
}
```

_hic svnt dracones_: this may not be best practice, but it works.

What does this mean? We will use the three unit structs to represent the type of `ShoppingCart`; that is, a `ShoppingCart<Empty>` is a different type than `ShoppingCart<InProgress>`, _and they can have independent implementations_.

But what's this [`PhantomData<T>`](https://doc.rust-lang.org/std/marker/struct.PhantomData.html)? It appeases the compiler because we're not actually storing a `T`; `PhantomData` makes our `ShoppingCart<T>` _act like_ it contains a `T`. We _could_ have instead used, say, `_state: T` if we wanted to.

### The Implementations
Interestingly, we can have different `impl` blocks for the different states:

```rust
impl ShoppingCart<Empty> {
    fn new() -> Self {
        ShoppingCart {
            started: Instant::now(),
            completed: Instant::now(),
            products: Vec::new(),
            total: 0.0,
            phantom: PhantomData,
        }
    }
}

fn test_cart_marker() {
    let cart = ShoppingCart::new(); // of type ShoppingCart<Empty>
}
```

Currently, there exists exactly one implementation of `ShoppingCart` for which a `new` function exists, so Rust knows that it must be a `ShoppingCart<Empty>`.

Even though the cart has neither been started (per our definition above) nor completed, these fields shouldn't exist. We could make the fields optional and set them to `None`. But we also know the current state is `Empty` and we can thus set but ignore the value. Again, this may not be best practice.

To add a product to a cart, we provide an `.add()` function to both the empty cart:

```rust
impl ShoppingCart<Empty> {
    fn add(self, product: String) -> ShoppingCart<InProgress> {
        ShoppingCart {
            // The only fields we really care about:
            started: Instant::now(),
            products: vec![product],

            // Everything else has a valid value that we'll just ignore
            completed: self.completed,
            total: self.total,
            phantom: PhantomData,
        }
    }
}
```

And the separate implementation of `ShoppingCart<InProgress>`:

```rust
impl ShoppingCart<InProgress> {
    fn add(mut self, product: String) -> ShoppingCart<InProgress> {
        self.products.push(product);
        self
    }
}
```

The distinction here is that the empty cart needs to create an in-progress cart while an in-progress cart can keep its state and simply add a product to its already existing list. Now, our test code can be:


```rust
fn test_cart_marker() {
    let cart = ShoppingCart::new(); // of type ShoppingCart<Empty>
    let cart = cart.add("Apple".to_string()); // of type ShoppingCart<InProgress>
    let cart = cart.add("Orange".to_string()); // of type ShoppingCart<InProgress>
}
```

By virtue of calling `cart.add()` on an _empty_ cart, we are returned a differently typed value. That is, just as a `Vec<u32>` is an altogether different animal than a `Vec<bool>`, so too is `ShoppingCart<Empty>` different than `ShoppingCart<InProgress>`. So it is with an in-progress cart being completed:

```rust
impl ShoppingCart<InProgress> {
    fn complete(self) -> ShoppingCart<Complete> {
        let total = self
            .products
            .iter()
            .map(|p| match &p[..] {
                "Apple" => 1.10,
                "Orange" => 0.75,
                _ => panic!("Unknown product"),
            })
            .sum();

        ShoppingCart {
            started: self.started,
            completed: Instant::now(),
            total,
            products: self.products,
            phantom: PhantomData,
        }
    }
}
```

For now, there's no implementation of the completed cart. Specifically, we don't create an `.add()` function on it, which means:

```rust
fn test_cart_marker() {
    let cart = ShoppingCart::new(); // of type ShoppingCart<Empty>
    let cart = cart.add("Apple".to_string()); // of type ShoppingCart<InProgress>
    let cart = cart.add("Orange".to_string()); // of type ShoppingCart<InProgress>
    let cart = cart.complete();
    assert_eq!(cart.total, 1.85);
    //cart.add("Banana".to_string()); // no method named `add` found for struct `ShoppingCart<Complete>` in the current scope
}
```
## Misc
Because the type is changing on the first call to `.add()` and on the call to `.complete()`, we have to [shadow the variables](https://doc.rust-lang.org/stable/rust-by-example/variable_bindings/scope.html) -- we can't make cart mut and overwrite it:

```rust
fn test_cart_marker() {
    let mut cart = ShoppingCart::new(); // of type ShoppingCart<Empty>
    //cart = cart.add("Apple".to_string()); // mismatched types
                                            // expected struct `ShoppingCart<Empty>`
                                            //    found struct `ShoppingCart<InProgress>
}
```

My next post will include more on converting between the generic types.