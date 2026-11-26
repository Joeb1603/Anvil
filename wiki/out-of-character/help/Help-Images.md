---
title: Help:Images
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Images
class: out-of-character
topic: help
categories:
- Help
last_edited: '2012-02-15T09:58:02Z'
revision: 57
---

# Help:Images

This page explains the **image** syntax when editing the wiki. You or another user must usually [upload an image](https://www.profounddecisions.co.uk/empire-wiki/Special:Upload) before you can use it on a page.

Images that are stored on a MediaWiki server are usually rendered by using the `File:` namespace prefix. The alternate `Media:` namespace prefix is also usable to reference the original media file content (for rendering or downloading it separately, out of any MediaWiki page).

## Supported types for images

The following file formats are supported by default:

- .jpg or .jpeg, .png, .gif

## Rendering a single image

### Syntax

The full syntax for displaying an image is:

```
[[File:filename.extension|options|caption]]
```

where *options* can be zero or more of the following, separated by pipes (**|**):

- *[Format](#format)* option: one of **border** and/or **frameless**, **frame**, **thumb** (or **thumbnail**);

  :   Controls how the rendered image is formatted and embedded in the rest of the page.
- *[Resizing](#size-and-frame)* option: one of
  - *{width}***px** — Resizes the image to fit within the given maximum width in pixels, without restricting its height;
  - **x***{height}***px** — Resizes the image to fit within the given maximum height in pixels, without restricting its width;
  - *{width}***x***{height}***px** — Resizes the image to fit within the given width and height in pixels;
  - **upright** — Resizes an image to fit within reasonable dimensions, according to user preferences (suitable for images whose height is larger than width).

  :   Note that the image will always retain its aspect ratio, and can only be reduced (not increased) in size unless it's in a scalable media type (bitmap images cannot be scaled up).
  :   The default maximum size depends on the *format* and the internal image dimensions (according to its media type).
- *[Horizontal alignment](#horizontal-alignment)* option: one of **left**, **right**, **center**, **none**;

  :   Controls the horizontal alignment (and inline/block or floating styles) of the image within a text (no default value).
- *[Vertical alignment](#vertical-alignment) option*: one of **baseline**, **sub**, **super**, **top**, **text-top**, **middle**, **bottom**, **text-bottom**;

  :   Controls the vertical alignment of a non-floating inline image with the text before or after the image, and in the same block (the default vertical alignment is **middle**).
- *[Link](#altering-the-default-link-target) option*: one of
  - **link=***{target}* — Allows to change the target (to an arbitrary page title, or URL) of the generated link, activable on the rendered image surface; e.g. `[[File:Example.jpg|20px|link=http://www.wikipedia.org]]` renders as [Image: Example.jpg](http://www.wikipedia.org) (external link), or `[[File:Example.jpg|20px|link=MediaWiki]]` renders as [Image: Example.jpg](https://www.profounddecisions.co.uk/empire-wiki/MediaWiki) (internal link).
  - **link=** (with an empty value) — ([MediaWiki 1.14+](http://www.mediawiki.org/wiki/rev:41727)) Displays an image without any activable link; e.g. `[[File:Example.jpg|20px|link=]]` renders as [Image: Example.jpg](https://www.profounddecisions.co.uk/mediawiki-public/images/thumb/a/a9/Example.jpg/20px-Example.jpg).

:   **!** Link does **not** work with thumb, thumbnail or frame.

- Other specific options:
  - **alt=***{alternative text}* — ([MediaWiki 1.14+](http://www.mediawiki.org/wiki/rev:41837)) Defines the alternative text (maps to the HTML attribute `alt="..."` of the generated `<image />` element) of an image that will be rendered if either the referenced image cannot be downloaded and embedded, or if the support media must use the alternative description text (e.g. when using a Braille reader or with accessibility options set by the user in its browser).
  - **page=***{number}* — Renders the specified page number (currently only applicable when showing a .djvu or .pdf file).

The options can be given in any order. If the given *options* conflict each other, the latter is applied, except for the *format* options, where the options take the priority in the order of: **frame**; **thumb** (or **thumbnail**); **frameless** and/or **border**.

If a parameter does not match any of the other possibilities, it is assumed to be the caption text. Caption text shows below the image in **thumb** and **frame** formats, or as mouseover text in **border**, **frameless** formats or when the format is omitted. Caption text displayed in the **thumb** and **frame** formats may contain wiki links and other formatting. In the other options, wiki-formatting will not work though transclusion will.

If no caption text is supplied, a caption is automatically created showing the file name. To completely remove the caption, set it to `<span title=""></span>`. For example, `[[File:Example.jpg|20px|<span title=""></span>]]` renders as [Image: 20px-Example.jpg](https://www.profounddecisions.co.uk/empire-wiki/File:Example.jpg).

### Stopping the text flow

On occasion it is desirable to stop text (or other inline non-floating images) from flowing around a floating image. Depending on the web browser's screen resolution and such, text flow on the right side of an image may cause a section header (for instance, == My Header ==) to appear to the right of the image, instead of below it, as a user may expect. The text flow can be stopped by placing **<br style="clear: both" />** before the text that should start below the floating image.

All images rendered as blocks (including non-floating **center**ed images, **left**- or **right**-floating images, as well as **framed** or **thumbnail**ed floating images) are implicitly breaking the surrounding lines of text (terminating the current block of text before the image, and creating a new paragraph for the text after them). They will then stack vertically along their left or right alignment margin (or along the center line between these margins for **center**ed images).

## Linking to an image without displaying it

### Link to description page

If you put a colon (`:`) before `File:`, the image will not be embedded and the link will lead to the description page of the file.

```
[[:File:MediaWiki:Image sample]]
[[:File:MediaWiki:Image sample|Sunflowers]]
```

results in

[[:File:MediaWiki:Image sample]]
[[:File:MediaWiki:Image sample|Sunflowers]]

### Link to another page

**Note:** link **does not work with** thumb **or** frame.

This will make a 50px width picture with a link to the page MediaWiki:

```
[[File:Example.jpg|50px|link=MediaWiki]]
```

[Image: Example.jpg](https://www.profounddecisions.co.uk/empire-wiki/MediaWiki)

### Link directly to the media file

You can use the pseudo-namespace “Media” to link directly to a file without rendering it, bypassing the description page.

```
[[Media:MediaWiki:Image sample]]
[[Media:MediaWiki:Image sample|Sunflowers]]
```

results in

[[Media:MediaWiki:Image sample]]
[[Media:MediaWiki:Image sample|Sunflowers]]

The same result can be achieved by adding a colon before the namespace (works with categories too):

```
[[:File:MediaWiki:Image sample]]
```

You can also use:

```
[[Special:FilePath/MediaWiki:Image sample]]
```

which can be used to link to a potential file, even if it doesn't exist. You can also use:

```
{{FILEPATH:MediaWiki:Image sample}}
```

which generates an external URL to the file inline:

## Files at other websites

You can link to an external file available online using the same syntax used for linking to an external web page. With these syntaxes, the image will not be rendered, but only the text of the link to this image will be displayed.

```
[http://url.for/some/image.png]
```

Or with a different displayed text:

```
[http://url.for/some/image.png link text here]
```

Additional MediaWiki markup or HTML/CSS formatting (for inline elements) is permitted in this displayed text (with the exception of embedded links that would break the surrounding link):

```
[http://www.example.com/some/image.png Example '''<del>rich</del>''' ''<ins>link text</ins>'' here.]
```

which renders as: [Example **~~rich~~** *link text* here.](http://www.example.com/some/image.png)

If it is enabled on your wiki (see [Manual:$wgAllowExternalImages](http://www.mediawiki.org/wiki/Manual:$wgAllowExternalImages)), you can also embed external images. To do that, simply insert the image's url:

```
http://url.for/some/image.png
```

Currently, embedded images cannot be resized, but they may be formatted by surrounding MediaWiki markup or HTML/CSS code.

If this wiki option is not enabled, the image will not be embedded but rendered as a textual link to the external site, just like above.

---

Categories: [Help](../../indexes/by-category/Help.md)
