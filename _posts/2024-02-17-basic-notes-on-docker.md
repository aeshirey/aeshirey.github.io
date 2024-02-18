---
layout: post
title:  "Basic notes on Docker"
date:   2024-02-17 19:30:33 -0700
category: code
tags: [docker]
---

Some notes I took a while back on learning the basics of [Docker](https://www.docker.com/).

# Managing images
Lets use [minideb](https://hub.docker.com/r/bitnami/minideb), a small Debian-based linux:

```bash
$ docker pull bitnami/minideb
Using default tag: latest
latest: Pulling from bitnami/minideb
ba49d470d895: Pull complete
Digest: sha256:cbbc1db2617a7e5224f8dc692c990b723e4fe3ef69864544e7c14aa613c0ccb7
Status: Downloaded newer image for bitnami/minideb:latest
docker.io/bitnami/minideb:latest
```

We can see this new image is available locally with `docker images`:

```bash
$ docker images
REPOSITORY        TAG       IMAGE ID       CREATED      SIZE
bitnami/minideb   latest    c5eecd6244a8   3 days ago   120MB
```

And we can remove it with `docker image rm <id>`:

```bash
$ docker image rm c5eecd6244a8
Untagged: bitnami/minideb:latest
Untagged: bitnami/minideb@sha256:cbbc1db2617a7e5224f8dc692c990b723e4fe3ef69864544e7c14aa613c0ccb7
Deleted: sha256:c5eecd6244a829084e2f788e3f877a5ab8ac63f9c8dc55c3cfff4f1d172fc23c
Deleted: sha256:44b47439f86a658d61565e3a9e86c1c9608b2ee8adb4f6e85005634e6f537f43

$ docker images
REPOSITORY   TAG       IMAGE ID   CREATED   SIZE
```

# Running images in containers

We could run this image in a new container with `docker run c5eecd6244a8`, but it would almost immediately return to our console. With `docker container ls -a`, we'd see that this container ran and terminated:

```bash 
$ docker container ls -a
CONTAINER ID   IMAGE          COMMAND       CREATED          STATUS                      PORTS     NAMES
ff11c7f3afb8   c5eecd6244a8   "/bin/bash"   29 seconds ago   Exited (0) 28 seconds ago             clever_franklin

# Delete this terminated container
$ docker container rm ff11c7f3afb8
```

What we want is to run _interactively_, so we'll use `docker run -it <id>`:

```bash
# In the host:
$ docker run -it c5eecd6244a8

# In the container!
root@25bca2749327:/# uname -a
Linux 25bca2749327 5.15.0-1042-azure #49~20.04.1-Ubuntu SMP Wed Jul 12 12:44:56 UTC 2023 x86_64 GNU/Linux

root@25bca2749327:/# cat /etc/os-release | grep NAME
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_CODENAME=bookworm

root@25bca2749327:/# exit
```

At this point, we're back in our host. There's still a terminated container:

```bash
$ docker container ls -a
CONTAINER ID   IMAGE          COMMAND       CREATED         STATUS                      PORTS     NAMES
25bca2749327   c5eecd6244a8   "/bin/bash"   2 minutes ago   Exited (0) 49 seconds ago             elegant_saha

$ docker container rm 25bca2749327
```

To avoid this, use `docker run --rm` (NB, it has to be before the container name!):

```bash
$ docker container ls -a
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ docker run -it --rm c5eecd6244a8
root@21735047c8bb:/# hostname
21735047c8bb

root@21735047c8bb:/# exit

$ docker container ls -a
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

# Creating a container
Let's make use of the minideb image as the basis for a derived image. We use a [Dockerfile](https://docs.docker.com/engine/reference/builder/) to describe the image we'll create:

```dockerfile
# The base image for our new image
FROM bitnami/minideb

# For a simple Rust service, see:
# https://aeshirey.github.io/code/2023/02/25/simple-rust-service-in-docker.html
# COPY <host-filename> <docker-filanem>
COPY rust-server my-rust-server

CMD ["./my-rust-server"]
```

To build this, we can use `docker build <path>`, where `<path>` is the directory in which the Dockerfile lives (eg, `.`). Additionally, we'll use the `-t <name>:<tag>` to give our image a name and tag. If the tag is omitted, _latest_ is used.

```bash
$ docker images
REPOSITORY        TAG       IMAGE ID       CREATED      SIZE
bitnami/minideb   latest    c5eecd6244a8   3 days ago   120MB

$ docker build . -t my-simple-container
 => [internal] load .dockerignore                                                                  0.0s
 => => transferring context: 2B                                                                    0.0s
 => [internal] load build definition from Dockerfile                                               0.0s
 => => transferring dockerfile: 141B                                                               0.0s
 => [internal] load metadata for docker.io/bitnami/minideb:latest                                  0.0s
 => [internal] load build context                                                                  0.0s
 => => transferring context: 84B                                                                   0.0s
 => [1/2] FROM docker.io/bitnami/minideb:latest                                                    0.0s
 => CACHED [2/2] COPY simple-server/simple-server my-simple-server                                 0.0s
 => exporting to image                                                                             0.0s
 => => exporting layers                                                                            0.0s
 => => writing image sha256:61a24712801a996b6ceefb378cd9ebccdb9caae8c58ea7acf17eaff0285666bb       0.0s
 => => naming to docker.io/library/my-simple-container                                             0.0s

$ docker images
REPOSITORY            TAG       IMAGE ID       CREATED              SIZE
my-simple-container   latest    61a24712801a   About a minut
bitnami/minideb       latest    c5eecd6244a8   3 days ago           120MB
```

Because our server exposes port 8080, we want our container to also expose it. Maybe we want to use the same port or maybe we want to remap it. Either way, we'll use `-p <host-port>:<container-port>`:

```bash
$ docker run --rm --init -p 8123:8080 fd83da080eab
```

Then we can connect in another shell on our host to communicate with this container:

```bash
$ curl 127.0.0.1:8123 -l -w "\n"
home
```


# Extras
## Need to 'log into' a container for an image you built to inspect it?
```bash
# Specify 'bash' as the process to run
$ docker run -p 8123:8080 --rm -it 61a24712801a bash
#                        image id ------^        ^-- command to run
```

## Can't CTRL-C from your `docker run`?

Oops, can't exit this container:
```bash
$ docker run --rm fd83da080eab
^C
```

From another shell:

```bash
$ docker ps
CONTAINER ID   IMAGE          COMMAND               CREATED              STATUS              PORTS     NAMES
260c882a217e   fd83da080eab   "/my-simple-server"   About a minute ago   Up About a minute             gracious_hawking
#    ^------ this is the container we'll want to kill because oopsie

$ docker kill 260c882a217e
260c882a217e
```

Avoid this by [including the `--init` flag next time you `docker run`](https://stackoverflow.com/a/60812082/1191181):

```bash
$ docker run --rm --init fd83da080eab
^C$
```

## How about accessing the host network?
If you use `docker run --network=host`, then the container will be able to access the host network. For example:

```bash
# In the host OS:
$ ./rust-server &

$ curl 127.0.0.1:8080 -w "\n"
home

$ docker run -it --rm --network=host c5eecd6244a8

# Now in the container
root@hostname:/# curl 127.0.0.1:8080 -w "\n"
home
# 
```

## Exporting/importing images

```bash
$ docker images
REPOSITORY            TAG       IMAGE ID       CREATED          SIZE
<none>                <none>    61a24712801a   30 minutes ago   131MB
my-simple-container   latest    fd83da080eab   30 minutes ago   131MB
bitnami/minideb       latest    c5eecd6244a8   3 days ago       120MB

$ docker save fd83da080eab | gzip > my-simple-container.tar.gz

$ file my-simple-container.tar.gz
my-simple-container.tar.gz: gzip compressed data, from Unix, original size modulo 2^32 135666688 gzip compressed data, reserved method, ASCII, extra field, encrypted, from FAT filesystem (MS-DOS, OS/2, NT), original size modulo 2^32 135666688

$ ls -lh my-simple-container.tar.gz
-rw-r--r-- 1 root root 41M Feb 17 04:48 my-simple-container.tar.gz

# Later/elsewhere, this can be loaded:
$ docker load < my-simple-container.tar.gz
Loaded image: my-simple-container:latest
```
