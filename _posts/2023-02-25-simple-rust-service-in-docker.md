---
layout: post
title:  "Simple Rust service in Docker"
date:   2023-02-25 16:07:00 -0700
category: code
tags: [rust, docker]
---

At work, I own a Rust service that runs in an Azure Function. Among other things, the Functions runtime handles restarting the service should it be needed; fortunately, the service is incredibly stable and reliable. That said, I have done almost nothing with Docker (since I guess I'm living in the mid 2010s), and I really should learn more about it, as I expect I may need to deploy Rust services through Docker at some point.

I started looking at some simple Docker examples, but they all seem to use Node as a starting point. I don't want to start there and try to work my way back, so instead, I figured I'd start with a simple Rust service and see if I can start from scratch.

As a total Docker newbie, here's a fairly brief summary of my misadventures.

## Build a Simple Server
Let's start with the service itself. Wanting to keep this incredibly simple (in this case, avoiding Rust async), I found [OxHTTP](https://github.com/oxigraph/oxhttp), a very simple synchronous HTTP server. We'll start with a new project that uses it:

```shell
$ cargo new rust-server
$ cd rust-server
$ cargo add oxhttp
```

The [provided example](https://github.com/oxigraph/oxhttp#server) is just about perfect for what we want; I'll just _slightly_ tweak it by wrapping it in a `main` function:

```rust
fn main() {
    use oxhttp::Server;
    use oxhttp::model::{Response, Status};
    use std::time::Duration;
    
    // Builds a new server that returns a 404 everywhere except for "/" where it returns the body 'home'
    let mut server = Server::new(|request| {
        if request.url().path() == "/" {
            Response::builder(Status::OK).with_body("home")
        } else {
            Response::builder(Status::NOT_FOUND).build()
        }
    });
    // Raise a timeout error if the client does not respond after 10s.
    server.set_global_timeout(Duration::from_secs(10));
    // Listen to localhost:8080
    server.listen(("localhost", 8080)).unwrap();
}
```

Build this with `cargo build --release` and test it out. I've configured my `~/.cargo/config` to specify a common build directory:

```
[build]
target-dir = "/home/adam/cargo-target"
```

This means that I can run my built server with `~/cargo-target/release/rust-server`, and when I visit `http://localhost:8080` in my browser, I see the HTTP response "home". The server now works, so I copied the binary into the current working directory.

## Simple Docker image
Next, we'll need to build a Dockerfile. As I said, I know just about nothing about Docker, but I want to avoid the Node route. It seems pretty much everything is built off of [Alpine](https://www.alpinelinux.org/), so I'll start there:

```dockerfile
FROM alpine:latest
COPY rust-server rust-server
CMD ["rust-server"]
```

Building this is quick and completes without issue:

```shell
$ docker build -t my-rust-server:latest .
[+] Building 0.6s (7/7) FINISHED
 => [internal] load build definition from Dockerfile                                                                                 0.1s
 => => transferring dockerfile: 113B                                                                                                 0.0s
 => [internal] load .dockerignore                                                                                                    0.0s
 => => transferring context: 2B                                                                                                      0.0s
 => [internal] load metadata for docker.io/library/alpine:latest                                                                     0.0s
 => [internal] load build context                                                                                                    0.1s
 => => transferring context: 4.70MB                                                                                                  0.1s
 => CACHED [1/2] FROM docker.io/library/alpine:latest                                                                                0.0s
 => [2/2] COPY rust-server rust-server                                                                                               0.2s
 => exporting to image                                                                                                               0.1s
 => => exporting layers                                                                                                              0.1s
 => => writing image sha256:108dbb6764b4e6c94cc3bde571eb2157dceb57aab1ac3f393577174c1175a282                                         0.0s
 => => naming to docker.io/library/my-rust-server:latest                                                                             0.0s
```

Then I run it:

```shell
$ docker run -t my-rust-server:latest
docker: Error response from daemon: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: "rust-server": executable file not found in $PATH: unknown.
ERRO[0001] error waiting for container: context canceled
```

It seems that `COPY foo foo` places `foo` into the root directory (ie, `/`), which isn't in `$PATH`, I guess? So let's try putting it into `/bin/`:

```dockerfile
FROM alpine:latest
COPY rust-server /bin/rust-server
CMD ["/bin/rust-server"]
```

```shell
$ docker run -t my-rust-server:latest
exec /bin/rust-server: no such file or directory
```

This is a different error, so _something_ changed. But it's still not finding it? Let's inspect the container:

```shell
$ docker run -it my-rust-server:latest /bin/sh
/ # ls /bin/rust-server
/bin/rust-server
/ # file /bin/rust-server
/bin/sh: file: not found
```

The binary is definitely there. I tried `file` to see what the system thinks the binary is, but Alpine doesn't have it. Instead, we can try `ldd` to get details:

```shell
/ # ldd /bin/rust-server
        /lib64/ld-linux-x86-64.so.2 (0x7fa7b4984000)
Error loading shared library libgcc_s.so.1: No such file or directory (needed by /bin/rust-server)
        librt.so.1 => /lib64/ld-linux-x86-64.so.2 (0x7fa7b4984000)
        libpthread.so.0 => /lib64/ld-linux-x86-64.so.2 (0x7fa7b4984000)
        libdl.so.2 => /lib64/ld-linux-x86-64.so.2 (0x7fa7b4984000)
        libc.so.6 => /lib64/ld-linux-x86-64.so.2 (0x7fa7b4984000)
Error loading shared library ld-linux-x86-64.so.2: No such file or directory (needed by /bin/rust-server)
Error relocating /bin/rust-server: _Unwind_Resume: symbol not found
Error relocating /bin/rust-server: _Unwind_Backtrace: symbol not found
```

Ohh, so it's not that my Docker image can't find _my binary_ but that when trying to run my binary, it can't find the _dynamically-linked libgcc_. A quick search on how to install packages in Alpine (since it's not Debian-based, I can't use `apt`) shows that it uses `apk`, and [`libgcc` exists in Alpine's package repository](https://pkgs.alpinelinux.org/packages?name=libgcc&branch=edge&repo=&arch=&maintainer=). Adding this to the Dockerfile:
    
```dockerfile
FROM alpine:latest
COPY rust-server /bin/rust-server

# These are new:
RUN apk update
RUN apk add libgcc

CMD ["/bin/rust-server"]
```

Running this still gives the `no such file or directory` error. So let's inspect with `ldd` again:

```shell
/ # ldd /bin/rust-server
        /lib64/ld-linux-x86-64.so.2 (0x7f1e6d596000)
        libgcc_s.so.1 => /usr/lib/libgcc_s.so.1 (0x7f1e6d2bc000)
        librt.so.1 => /lib64/ld-linux-x86-64.so.2 (0x7f1e6d596000)
        libpthread.so.0 => /lib64/ld-linux-x86-64.so.2 (0x7f1e6d596000)
        libdl.so.2 => /lib64/ld-linux-x86-64.so.2 (0x7f1e6d596000)
        libc.so.6 => /lib64/ld-linux-x86-64.so.2 (0x7f1e6d596000)
Error loading shared library ld-linux-x86-64.so.2: No such file or directory (needed by /bin/rust-server)
Error relocating /bin/rust-server: __res_init: symbol not found
Error relocating /bin/rust-server: gnu_get_libc_version: symbol not found
```

`libgcc` is no longer a problem, but `ld-linux` still is. And it appears that `ld-linux` is part of [`gcompat`](https://pkgs.alpinelinux.org/package/edge/community/x86_64/gcompat). After adding `RUN apk add gcompat`, rebuilding, and rerunning, the message "Error loading shared library ld-linux-x86-64.so.2" goes away, but the "__res_init" and "gnu_get_libc_version" errors remain.

I did some further sleuthing and found [a suggestion on Reddit](https://www.reddit.com/r/rust/comments/o8gxzn/understanding_why_a_rust_app_fails_within_an/) to use [this hack](https://github.com/TobiasDeBruijn/SkinFixer-API/blob/a24da0657f222101864cf5f500e81628b90eec18/Dockerfile) to make it work, but instead of continuing down this rabbit hole, I decided to try another approach I saw: [`musl`](https://en.wikipedia.org/wiki/Musl).

## Static linking with musl

Rust can compile to a number of [build targets](https://doc.rust-lang.org/rustc/targets/built-in.html); in my dev environment (Ubuntu in WSL2), the default is:

```shell
$ rustc -vV | grep host
host: x86_64-unknown-linux-gnu
```

We can find supported targets with `rustup target list`. Doing this shows that there's _x86_64-unknown-linux-musl_. Let's install this toolchain and compile the server:

```shell
$ rustup target add x86_64-unknown-linux-musl 
(...)
$ cargo build --target=x86_64-unknown-linux-musl --release
$ mv rust-server rust-server-old
$ cp ~/cargo-target/x86_64-unknown-linux-musl/release/rust-server .
```

We can compare the old binary to the new one:

```shell
$ file rust-server-old rust-server
rust-server-old: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=523b84a693e7b90bcf8332d2eecd51cc9bfbe45a, with debug_info, not stripped
rust-server:     ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, with debug_info, not stripped

$ ldd rust-server-old
        linux-vdso.so.1 (0x00007ffea2be5000)
        libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007fd1fa870000)
        librt.so.1 => /lib/x86_64-linux-gnu/librt.so.1 (0x00007fd1fa668000)
        libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007fd1fa449000)
        libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007fd1fa245000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fd1f9e54000)
        /lib64/ld-linux-x86-64.so.2 (0x00007fd1fad44000)

$ ldd rust-server
        statically linked
```

_(Side note: the old and new binaries are 4.5Mb and 4.9Mb, respectively, showing the cost of statically linking. However, if we `strip` both binaries, their sizes -- and the marginal difference -- drop: 751Kb and 865Kb, respectively.)_

## Running the `musl` binary

Since the new binary is statically linked, we don't need to install extra apk packages, so the Dockerfile is now back to:

```dockerfile
FROM alpine:latest
COPY rust-server /bin/rust-server
CMD ["/bin/rust-server"]
```

This builds very quickly, and calling `docker run` now has a service running. Going to [http://localhost:8080](http://localhost:8080) should work, right?

```shell
$ curl localhost:8080
curl: (7) Failed to connect to localhost port 8080: Connection refused
```

Ah, but we need to publish the container's port to the host:

```shell
$ docker run -p 8080:8080 -t my-rust-server:latest

# In another terminal (because `docker run` is blocking):
$ curl localhost:8080
curl: (52) Empty reply from server
```

So it's connecting but not getting any data?

```shell
$ telnet localhost 8080
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
Connection closed by foreign host.

$ telnet localhost 8081
Trying 127.0.0.1...
telnet: Unable to connect to remote host: Connection refused
```

The connection on 8080 is opened but immediately closed; the attempt on 8081 fails, as expected, because there's nothing on that port -- it's showing that there's something different about 8080. So Docker _is_ forwarding the port, and something _is_ listening. Surely that's our server.

Looking at the Rust code, we notice that we're listening on localhost, port8080:

```rust
server.listen(("localhost", 8080)).unwrap();
```

But wait: [it turns out](https://serverfault.com/a/876703) that there's a difference:

> 127.0.0.1:xxxx is the normal loopback address, and localhost:xxxx is the hostname for 127.0.0.1:xxxx.
>
> 0.0.0.0 is slightly different, it's an address used to refer to all IP addresses on the same machine. Or no specific IP address.

Simply changing from "localhost" to "0.0.0.0", recompiling, rebuilding the image, and rerunning does the trick

```shell
$ curl localhost:8080
home
```

## Bonus: Saving the image:

I am familiar (but have no experience) with Docker Hub, and I have only briefly played with [Azure Container Registry](https://azure.microsoft.com/en-us/products/container-registry/), I thought I'd first start with the simplest option: saving the image to a file:

```shell
$ docker save my-rust-server:latest | gzip > my-rust-server.tar.gz

$ ls -lh my-rust-server.tar.gz
-rw-r--r-- 1 adam adam 4.5M Feb 24 16:30 my-rust-server.tar.gz
```

Now let's remove the image from Docker, make sure we can re-load it, and run it again:


```shell
$ docker image rm my-rust-server:latest
Untagged: my-rust-server:latest
Deleted: sha256:0ed0fda582a3c568fdb8f4a313a464ce3244442d1f1d36934be9bb29e8b9e4fd

$ docker images | grep my-rust

$ docker load < my-rust-server.tar.gz
Loaded image: my-rust-server:latest

$ docker images | grep my-rust
my-rust-server   latest    732da9278f98   18 minutes ago   12.1MB

$ docker run -it my-rust-server:latest /bin/sh
/ # ls /bin/rust-server
/bin/rust-server
```
