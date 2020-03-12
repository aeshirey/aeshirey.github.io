---
layout: default
title: Tags
---

{% comment %}
See https://codinfox.github.io/dev/2015/03/06/use-tags-and-categories-in-your-jekyll-based-github-pages/ for more info.

Extract and sort all the tags from posts
{% endcomment %}

{% assign tags = "" %}
{% for post in site.posts %}
	{% assign ttags = post.tags | join:'|' | append:'|' %}
	{% assign tags = tags | append:ttags %}
{% endfor %}
{% assign tags = tags | split:'|' | uniq | sort %}

Tags: {% for tag in tags %}{% if tag != tags.first %} \| {% endif %}
<a href='#{{ tag | slugify }}'>`{{ tag }}`</a>
{% endfor %}

<hr/>


{% for tag in tags %}
## {{ tag }}
<a name='{{ tag | slugify }} /'>
{% for post in site.posts %}
{% for post_tag in post.tags %}
{% if post_tag == tag %} 
<a href='{{ post.url }}'>{{ post.title }}</a>
{% break %}
{% endif %} 
{% endfor %}
{% endfor %}
{% endfor %}
