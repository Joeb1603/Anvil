---
title: Help:Formatting
source: https://www.profounddecisions.co.uk/empire-wiki/Help:Formatting
class: out-of-character
topic: help
categories:
- Help
last_edited: '2012-02-15T09:29:58Z'
revision: 45
---

# Help:Formatting

You can format your text by using wiki markup. This consists of normal characters like asterisks, single quotes or equal signs which have a special function in the wiki, sometimes depending on their position. For example, to format a word in *italic*, you include it in two pairs of single quotes like `''this''`.

## Text formatting markup

| Description | You type | You get |
| --- | --- | --- |
| character (inline) formatting – *applies anywhere* | | |
| Italic text | ``` ''italic'' ``` | *italic* |
| Bold text | ``` '''bold''' ``` | **bold** |
| Bold and italic | ``` '''''bold & italic''''' ``` | ***bold & italic*** |
| Escape wiki markup | ``` <nowiki>no ''markup''</nowiki> ``` | no ''markup'' |
| Escape wiki markup once | ``` [[API]]<nowiki/>extension ``` | APIextension |
| section formatting – *only at the beginning of the line* | | |
| Headings of different levels | ``` == Level 2 ==  === Level 3 ===  ==== Level 4 ====  ===== Level 5 =====  ====== Level 6 ====== ```  ---   **Note:** • Skip Level 1, it is page name level. <br> • An article with 4 or more headings automatically creates a [table of contents](http://en.wikipedia.org/wiki/Wikipedia:Section#Table_of_contents_(TOC)). | **Level 2** <br> **Level 3** <br> **Level 4** <br> **Level 5** <br> **Level 6** |
| Horizontal rule | ``` Text above ---- Text below ``` | Text above <br> ---  Text below |
| Bullet list | ``` * Start each line * with an [[Wikipedia:asterisk|asterisk]] (*). ** More asterisks gives deeper *** and deeper levels. * Line breaks<br/>don't break levels. *** But jumping levels creates empty space. Any other start ends the list. ``` | • Start each line <br> • with an [asterisk](http://en.wikipedia.org/wiki/asterisk) (\*). • More asterisks gives deeper • and deeper levels. <br> • Line breaks <br> don't break levels. • • But jumping levels creates empty space. <br> Any other start ends the list. |
| Numbered list | ``` # Start each line # with a [[Wikipedia:Number_sign|number sign]] (#). ## More number signs gives deeper ### and deeper ### levels. # Line breaks<br/>don't break levels. ### But jumping levels creates empty space. # Blank lines  # end the list and start another. Any other start also ends the list. ``` | • Start each line <br> • with a [number sign](http://en.wikipedia.org/wiki/Number_sign) (#). • More number signs gives deeper • and deeper <br> • levels. <br> • Line breaks <br> don't break levels. • • But jumping levels creates empty space. <br> • Blank lines <br> • end the list and start another. <br> Any other start also ends the list. |
| Definition list | ``` ;item 1 : definition 1 ;item 2 : definition 2-1 : definition 2-2 ``` | item 1  definition 1  item 2  definition 2-1  definition 2-2 |
| Indent text | ``` : Single indent :: Double indent ::::: Multiple indent ```  ---   **Note:** This workaround may be controversial from the viewpoint of accessibility. | Single indent Double indent Multiple indent |
| Mixture of different types of list | ``` # one # two #* two point one #* two point two # three #; three item one #: three def one # four #: four def one #: this looks like a continuation #: and is often used #: instead<br/>of <nowiki><br/></nowiki> # five ## five sub 1 ### five sub 1 sub 1 ## five sub 2 ```  ---   **Note:** The usage of `#:` and `*:` for breaking a line within an item may also be controversial. | • one <br> • two • two point one <br> • two point two <br> • three three item one  three def one <br> • four four def one  this looks like a continuation  and is often used  instead <br> of <br/> <br> • five • five sub 1 • five sub 1 sub 1 <br> • five sub 2 |
| Preformatted text | ```  Start each line with a space.  Text is '''preformatted''' and  ''markups'' '''''can''''' be done. ```  ---   **Note:** This way of preformatting only applies to section formatting. Character formatting markups are still effective. | ``` Start each line with a space. Text is preformatted and markups can be done. ``` |
| Preformatted text blocks | ```  <nowiki>Start with a space in the first column, (before the <nowiki>).  Then your block format will be     maintained.   This is good for copying in code blocks:  def function():     """documentation string"""      if True:         print True     else:         print False</nowiki> ``` | ``` Start with a space in the first column, (before the <nowiki>).  Then your block format will be     maintained.  This is good for copying in code blocks:  def function():     """documentation string"""      if True:         print True     else:         print False ``` |

## Paragraphs

MediaWiki ignores single line breaks. To start a new paragraph, leave an empty line. You can force a line break within a paragraph with the HTML tag `<br/>`.

## HTML tags

Some [HTML](http://en.wikipedia.org/wiki/HTML) tags are allowed in MediaWiki, for example `<code>`, `<div>`, `<span>` and `<font>`. These apply anywhere you insert them.

| Description | You type | You get |
| --- | --- | --- |
| Inserted <br> (Displays as underline in most browsers.) | ``` <ins>Inserted</ins>  or  <span style="text-decoration: underline;">Underline</span> ``` | Inserted <br> or <br> Underline |
| Deleted <br> (Displays as strikethrough in most browsers.) | ``` <del>Deleted</del>  or  <span style="text-decoration:line-through;">Deleted</span> ``` | ~~Deleted~~ <br> or <br> Deleted |
| Fixed width text | ``` <code>Source code</code>  or  <tt>Fixed width text</tt> ``` | `Source code` <br> or <br> Fixed width text |
| Blockquotes | ``` text above text above <blockquote>blockquote</blockquote> text below text below ``` | text above text above <br> blockquote <br> text below text below |
| Comment | ``` <!-- This is a comment --> Comments are only visible in the edit window. ``` | Comments are only visible in the edit window. |
| Completely preformatted text | ``` <pre> Text is '''preformatted''' and ''markups'' '''''cannot''''' be done</pre> ```  ---   **Note:** For marking up of preformatted text, check the "Preformatted text" entry at the bottom of the previous table. | ```  Text is '''preformatted''' and ''markups'' '''''cannot''''' be done ``` |
| **Customized** preformatted text | ``` <pre style="color:red"> Text is '''preformatted''' with a style and ''markups'' '''''cannot''''' be done </pre> ```  ---   **Note:** A CSS style can be named within the `style` property. | ``` Text is '''preformatted''' with a style and ''markups'' '''''cannot''''' be done ``` |
| **Customized** preformatted text with text wrap according to screen width | ``` <pre style="white-space: pre-wrap"> This longer sentence is used to demonstrate text wrapping. </pre> ``` | ``` This longer sentence is used to demonstrate text wrapping. ``` |

## Inserting symbols

Symbols and other special characters not available on your keyboard can be inserted through a special sequence of characters. Those sequences are called HTML entities. For example, the following sequence (entity) **&rarr;** when inserted will be shown as right arrow HTML symbol → and **&mdash;** when inserted will be shown as an em dash HTML symbol —

---

**Note:** Hover any character to find out the symbol that produces it. Some symbols not available in the current font will appear as empty squares.

| HTML symbol entities | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **á** | **Â** | **â** | **´** | **Æ** | **æ** | **À** | **à** | **ℵ** | **Α** | **α** | **&** | **∧** | **∠** | **Å** | **å** | **≈** | **Ã** | **ã** | **Ä** | **ä** | **„** | **Β** | **β** | **¦** | **•** | **∩** | **Ç** | **ç** | **¸** | **¢** |
| **Χ** | **χ** | **ˆ** | **♣** | **≅** | **©** | **↵** | **∪** | **¤** | **†** | **‡** | **↓** | **⇓** | **°** | **Δ** | **δ** | **♦** | **÷** | **É** | **é** | **Ê** | **ê** | **È** | **è** | **∅** |  |  | **Ε** | **ε** | **≡** | **Η** | **η** |
| **Ð** | **ð** | **Ë** | **ë** | **€** | **∃** | **ƒ** | **∀** | **½** | **¼** | **¾** | **⁄** | **Γ** | **γ** | **≥** | **>** | **↔** | **⇔** | **♥** | **…** | **Í** | **í** | **Î** | **î** | **¡** | **Ì** | **ì** | **ℑ** | **∞** | **∫** | **Ι** | **ι** |
| **¿** | **∈** | **Ï** | **ï** | **Κ** | **κ** | **Λ** | **λ** | **⟨** | **«** | **←** | **⇐** | **⌈** | **“** | **≤** | **⌊** | **∗** | **◊** | **‎** | **‹** | **‘** | **<** | **¯** | **—** | **µ** | **·** | **−** | **Μ** | **μ** | **∇** |  | **–** |
| **≠** | **∋** | **¬** | **∉** | **⊄** | **Ñ** | **ñ** | **Ν** | **ν** | **Ó** | **ó** | **Ô** | **ô** | **Œ** | **œ** | **Ò** | **ò** | **‾** | **Ω** | **ω** | **Ο** | **ο** | **⊕** | **∨** | **ª** | **º** | **Ø** | **ø** | **Õ** | **õ** | **⊗** | **Ö** |
| **ö** | **¶** | **∂** | **‰** | **⊥** | **Φ** | **φ** | **Π** | **π** | **ϖ** | **±** | **£** | **′** | **″** | **∏** | **∝** | **Ψ** | **ψ** | **"** | **√** | **⟩** | **»** | **→** | **⇒** | **⌉** | **”** | **ℜ** | **®** | **⌋** | **Ρ** | **ρ** | **‏** |
| **›** | **’** | **‚** | **Š** | **š** | **⋅** | **§** | **­** | **Σ** | **σ** | **ς** | **∼** | **♠** | **⊂** | **⊆** | **∑** | **⊃** | **¹** | **²** | **³** | **⊇** | **ß** | **Τ** | **τ** | **∴** | **Θ** | **θ** | **ϑ** |  | **Þ** | **þ** | **˜** |
| **×** | **™** | **Ú** | **ú** | **↑** | **⇑** | **Û** | **û** | **Ù** | **ù** | **¨** | **ϒ** | **Υ** | **υ** | **Ü** | **ü** | **℘** | **Ξ** | **ξ** | **Ý** | **ý** | **¥** | **ÿ** | **Ÿ** | **Ζ** | **ζ** | **‍** | **‌** |

| Description | You type | You get |
| --- | --- | --- |
| Copyright symbol | ``` &copy; ``` | **©** |
| Greek delta letter symbol | ``` &delta; ``` | **δ** |
| Euro currency symbol | ``` &euro; ``` | **€** |

See the list of all HTML entities on the Wikipedia article List of HTML entities. Additionally, MediaWiki supports two non-standard entity reference sequences: `&רלמ;` and `&رلم;` which are both considered equivalent to `&rlm;` which is a right-to-left mark. (Used when combining right to left languages with left to right languages in the same page.)

## HTML tags and symbol entities displayed themselves

:   &amp;euro;  → **&euro;**

:   <span style="color: red; text-decoration: line-through;">Typo to be corrected</span>  → **Typo to be corrected**

:   &lt;span style="color: red; text-decoration: line-through;">Typo to be corrected&lt;/span>  → **<span style="color: red; text-decoration: line-through;">Typo to be corrected</span>**

## Other formatting

Beyond the text formatting markup shown above, here are some other formatting references:

- [Links](Help-Links.md)
- [Images](Help-Images.md)
- [Tables](Help-Tables.md)

---

Categories: [Help](../../indexes/by-category/Help.md)
