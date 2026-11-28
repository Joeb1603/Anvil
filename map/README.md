# Empire Atlas

An interactive map of the Empire and its neighbours with a timeline from 376YE Winter to
388YE Winter. Open `index.html` in a browser; it is self-contained.

- **Shapes:** built top-down in `mapbuilder/coverage.py`, so every edge exists once and neighbours share
  it exactly: the land's outline comes from the wiki's territory map; it is split into territories
  (thin gaps between the wiki's outlines are divided down their middle); each territory is split
  into its regions with straight lines halfway between the regions' anchor points. The tiling is snapped
  as a whole, merged outlines heal any hairline slit, and every build checks each nation's and
  territory's outline for slits (`seam` in checks.md) so a stray line inside a nation fails the build.
- **Selecting:** clicking the selected nation, territory, region or the sinkhole again clears it; in
  Regions view only the clicked region is outlined. Seas show their name on hover.
- **Zoom:** the mouse wheel, pinch, or the + and − buttons, which step exactly one wheel notch.
- **Map:** 62 territories and seas, 312 regions. Pan, zoom, click a territory or region. Click
  empty sea or background to clear the selection.
- **Timeline:** 49 seasons. Step through them or press Play to watch control change.
- **Colours:** each region shows who holds it that season. Imperial nations are solid colours (each
  its own; Imperial land not yet given to a nation is solid gold). Barbarians and foreign powers are
  hatched with diagonal lines (the Druj in brown, the vallorn in plum); minor foreign powers are grey
  and hatched. Uncontrolled land (parchment) is solid.
- **Keys:** the line key and, under it, a Nations key: a short scrollable list of every power's colour
  that season (click one to open it). The keys are slightly see-through and the map draws under them as usual. The
  Nations key folds away, and is folded on phones.
- **Nation names** are on by default; untick the box to rely on the key alone.
- **Labels (Auto by default):** Auto shows nation names for the first three wheel notches (every Imperial nation is
  always named), territory names in between
  and region names from the seventh wheel notch. Nations, Territories, Regions or None fix it. Nations shows only nation names at every zoom
  (no sea names either, and a Nations-tab journey doesn't switch it to territories; that only happens on Auto). None hides every
  boundary line; clicks and hovers then follow the zoom, as in Auto. Territories shows territory names at every zoom.
  Labels never sit under an event-count circle.
- **Where names go:** nation, territory and region names all work the same way.
  - Each name sits where it can be largest inside its land, measured in the page's own font, on one line or,
    for long names, on two (IRON / CONFEDERACY). It shrinks to fit.
  - **Nations:** names are worked out from each season's nation borders. Up to 18px, down to 7px.
    - Every Imperial nation is named whenever any of its land is on screen, if need be in small type. If even
      that doesn't fit, it goes over its land where it overlaps least.
    - Other powers are named only if the name fits, or nearly fits, over their own land.
    - A power's other blocks of land are named too when the name fits inside them and isn't next to another of
      its names.
  - **Territories:** up to 12px, down to 8px.
  - **Regions:** 11px, growing to 14px with the zoom, down to 8px.
  - A territory or region name never leaves its land, except an Imperial one that almost fits, which is drawn
    at 8px.
  - Imperial nations, territories and regions are named first. Other regions' names are a touch smaller and
    lighter, and only use the room left over. Names never touch: there is always a little gap.
  - Event counts sit beside their name: below it, or else to its right, above it or to its left, wherever there
    is room (over the name's own land if possible).
  - Names stay on the visible map: one whose region is partly off screen (or under the phone's info sheet) moves
    into the part you can see, and none sit under the zoom buttons, the Fighting key, the phone's Key button or
    an open card. The translucent Nations key is the exception: names show through it, as the map does.
- **Clicking and hovering:** follow the label mode in force. In Nations mode a hover describes the
  nation, a click opens it in the Info tab, and each nation shows one event count beside its name; Territories and Regions modes count per
  territory and per region, beside the name;
  in Territories mode the territory; in Regions mode the region. Click empty map to clear.
- **Nations tab:** picking a nation outlines its lands, fades everything else and switches the map
  to territories; opening one of its territories switches to regions; the fading follows down to
  the region you open. Clicking the map (including a faded area, which selects nothing), empty space or another tab ends that and returns to the
  chosen label mode.
- **Boundary lines** follow the label mode: dark lines around each nation's land in Nations view,
  around territories in Territories view, around regions in Regions view (elsewhere region borders
  show as faint lines), in the same dark colour in light and dark mode; colours show each region's real holder, and a split
  territory reads "Mostly held by X (5 of 7 regions)".
- **Borders:** the black boundary lines (see above) mark every border. (Coloured Imperial and barbarian
  border lines were tried and retired: the black lines read better.)
- **Fighting:** crosshatched regions are ones a Wind of War names that season, where the region
  changes hands that season or the next, or its territory is split between the Empire and its
  enemies. It's an approximation of "actively contested"; the panel names the reports.
- **Panel:** the Info tab shows the season (its changes of control and its events, each in a
  fold-out box, plus the territory table), or the selected place or nation: who holds it and what
  happened there in the chosen season, with everything earlier in a fold-out Earlier history box, each linked to its wiki page. Places opened from the Nations tab get a
  Back button that retraces the way (region, territory, nation). The Nations tab lists every
  power; picking one outlines its lands and opens its holdings in place, without moving the
  list. A third tab lists earlier history.
- **The Great Sinkhole** (Lorenzo's Deep Pockets), which the wiki's map draws inside Miaren, shows as a
  black pit from 381YE Summer, when it opened (Wind of Fortune "Rocks and gravel"); before that the
  spot is ordinary land shared between Wood Heath, Vardstein Vale and Goldglades, whose borders meet in
  the middle. Hover or click it for what it is.
- **Event summaries:** every event box shows a one-or-two sentence overview, a "Read more" with a
  short fuller description, and "Read full article" linking to the wiki page. With a nation,
  territory or region selected, the box says what the event means for that nation, territory or
  region; events that only mention it in passing are listed after the rest, under "Also mentioned".
  The summaries are written by Claude from each page (`mapbuilder/summarise.py`, run by the
  "Summarise events" workflow and the daily update using the `ANTHROPIC_API_KEY` repository secret),
  stored in `summaries.json` beside the page, and only rewritten when a page or its places change.
  The page doesn't download that whole file (7 MB): each build splits it into `summaries/index.json`
  (every overview, and which lines each event has: about 260 KB gzipped) and one file per season with
  the fuller text and the lines (about 40 KB gzipped each), fetched the first time something from that
  season is shown. Until it arrives a box shows the overview.
  Spending is recorded in `summaries_cost.json` and capped at $95 in total (the full history cost
  $67.25: a 20-event pilot plus one batch of 1,951).
- **Place names in text are links:** in event summaries and control notes, territory, region and nation
  names open a card on the map, beside the panel (across the top of the map on phones, with the info sheet folded down until you close it), with who holds
  it, any fighting and that season's events there; the map moves to it, outlines it with a dashed
  line and fades everything else. The panel is untouched. Close the card (×, Esc or empty map) and the view goes back to where
  it was; "Open in Info" selects it instead. The card always describes the season on the timeline:
  step or play the timeline and it updates in place.
- **Nations:** picking a nation in the Nations tab or the key moves the map to show all its land as
  large as fits.
- **Search** for a territory, region or event title (places are listed first). ↑ and ↓ pick a result, Enter
  opens it (or the first one), Esc closes the list. An event opens on its own in the Info tab (its season,
  summary and full article), with every territory and region it touches listed with what happened there;
  the map frames them all and fades the rest, and picking one opens its card.
- **On phones** the map fills the screen. ⌕ opens search and ☰ the map options (with the credits);
  the Key button shows the keys. Tapping a place or nation slides its information up from the
  bottom (half height, so the map stays in view); drag or tap the handle for full height or to put
  it away, and tap empty sea to clear. On a phone held sideways (any touch screen under 500 px tall, however wide)
  the phone layout stays, with a one-row season bar; the closed panel is just its handle and title, and it opens
  down the right-hand side instead. On phones the buttons, tabs and handle are at least 44px, and each event count
  has a tap area at least 32px across. Double-tap zooms in one step; pinch and drag as usual. Tablets and computers keep
  the side-by-side layout.

- **Keyboard:** Tab reaches the map; with the map focused (click it, or Tab to it) the arrow keys pan.
  Anywhere except while typing, + and − zoom, 0 resets the view, [ and ] step through the seasons and /
  jumps to search. Opening a place from a link moves focus into its card, and closing the card (Esc or ×)
  puts focus back where it was. Screen readers hear the season once the timeline settles, the number of
  search results, and what a search result opened.
- **Nations key counts:** each nation in the key shows how many regions it holds that season.
- **Shareable links:** the address keeps the season, what is open (a place, a nation or an event, or the
  Nations or Earlier history tab), the label mode and the view, e.g.
  `#s=388YE%20Autumn&t=Astolat&r=The%20Chase&v=6.00,1010,760`. Copy it to share exactly what you see;
  opening it restores the same view, on any screen.

## Where the data comes from

| Layer | Source | How reliable |
|---|---|---|
| Territory outlines | The polygons of the wiki's clickable Gazetteer map | Exact copy |
| Region positions | The name labels on the wiki's hand-drawn territory maps, read by eye | Good: 293 of 306 placed from a label |
| Region borders | Each territory outline divided around those label positions | **Approximate.** The wiki has no border data |
| Events | 1,970 dated archive pages, placed by the territories and regions they link to or name in the text (ignoring people's surnames, donors, sponsors, senators' titles and rosters; region names that usually mean something else, like Terunael, count only beside their territory) | Mechanical |
| Control over time | Read out of the Winds of War reports and territory pages | **Interpretation**, see below |

Thirteen regions had no usable label (Ayereed and the Mountains of the Moon have no map;
Crucible in Madruga is not on its map) and are placed by compass words in their description
or simply spread out. The page says so when you select one.

### Control over time

Who held each region, season by season, was extracted by reading prose: the outcome sections
of the Winds of War pages for every event, and the history sections of the territory pages.
The raw extractions are in `control_raw/`, one file per era plus one for the territory pages.

- 574 entries from the reports, plus the territory pages' own histories: changes of control, plain
  statements of who held what, and territory-level statements that are listed but not painted
  onto individual regions.
- Every entry names its source page, and the page links to it.
- Entries the sources leave unclear are marked uncertain.

Each region starts with the holder its first report gives for it: a change says who held the
region before it, and a plain statement says who holds it. Where that disagrees with the
territory as a whole (Holberg's walls, Greensward in Mournwold and so on), the region keeps its
own record, and loose whole-territory statements such as "Karsk is Varushkan" do not paint over it.
A whole-territory statement that doesn't say which regions it covers ("the Druj regain the east")
is listed but not painted. When the territory page and a campaign report date the same change
differently, the report wins.

When the Senate gives a territory to a nation (`nation_history.json`: Spiral to Urizen and later
the League, Skarsind to the Imperial Orcs, Ossium to Varushka, Mareave to the Imperial Orcs,
Sarangrave to Urizen), the regions the Empire already holds there pass to that nation from that
season, and a report's bare "the Empire" means whichever nation the territory belonged to then.

Known gaps the sources do not resolve include what happened to Greenwall after it was conquered,
Liathaven between 381YE and 384YE, and the per-region picture at the very start where no report
names a region. Treat the earliest seasons as the least certain.

### Atlas checks

Every build runs `mapbuilder/checks.py` and writes the results to `checks.md` (and `checks.json`).
It fails on anything that probably makes the map wrong:

- a control record naming a territory or region the map doesn't have;
- a place with no known holder today, or none in any season, or a holder with no legend entry;
- a report saying someone held a region (or territory) just before a change, when the map shows
  someone else then (checked for every report, not only the first: 245 region changes);
- two reports giving the same region different holders in the same season;
- a missing season, or pages dated outside the timeline.

It warns about things that may be missing: regions positioned by guesswork rather than a wiki map,
Winds of War attached to no place, holders known only from today's territory page with no date,
changes a territory page dates only by year, and "the Empire" with no nation where the territory
has one. Explained exceptions, each with its reason, are in `checks_accepted.json`; today there are
12 (the Mountains of the Moon have no region map, and seven reports describe a partial occupation
or a change undone between summits). The daily update flags failures on its run; an update from the
scheduled Claude task is refused if it adds a failure.

Seasons within an Imperial year run Spring, Summer, Autumn, Winter. In real life each year's
events open with a Winter Solstice, which closes the previous Imperial year: the wiki counts
Winter Solstice 2014 as the fifth Empire event and Spring Equinox 2014 as the sixth. That pattern
holds before and after the pandemic.

### Checked against the wiki's own maps

The wiki has two dated territory maps: "End of Winter 378YE" (Map-tactical2-y3e1) and
"The Empire, Spring 381" (Map-tactical-MASTER-IC-01). The atlas agrees with both on which
territories were Imperial and who held the rest. Ossium isn't drawn on either map, so it can't be
compared. They also settled one conflict between sources: Nitrost in Karsk returned to Varushka in
378YE Winter, recorded in `control_raw/corrections.json`. That file also holds changes found by
reading the sources when the checks flagged them: Deer's Folly in Hercynia held by the vallorn
throughout, Crowslook and Branoc retaken by the Golden Axe in 379YE Winter, Dogri Thulebane's
Winterfolk rebels holding Crow's Ridge 379YE Winter to 381YE Spring, Miechernya ceded to the Thule in
383YE Winter, the Jotun sweep of Liathaven in 384YE Winter, and Ribeira back in Jotun hands by 387YE
Summer.

Ayereed's regions are read from "Ayereed regions.png", which appears on other pages rather than
Ayereed's own. Madruga's are from "Madruga Made Anew.png", the post-blight map that adds the
Crucible, and Otkodov's three outline parts are its regions Nithoggir, Urdur and Sküld. The Mountains of the Moon have no region map anywhere on the wiki, so they stay
placed by the compass directions in their descriptions.

### Territories with no page of their own

Eight territories on the wiki's map have no page: Tathar, Raineach and Shayeel (the Grendel lands
of Attar), Shavronne, Veroigne and Kalino (the Iron Confederacy, which conquered Kalino from the
Lasambrian orcs by 379YE Winter and calls it Arbonne), and Bryadvik and Fjorknae (Jotun). Their
holders come from the Bay of Catazar and Sea of Snow pages and the campaign reports, and are
recorded in `control_raw/outlying.json`.

Holder colours are kept in `holder_colours.json`, so a nation keeps its colour when new holders
appear.

### Tsirku

Wintermark began exploring Tsirku, the frozen wasteland north of Sermersuaq, in 388YE. The wiki's
own map stops short of it, so its outline and three regions (Warriors' Gate, an unnamed region and
the unexplored north) are hand-drawn estimates from the reports, kept in `extra_territories.json`
and drawn with a dashed border. Only the southern edge follows real borders. Nobody holds it yet.
Selecting it shows a dated exploration log with links to the source reports, and every dated page
that mentions Tsirku is placed on it.

### The Covid break

The Covid lockdown fell between 383YE Autumn (Autumn Equinox 2019) and 383YE Winter. That
summit's Winds of War were written in March 2020, a couple of weeks before lockdown, and it
finally ran as Winter Solstice 2022. No events ran in 2020 or 2021 and in-game time paused, so
real and in-game years drift apart by two:

| | Winter Solstice | Spring to Autumn |
|---|---|---|
| Up to 2019 | in-game year + 1637 | in-game year + 1636 |
| From 2022 | in-game year + 1639 | in-game year + 1638 |

The timeline marks the break and shows the real-world event for every season. The naming rule
agrees with all 31 wiki event pages that state their in-game season, and with the 4 that give
their running number.

## Rebuilding

```
python3 -m mapbuilder.geometry    # territory outlines from the Gazetteer page
python3 -m mapbuilder.regions     # region lists from territory pages
python3 -m mapbuilder.partition   # region cells from map/region_labels.json
python3 -m mapbuilder.events      # dated pages tied to places
python3 -m mapbuilder.build       # data.json and index.html
```

Requires the archive in `wiki/` and `data/`, plus `numpy` and `opencv-python-headless`.
`region_labels.json` and `control_raw/` are hand-read inputs; edit them to correct the map.

## Licence

- Event titles and excerpts are text by Profound Decisions under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), as for the rest of the
  archive (see `wiki/LICENSE.md`).
- Territory outlines and region positions are derived from the wiki's map art. The wiki's
  [terms](https://www.profounddecisions.co.uk/empire-wiki/Terms_and_conditions) keep game art
  with its artists and allow non-commercial reuse, so that part of the data is **not** under
  CC BY-SA: use it non-commercially and credit Profound Decisions and the map artists.
- No map image from the wiki is included here.
