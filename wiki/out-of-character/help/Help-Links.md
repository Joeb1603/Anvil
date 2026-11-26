---
title: Help:Links
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Links
class: out-of-character
topic: help
categories:
- Help
last_edited: '2012-02-15T09:31:00Z'
revision: 47
---

# Help:Links

There are five types of links in MediaWiki:

1. **[Internal links](#internal-links)** to other pages in the wiki
2. **[External links](#external-links)** to other websites
3. **[External links to internal pages](#external-links-to-internal-pages)** in the wiki
4. **[Interwiki links](#interwiki-links)** to other websites registered to the wiki in advance
5. **[Interlanguage links](#interlanguage-links)** to other websites registered as other language versions of the wiki

## Internal links

To add an internal link, enclose the name of the page you want to link to in double square brackets. When you save the page, you'll see the new link pointing to your page. If the page exists already it is displayed in blue, if it does not, in red.
Selflinks to the current page are not transformed in URLs but displayed in bold.
(If you really want to link to the current page, use an anchor (see below), or [[#top|current page]] which always links to the top.)

The first letter of the target page is automatically capitalized, unless otherwise set by the admins, and spaces are represented as underscores (typing an underscore in the link will have a similar effect as typing a space, but is not recommended, since the underscore will also be shown in the text).

| Description | You type | You get |
| --- | --- | --- |
| Internal link | ``` [[Main Page]] ``` | [Main Page](../site/Main_Page.md) |
| Piped link | ``` [[Main Page|different text]] ```  See also [Meta:Help:Piped link](http://www.mediawiki.org/wiki/Meta:Help:Piped_link) | [different text](../site/Main_Page.md) |
| Hide namespace shortcut | ``` [[Help:Contents|]] ```  Short for [[Help:Contents|Contents]] | Contents |
| Word-ending links | ``` [[Help]]s  [[Help]]ing  [[Help]]ers  [[Help]]anylettersyoulikehere ``` | Helps <br> Helping <br> Helpers <br> Helpanylettersyoulikehere |
| Avoiding word-ending links | ``` [[Help]]<nowiki />ful advice  [[wikipedia:GNU General Public License|GPL]]<nowiki />v3 ``` | Helpful advice <br> [GPL](http://en.wikipedia.org/wiki/GNU_General_Public_License)v3 |
| Redirect | ``` #REDIRECT [[Main Page]] ```  See also Help:Redirects | → [Main Page](../site/Main_Page.md) |
| Internal link to an anchor | ``` [[#See also]] ```  [Section headings](Help-Formatting.md) and the [top](#top) of the page are automatically anchored. | [#See also](#see-also) |
| Internal link to an anchor from different text | ``` [[#See also|different text]] ``` | [different text](#see-also) |
| Setting an internal link anchor | ``` <div id="NameOfAnchorHere">optional text</div> ```  Omit the "optional text" for invisible anchor. | optional text |
| Internal link to an anchor at another page | ``` [[Help:Images#See also]] ``` | [Help:Images#See also](Help-Images.md#see-also) |
| Internal link to the current page's talk page | ``` [[{{TALKPAGENAME}}|Discussion]] ```  See also Help:Magic\_words#Page\_names | Discussion |
| Internal link to a subpage | ``` [[/example]] ```  Shortcut for [[Help:Links/example]]. See also Help:Subpages. | /example |
| Internal link to a subpage without the leading slash | ``` [[/example/]] ```  Shortcut for [[Help:Links/example|example]]. | example |
| Internal link to a category page | ``` [[:Category:Help]] ```  See also [Help:Categories](Help-Categories.md) | [Category:Help](../../indexes/by-category/Help.md) |
| Internal link to an image or a file of other types | ``` [[media:example.jpg]]  [[media:example.pdf]] ```  See also [Help:Images](Help-Images.md) | [media:example.jpg](https://www.profounddecisions.co.uk/mediawiki-public/images/a/a9/Example.jpg) media:example.pdf |
| Internal link to the user's user page | ``` [[Special:MyPage]] ``` | [Special:MyPage](https://www.profounddecisions.co.uk/empire-wiki/Special:MyPage) |

## External links

To add an external link, enclose the name of the page you want to link to in single square brackets. When you save the page, you'll see the new link pointing to your page, with an arrow icon after it to show that it was coded with single bracket external link syntax, and thus may lead to another site.

| Description | You type | You get |
| --- | --- | --- |
| External link | http://mediawiki.org | <http://mediawiki.org> |
| External link with different label | [http://mediawiki.org MediaWiki] | [MediaWiki](http://mediawiki.org) |
| Numbered external link | [http://mediawiki.org] | [[1]](http://mediawiki.org) |
| External links with file icons | [http://en.wikipedia.org/wiki/.avi video] [http://en.wikipedia.org/wiki/.ogg sound] [http://en.wikipedia.org/wiki/.pdf document] See [#External link icons](#external-link-icons) for currently supported icons and extensions. | [video](http://en.wikipedia.org/wiki/.avi) <br> [sound](http://en.wikipedia.org/wiki/.ogg) <br> [document](http://en.wikipedia.org/wiki/.pdf) |
| External link to the same host | http://{{SERVERNAME}}/pagename | <http://www.profounddecisions.co.uk/pagename> |
| External link to other host passing the pagename | http://google.com/search?q={{PAGENAMEE}} <br> See also: URL encoded page names | <http://google.com/search?q=Links> |
| Mailto link | [mailto:info@example.org email me] | [email me](mailto:info@example.org) |
| Mailto named with subject line and body | [mailto:info@example.org?Subject=URL%20Encoded%20Subject&body=Body%20Text info] | [info](mailto:info@example.org?Subject=URL%20Encoded%20Subject&body=Body%20Text) |

### External links to internal pages

To add a link to a page on the same wiki using URL query parameters, you may need to use external link syntax.

| Description | You type | You get |
| --- | --- | --- |
| External link to the current page's edit page | ``` [http://www.mediawiki.org/w/index.php?title=Help:Links&action=edit Edit] ``` | [Edit](http://www.mediawiki.org/w/index.php?title=Help:Links&action=edit) |
| External link to the current page's edit page using the fullurl parser function | ``` [{{fullurl:{{PAGENAME}}|action=edit}} Edit] ```  See also Help:Magic\_words#URL\_data and [#External links](#external-links) | [Edit](https://www.profounddecisions.co.uk/mediawiki-public/index.php?title=Links&action=edit) |
| External link to the current page's edit page, and styled to look like an internal link | ``` <span class="plainlinks">[http://www.mediawiki.org/w/index.php?title=Help:Links&action=edit Edit]</span> ```  The plainlinks class can be used in cases where you want an external link to look like an internal one, by suppressing the icon that normally appears after it. | [Edit](http://www.mediawiki.org/w/index.php?title=Help:Links&action=edit) |

### External link icons

| Test link | Icon | Trigger |
| --- | --- | --- |
| [[2]](http://.) | [external-link-ltr-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/external-link-ltr-icon.png) | `.external`, `http://`, `gopher://` |
| [[3]](https://.) | [lock-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/lock-icon.png) | `https://` |
| [[4]](mailto:.) | [mail-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/mail-icon.png) | `mailto:` |
| [[5]](news://.) | [news-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/news-icon.png) | `news://` |
| [[6]](ftp://.) | [file-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/file-icon.png) | `ftp://` |
| [[7]](irc://.) | [talk-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/talk-icon.png) | `irc://` |
| [[8]](http://.ogg) | [audio-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/audio-icon.png) | `.ogg`, `.mid`, `.midi`, `.mp3`, `.wav`, `.wma` |
| [[9]](http://.ogm) | [video-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/video-icon.png) | `.ogm`, `.avi`, `.mpeg`, `.mpg` |
| [[10]](http://.pdf) | [document-icon.png](http://bits.wikimedia.org/skins-1.17/vector/images/document-icon.png) | `.pdf`, `.pdf#`, `.pdf?` |

### How to avoid auto-links

When you put a URL on a wiki page it will be automatically converted into an external link, like this:

<http://mediawiki.org>

To avoid that effect, put the URL between `<nowiki>` tags, like this:

```
<nowiki>http://mediawiki.org</nowiki>
```

To get this:

http://mediawiki.org

## Interwiki links

Interwiki links are links with the internal link markup to a website registered in advance. For example, you can link to the Sunflower article on <http://en.wikipedia.org> by typing `[[wikipedia:Sunflower]]`, which will result in a link [wikipedia:Sunflower](http://en.wikipedia.org/wiki/Sunflower). This is because `http://en.wikipedia.org/wiki/` is registered to your wiki by default with the prefix of `wikipedia`. *This link may not work properly, if the admin of your wiki has changed the setting.* Unlike internal links, interwiki links do not use page existence detection, so an interwiki link will appear blue even if the page does not exist on the remote wiki.

Similar to internal page links, you can create piped links, with alternate link label, e.g. `[[wikipedia:Sunflower|big yellow flower]]`, this is the link [big yellow flower](http://en.wikipedia.org/wiki/Sunflower).

Basically this is an abbreviation for longer URLs. A very similar link could be created as a normal external link by typing `[http://en.wikipedia.org/wiki/Sunflower big yellow flower]`, but interwiki links allow you to type out an easy and compact link, almost as if you are linking to a page on your own wiki.

More details are at [Manual:Interwiki](http://www.mediawiki.org/wiki/Manual:Interwiki). To edit the [interwiki table](http://www.mediawiki.org/wiki/Manual:Interwiki_table) on your site, see the [InterWiki extension](http://www.mediawiki.org/wiki/Extension:InterWiki).

### Interlanguage links

If your wiki has other language versions, you may find “interlanguage links” in the sidebar, just below toolbox in the box named “in other languages.”

Interlanguage links behave similarly to interwiki links, except that they are listed in the sidebar. To create an interlanguage link from a page, just type `[[language prefix:pagename]]` wherever you like in the page; the language prefix is the prefix specified at your wiki for the other language version (typically the [ISO language code](http://en.wikipedia.org/wiki/ISO_639)).

If you want to make the interlanguage link appear in the content of the page, you can add a colon before the language prefix:

:   `[[:en:Sunflower]]` → **en:Sunflower**

When link is both interwiki and interlanguage, the order is **[wikipedia:en:Sunflower](http://en.wikipedia.org/wiki/en:Sunflower)**.

## See also

- Linked images
- meta:Help:Links

---

Categories: [Help](../../indexes/by-category/Help.md)
