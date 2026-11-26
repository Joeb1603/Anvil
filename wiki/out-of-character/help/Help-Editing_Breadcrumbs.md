---
title: Help:Editing Breadcrumbs
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Editing_Breadcrumbs
class: out-of-character
topic: help
categories:
- Help
last_edited: '2012-03-01T18:26:05Z'
revision: 111
---

# Help:Editing Breadcrumbs

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

---

Categories: [Help](../../indexes/by-category/Help.md)
