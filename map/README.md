# Empire Atlas

An interactive map of the Empire and its neighbours with a timeline from 376YE Winter to
388YE Winter. Open `index.html` in a browser; it is self-contained.

- **Map:** 61 territories and seas, 306 regions. Pan, zoom, click a territory or region.
- **Timeline:** 49 seasons. Step through them or press Play to watch control change.
- **Colourings:** by holder (who holds each region that season) or by territory.
- **Labels:** Nations (one name per connected block of land a power holds that season),
  Territories, Regions, or None. Labels never sit under an event-count circle, so in busy
  seasons switch Event counts off to see every nation's name.
- **Clicking:** in Nations mode a click highlights the nation holding that spot; in Territories
  mode it opens the whole territory; in Regions mode, the region. Tick **Focus on click** to fade
  everything else. A highlight clears when you select something else or change tab.
- **Regions box:** hides or shows the borders between regions. Colours always show each region's
  real holder, and a split territory reads "Mostly held by X (5 of 7 regions)".
- **Frontiers:** gold outlines land held by Imperial nations, crimson outlines land held by
  barbarians (Jotun, Druj, Grendel, Thule and barbarian orc bands). The outlines move with the
  timeline. Other holders, such as the vallorn, show as gaps inside the outlines.
- **Panel:** who holds a place, its control history, and the events recorded there, each
  linked to its wiki page. A second tab lists holders; a third lists earlier history.
- **Search** for a territory, region or event title.

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
