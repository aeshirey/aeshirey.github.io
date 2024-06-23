---
layout: post
title:  "Passwordless ssh"
date:   2024-06-23 09:11:37 -0700
category: code
tags: []
---

I kept having to re-learn how to do passwordless authentication with ssh in Linux, so here's the cheat sheet. For the purposes of discussion, _client_ is the machine from which you are connecting, and _server_ is the host machine to which you will connect. That is to say:

```
adam@client:~$ ssh server
adam@server's password:
```

On _client_, generate a key:

```
adam@client:~$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/adam/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/adam/.ssh/id_rsa
Your public key has been saved in /home/adam/.ssh/id_rsa.pub
The key fingerprint is:
SHA256:(...) adam@client
The key's randomart image is:
(...)
```

The public key, found in `~/.ssh/id_rsa.pub`, will now contain a line that looks like this:

```
ssh-rsa Xy5+In4uXy5+In4uXy5+In4uXy5+In4uX18ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll9fLn4ifi5fLn4ifi5fLn4ifi5fLn4ifi5fCl8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll9fLn4ifi5fLn4ifi5fLn4ifi5fLn4ifi5fICBOb3RoaW5nIHRvIHNlZSBoZXJlICBfLn4ifi5fLn4ifi5fLn4ifi5fLn4ifi5fXy5+In4uXy5+In4uXy5+In4uXy5+In4uXwpfLn4ifi5fLn4ifi5fLn4ifi5fLn4ifi5fXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uXy5+In4uX18ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8ufiJ+Ll8K adam@client
```

Copy this line and connect (with your password) to _server_. If it doesn't already exist, create `~/.ssh/authorized_keys`. Append the above line to that file. You should now be able to connect from _client_ to _server_ without a password.

Note: If you want to connect in the other direction, you will need to perform the same steps: generate a key with `ssh-keygen` on _server_ and its id\_rsa.pub line to _client_.
