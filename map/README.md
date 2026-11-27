# Empire Atlas

An interactive map of the Empire and its neighbours with a timeline from 376YE Winter to
388YE Winter. Open `index.html` in a browser; it is self-contained.

- **Map:** 61 territories and seas, 306 regions. Pan, zoom, click a territory or region.
- **Timeline:** 49 seasons. Step through them or press Play to watch control change.
- **Colourings:** by holder (who holds each region that season) or by territory.
- **Labels:** Nations (one name per connected block of land a power holds that season),
  Territories, Regions, or None. Labels never sit under an event-count circle, so in busy
  seasons switch Event counts off to see every nation's name.
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
| Events | 1,644 dated archive pages, placed by the territory and region links they contain | Mechanical |
| Control over time | Read out of the Winds of War reports and territory pages | **Interpretation**, see below |

Thirteen regions had no usable label (Ayereed and the Mountains of the Moon have no map;
Crucible in Madruga is not on its map) and are placed by compass words in their description
or simply spread out. The page says so when you select one.

### Control over time

Who held each region, season by season, was extracted by reading prose: the outcome sections
of the Winds of War pages for every event, and the history sections of the territory pages.
The raw extractions are in `control_raw/`, one file per era plus one for the territory pages.

- 605 entries in total: changes of control, plain statements of who held what, and
  territory-level statements that are listed but not painted onto individual regions.
- Every entry names its source page, and the page links to it.
- Entries the sources leave unclear are marked uncertain.
- A sample of ten painted changes was checked against the source wording: nine are stated
  directly and one was already marked as an inference.
- The final season was compared with what each territory page says today. Eight regions
  differed because the sources never date the change; those are applied at the final season
  and labelled as undated.

Each region starts with the holder its first report gives for it: a change says who held the
region before it, and a plain statement says who holds it. Where that disagrees with the
territory as a whole (Holberg's walls, Crowslook and Branoc in Karsk, Greensward in Mournwold and
so on), the region keeps its own record, and loose whole-territory statements such as "Karsk is
Varushkan" do not paint over it. Checked against every region with a report: 137 of 139 agree,
and the other two are places where two sources contradict each other in the same season. When
the territory page and a campaign report date the same change differently, the report wins.

Known gaps the sources do not resolve include when Spiral became Grendel-held, what happened
to Greenwall and Ribeira after they were conquered, and the per-region picture at the very
start (only whole-territory holders are known for 376YE Winter). Treat the earliest seasons
as the least certain.

Seasons within an Imperial year run Spring, Summer, Autumn, Winter. In real life each year's
events open with a Winter Solstice, which closes the previous Imperial year: the wiki counts
Winter Solstice 2014 as the fifth Empire event and Spring Equinox 2014 as the sixth. That pattern
holds before and after the pandemic.

### Checked against the wiki's own maps

The wiki has two dated territory maps: "End of Winter 378YE" (Map-tactical2-y3e1) and
"The Empire, Spring 381" (Map-tactical-MASTER-IC-01). The atlas agrees with both on which
territories were Imperial and who held the rest. Ossium isn't drawn on either map, so it can't be
compared. They also settled one conflict between sources: Nitrost in Karsk returned to Varushka in
378YE Winter, recorded in `control_raw/corrections.json`.

Ayereed's regions are read from "Ayereed regions.png", which appears on other pages rather than
Ayereed's own. The Mountains of the Moon have no region map anywhere on the wiki, so they stay
placed by the compass directions in their descriptions.

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
