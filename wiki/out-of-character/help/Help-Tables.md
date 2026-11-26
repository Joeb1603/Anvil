---
title: Help:Tables
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Tables
class: out-of-character
topic: help
categories:
- Help
last_edited: '2012-02-15T09:59:59Z'
revision: 60
---

# Help:Tables

**Tables** may be authored in wiki pages using either XHTML table elements directly, or using wikicode formatting to define the table. XHTML table elements and their use are well described on various web pages and will not be discussed here. The benefit of wikicode is that the table is constructed of character symbols which tend to make it easier to perceive the table structure in the article editing view compared to XHTML table elements.

As a general rule, it is best to avoid using a table unless you need one. Table markup often complicates page editing.

## Wiki table markup summary

|  |  |
| --- | --- |
| ``` {| ``` | **table start** |
| ``` |+ ``` | table **caption,** *optional;* only between **table start** and first **table row** |
| ``` |- ``` | **table row,** *optional on first row* -- wiki engine assumes the first row |
| ``` ! ``` | **table header** cell, *optional.* Consecutive **table header** cells may be added on same line separated by double marks (`!!`) or start on new lines, each with its own single mark (`!`). |
| ``` | ``` | **table data** cell, *required!* Consecutive **table data** cells may be added on same line separated by double marks (`||`) or start on new lines, each with its own single mark (`|`). |
| ``` |} ``` | **table end** |

- The above marks must **start on a new line** except the double `||` and `!!` for optionally adding consecutive cells to a line. However, blank spaces at the beginning of a line are ignored.
- **XHTML attributes.** Each mark, except table end, optionally accepts one or more XHTML attributes. Attributes must be on the same line as the mark. Separate attributes from each other with a single space.
  - Cells and caption (`|` or `||`, `!` or `!!`, and `|+`) hold content. So separate any attributes from content with a single pipe (`|`). Cell content may follow on same line or on following lines.
  - Table and row marks (`{|` and `|-`) do not directly hold content. Do *not* add pipe (`|`) after their optional attributes. If you erroneously add a pipe after attributes for the table mark or row mark the parser will delete it *and* your final attribute if it was touching the erroneous pipe!
- **Content** may (a) follow its cell mark on the same line after any optional XHTML attributes or (b) on lines below the cell mark. Content that uses wiki markup that itself needs to start on a new line, such as lists, headings, or nested tables, must be on its own new line.
  - **Pipe character as content.** To insert a pipe (`|`) character into a table use the <nowiki>`|`</nowiki> escaping markup

## Basics

The following table lacks borders and good spacing but shows the simplest wiki markup table structure.

| You type | You get |
| --- | --- |
| ``` {| |Orange |Apple |- |Bread |Pie |- |Butter |Ice cream  |} ``` | Orange Apple Bread Pie Butter Ice cream |

The cells in the same row can be listed on one line separated by `||` (two pipe symbols). If the text in the cell contains a line break, use `<br />` instead.

| You type | You get |
| --- | --- |
| ``` {| |Orange||Apple||more |- |Bread||Pie||more |- |Butter||Ice<br />cream||and<br />more |} ``` | Orange Apple more Bread Pie more Butter Ice cream and more |

Extra spaces within cells in the wiki markup, as in the wiki markup below, do not affect the actual table rendering.

| You type | You get |
| --- | --- |
| ``` {| |  Orange    ||   Apple   ||   more |- |   Bread    ||   Pie     ||   more |- |   Butter   || Ice cream ||  and more |} ``` | Orange Apple more Bread Pie more Butter Ice cream and more |

You can have longer text or more complex wiki syntax inside table cells, too:

| You type | You get |
| --- | --- |
| ``` {| |Lorem ipsum dolor sit amet,  consetetur sadipscing elitr,  sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat,  sed diam voluptua.   At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.  | * Lorem ipsum dolor sit amet * consetetur sadipscing elitr * sed diam nonumy eirmod tempor invidunt |} ``` | Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet consetetur sadipscing elitr sed diam nonumy eirmod tempor invidunt |

### Table headers

Table headers can be created by using "`!`" (exclamation mark) instead of "`|`" (pipe symbol). Headers usually show up bold and centered by default.

| You type | You get |
| --- | --- |
| ``` {| ! align="left"|Item ! Amount ! Cost |- |Orange |10 |7.00 |- |Bread |4 |3.00 |- |Butter |1 |5.00 |- !Total | |15.00 |} ``` | Item Amount Cost Orange 10 7.00 Bread 4 3.00 Butter 1 5.00 Total 15.00 |

**Note:** When using attributes as in the heading 'Item' a vertical bar '|' is used for separation. Not an exclamation character '!'.

### Caption

A **table caption** can be added to the top of any table as follows.

| You type | You get |
| --- | --- |
| ``` {| |+Food complements |- |Orange |Apple |- |Bread |Pie |- |Butter |Ice cream  |} ``` | Food complements Orange Apple Bread Pie Butter Ice cream |

## XHTML attributes

You can add XHTML attributes to tables. For the authoritative source on these, see [the W3C's HTML 4.01 Specification page on tables](http://www.w3.org/TR/REC-html40/struct/tables.html).

### Attributes on tables

Placing attributes after the table start tag (`{|`) applies attributes to the entire table.

| You type | You get |
| --- | --- |
| ``` {| border="1" align="center" style="text-align:center;" |Orange |Apple |12,333.00 |- |Bread |Pie |500.00 |- |Butter |Ice cream |1.00 |} ``` | Orange Apple 12,333.00 Bread Pie 500.00 Butter Ice cream 1.00 |

### Attributes on cells

You can put attributes on individual **cells**. For example, numbers may look better aligned right.

| You type | You get |
| --- | --- |
| ``` {| border="1" |Orange |Apple |align="right" | 12,333.00 |- |Bread |Pie |align="right" | 500.00 |- |Butter |Ice cream |align="right" | 1.00 |} ``` | Orange Apple 12,333.00 Bread Pie 500.00 Butter Ice cream 1.00 |

You can also use **cell** attributes when you are listing multiple **cells** on a single line. Note that the **cells** are separated by `||`, and within each **cell** the attribute(s) and value are separated by `|`.

| You type | You get |
| --- | --- |
| ``` {| border="1" | Orange || Apple     || align="right" | 12,333.00 |- | Bread  || Pie       || align="right" | 500.00 |- | Butter || Ice cream || align="right" | 1.00 |} ``` | Orange Apple 12,333.00 Bread Pie 500.00 Butter Ice cream 1.00 |

### Attributes on rows

You can put attributes on individual **rows**, too.

| You type | You get |
| --- | --- |
| ``` {| border="1" |Orange |Apple |align="right"|12,333.00 |- |Bread |Pie |align="right"|500.00 |- style="font-style:italic; color:green;" |Butter |Ice cream |align="right"|1.00 |} ``` | Orange Apple 12,333.00 Bread Pie 500.00 Butter Ice cream 1.00 |

#### Simple one-pixel table border

The default table formatting uses the "border-collapse: separate" model, which adds table cell spacing (which also separates the table outer border from its content cells). Even with a zero cellspacing, the borders of consecutive cells (and of the overall table container) will add up, so to get a one-pixel separation between cells, you need to selectively remove one or more of the four borders of cells.

Such tables may be formatted more simply, using the "border-collapse: collapse" CSS property; in this table formatting model, the cellspacing attribute (or the CSS "border-spacing:" property) and the table's "padding:" CSS property is ignored and only the larger border of adjacent inner cells (or the table border for outer cells) will be used.

An example of the above for one-pixel table border, using each model (without need for external extensions):

| You type | You get |
| --- | --- |
| ``` {|style="border-collapse: separate; border-spacing: 0; border-width: 1px; border-style: solid; border-color: #000; padding: 0" |- !style="border-style: solid; border-width: 0 1px 1px 0"| Orange !style="border-style: solid; border-width: 0 0 1px 0"| Apple |- |style="border-style: solid; border-width: 0 1px 0 0"| Bread |style="border-style: solid; border-width: 0"| Pie |} ``` | Orange Apple Bread Pie |
| ``` {|style="border-collapse: collapse; border-width: 1px; border-style: solid; border-color: #000" |- !style="border-style: solid; border-width: 1px"| Orange !style="border-style: solid; border-width: 1px"| Apple |- |style="border-style: solid; border-width: 1px"| Bread |style="border-style: solid; border-width: 1px"| Pie |} ``` | Orange Apple Bread Pie |

Notes :

- When using the "border-width:" CSS shortcut property, the order of the four space-separated specified values is: top, right, bottom, left. As an example from above:

:   :   "border-width: 0 1px 0 0"
:   When there are fewer than 4 values, the value for left takes its default from the value for right, the value for bottom takes its default from the value for top, and the value for right takes its default from the value for top.

- The HTML attributes (such as "width=", "border=", "cellspacing=", "cellpadding=") do not need any length unit (the pixel unit is assumed). The CSS style properties (which override the HTML attributes) require an explicit length unit (if the value is not 0) such as "px" for the pixel.

### HTML colspan and rowspan

You can use HTML **colspan** and **rowspan** attributes on cells for advanced layout.

| You type | You get |
| --- | --- |
| ``` {| border="1" !colspan="6"|Shopping List |- |rowspan="2"|Bread & Butter |Pie |Buns |Danish |colspan="2"|Croissant |- |Cheese |colspan="2"|Ice cream |Butter |Yoghurt |} ``` | Shopping List Bread & Butter Pie Buns Danish Croissant Cheese Ice cream Butter Yoghurt |

### With HTML attributes and CSS styles

CSS style attributes can be added with or without other HTML attributes.

| You type | You get |
| --- | --- |
| ``` {| style="color:green; background-color:#ffffcc;" cellpadding="10" cellspacing="0" border="1" |Orange |Apple |- |Bread |Pie |- |Butter |Ice cream  |} ``` | Orange Apple Bread Pie Butter Ice cream |

#### Attributes

**Attributes** can be added to the caption and headers as follows.

| You type | You get |
| --- | --- |
| ``` {| border="1" cellpadding="20" cellspacing="0" |+ align="bottom" style="color:#e76700;" |''Food complements'' |- |Orange |Apple |- |Bread |Pie |- |Butter |Ice cream  |} ``` | Food complements Orange Apple Bread Pie Butter Ice cream |

#### Column width

**Column width** can be added as follows.

You type:

```
{| style="color:black; background-color:#ffffcc;" width="85%" cellpadding="10%" cellpadding="15%" cellspacing="0" border="1"
| colspan="2" | This column width is 85% of the screen width (and has a background color)
|-
| style="width: 30%;background-color:white;"| '''This column is 30% counted from 85% of the screen width'''
| style="width: 70%;background-color:orange;"| '''This column is 70% counted from 85% of the screen width (and has a background color)'''
|}
```

You get:

|  |  |
| --- | --- |
| This column width is 85% of the screen width (and has a background color) | |
| **This column is 30% counted from 85% of the screen width** | **This column is 70% counted from 85% of the screen width (and has a background color)** |

### Accessibility of table header cells

Table header cells do not explicitly specify which table data cells they apply to (those on their right on the same row, or those below them on the same column). When the table is rendered in a visual 2D environment, this is usually easy to infer.

However when tables are rendered on non-visual medias, you can help the browser to determine which table header cell applies to the description of any selected cell (in order to repeat its content in some accessibility helper) using a scope="row" or scope="col" attribute on table header cells. In most cases with simple tables, you'll use scope="col" on all header cells of the first row, and scope="row" on the first cell of the following rows:

| You type | You get |
| --- | --- |
| ``` {| border="1" cellspacing="0" cellpadding="2" |- !scope="col"| Item !scope="col"| Quantity !scope="col"| Price |- !scope="row"| Bread | 0.3 kg | $0.65 |- !scope="row"| Butter | 0.125 kg | $1.25 |- !scope="row" colspan="2"| Total | $1.90 |} ``` | Item Quantity Price Bread 0.3 kg $0.65 Butter 0.125 kg $1.25 Total $1.90 |

## Caveats

### Negative numbers

If you start a cell on a new line with a negative number with a minus sign (or a parameter that evaluates to a negative number), your table can get broken, because the characters `|-` will be parsed as the wiki markup for table row, not table cell. To avoid this, insert a space before the value (`| -6`) or use in-line cell markup (`|| -6`).

### CSS vs Attributes

Table borders specified through CSS rather than the border attribute will render incorrectly in a small subset of text browsers.

### Common attributes for columns, column groups and row groups

The MediaWiki syntax for tables currently offers no support for specifying common attributes for columns (with the HTML element `<col />`), column groups (HTML element `<colgroup>...</colgroup>`) and row groups (HTML elements `<thead>...</thead>`, `<tbody>...</tbody> and <tfoot>...</tfoot>). Those standard HTML elements are not accepted even in their HTML or XHTML syntax.`

`All the rows and cells (header or data) of the table are rendered within a single implicit row group (HTML element <tbody>...</tbody>) without any attributes or styles.`

`## See also``- meta:Help:Sorting
- wikipedia:Help:Tables`

---

Categories: [Help](../../indexes/by-category/Help.md)
