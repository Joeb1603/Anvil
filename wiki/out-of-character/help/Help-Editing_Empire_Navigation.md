---
title: Help:Editing Empire Navigation
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Editing_Empire_Navigation
class: out-of-character
topic: help
categories:
- Help
last_edited: '2016-04-24T19:25:40Z'
revision: 43762
---

# Help:Editing Empire Navigation

## Breadcrumbs

Breadcrumbs are the hierarchical links at the top of the page (for example, for this page, it's Empire / Help / Editing Breadcrumbs).

This is a very manual thing for MediaWiki. You have to edit a set of rules in [Imperial:Breadcrumbs](../site/Imperial-Breadcrumbs.md).

There are lots of ways it can work, but I think the easiest is to make sure every page is in a category (see [Help:Categories](Help-Categories.md) for how to do that), and then use the category name to define the breadcrumbs.

For example, if the [Imperial:Breadcrumbs](../site/Imperial-Breadcrumbs.md) trail contains:

```
* Rules @ [[Main Page|Empire]] > [[Rules Overview|Rules]] >
* Help @ [[Main Page|Empire]] > [[Help]] >
```

then anything in the Rules category will have a breadcrumb trail of Empire (links to Main Page), Rules (links to the Rules category index) and so on.

If a page is in more than one category then it'll match the first one it finds.

## Putting A Page In A Category

To put a page in a category, just add a link like so:

```
[[Category:SomeCategory]]
```

preferably at the bottom of the page you want to put in the category. For example, this page has:

```
[[Category:Help]]
```

A page can be in multiple categories. The category link can be anywhere on the page (except in a

```
<pre>
```

tag or similar), but it is best practice to add category links to the bottom of the content.

## Categories as Templates

Some categories are set up to work like templates, for example in order to automatically pull in a navigation menu (see [Category:Herbs](../../indexes/by-category/Herbs.md)) or add related super-categories (see [Category:380YE Spring Equinox winds of fortune](../../indexes/by-category/380YE_Spring_Equinox_winds_of_fortune.md)). In that case, the template can be embedded as

```
{{Category:SomeCategory}}
```

## Editing The Top Menu

You need to edit the [Imperial:TitleBar](../site/Imperial-TitleBar.md) page. It's a fairly straightforward list using the syntax for bullet-lists in Wiki markup. You can have up to two levels of list - the top level entries are the visible links when the menu is closed, the sublists are the pop-up menus.

For example, this text:

```
* [[Home]]
* My Menu
** [[Page 1]]
** [[Page 2]]
```

gives you two menu entries, Home and My Menu. Home will be a link to the page called Home. My Menu will be a dropdown, containing two submenu items that link to Page 1 and Page 2.

If you want the menu item names to be different from the pages you're going to, no problem - just use the standard Wiki retitling feature. A pipe character (|) separates the page you want to go to from the title of the page that's displayed in the menu. For example:

```
* [[Home|Go Home]]
* My Menu
** [[Page 1|Go to Page 1]]
** [[Page 2|Go to Page 2]]
```

## Editing The Left Menu

You need to edit the [Imperial:LeftBar](../site/Imperial-LeftBar.md) page. The list format should be fairly obvious from what's in the file already. It's another type of list, consisting of section headers and wiki links. Again, you can retitle links using the pipe symbol as before.

```
<nav-list>
  <nav-header>A Header</nav-header>
  <nav-item>[[Page 1|Go to Page 1]]</nav-item>
  <nav-item>[[Page 2]]</nav-item>
  <nav-header>Another Header</nav-header>
  <nav-item>[[Kicking|How to kick people]]</nav-item>
  <nav-item>[[Punching|How to punch people]]</nav-item>
</nav-list>
```

## Editing The Footer

Edit the page [Imperial:Footer](../site/Imperial-Footer.md). It's a bit more complicated than the other two, because there's a set of three columns and then a footer line beneath. It should be obvious enough from the existing content.

---

Categories: [Help](../../indexes/by-category/Help.md)
