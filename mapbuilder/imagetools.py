"""Wiki images for the scheduled task to look at: download, add a reading grid, crop.

    python3 -m mapbuilder.imagetools territory "Astolat" OUT.png   # the territory's region map, gridded
    python3 -m mapbuilder.imagetools file "File:Some map.png" OUT.png
    python3 -m mapbuilder.imagetools crop IN.png X0 Y0 X1 Y1 OUT.png   # enlarge part of a gridded image

The grid runs 0-100 across and 0-100 down the original image, with a line every 10 units; crops keep
the full image's units, so positions read from a crop can be used directly. Images are cached under
.cache/images and never committed: they belong to their artists.
"""
from __future__ import annotations

import pathlib
import re
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

from scraper.common import CACHE, USER_AGENT, Api

IMAGES = CACHE / "images"
MAX_SIDE = 1600


def _font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def image_info(api: Api, titles: list[str]) -> dict:
    """{File:title: {"url", "thumburl", "timestamp", "sha1", "width", "height"}}"""
    out = {}
    for i in range(0, len(titles), 40):
        data = api.get(action="query", prop="imageinfo", iiprop="url|timestamp|sha1|size",
                       iiurlwidth=str(MAX_SIDE), titles="|".join(titles[i:i + 40]))
        for p in data["query"]["pages"]:
            if p.get("imageinfo"):
                ii = p["imageinfo"][0]
                out[p["title"]] = {k: ii.get(k) for k in ("url", "thumburl", "timestamp", "sha1", "width", "height")}
    return out


def region_map_titles(api: Api, territories: list[str]) -> dict:
    """{territory: File:title} — the region map used on each territory page (best guess by file name)."""
    imgs: dict[str, list[str]] = {}
    for i in range(0, len(territories), 25):
        for data in api.query_all(prop="images", imlimit="500", titles="|".join(territories[i:i + 25])):
            for p in data["query"]["pages"]:
                imgs.setdefault(p["title"], []).extend(im["title"] for im in p.get("images", []))

    def score(f):
        s = 0
        if re.search(r"(?i)regions?", f):
            s += 5
        if re.search(r"(?i)border", f):
            s -= 1
        if re.search(r"(?i)strategic|simple|basic|sketch|Region_Map", f):
            s -= 3
        return s

    out = {}
    for t in territories:
        cands = [f for f in imgs.get(t, []) if re.search(r"(?i)region|border|map|strategic|simple|basic", f)
                 or re.fullmatch(r"File:" + re.escape(t) + r"\.(png|jpg)", f)]
        if cands:
            out[t] = sorted(cands, key=lambda f: -score(f))[0]
    return out


def download(api: Api, title: str) -> pathlib.Path:
    IMAGES.mkdir(parents=True, exist_ok=True)
    info = image_info(api, [title]).get(title)
    if not info:
        raise SystemExit(f"No such image on the wiki: {title}")
    dest = IMAGES / (re.sub(r"[^\w.-]+", "_", title.split(":", 1)[1]) + f".{(info['sha1'] or 'x')[:8]}.png")
    if not dest.exists():
        url = info["thumburl"] if (info["width"] or 0) > MAX_SIDE else info["url"]
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(r.content)
        Image.open(tmp).convert("RGB").save(dest)
        tmp.unlink()
    return dest


def grid(src: pathlib.Path, out: pathlib.Path, box=(0, 0, 100, 100), scale_to=1500) -> pathlib.Path:
    """Draw the 0-100 reading grid on src (or on the part of it given by box, in grid units)."""
    im = Image.open(src).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    im = im.crop((int(W * x0 / 100), int(H * y0 / 100), int(W * x1 / 100), int(H * y1 / 100)))
    k = scale_to / max(im.size)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))
    pad = 34
    canvas = Image.new("RGB", (im.width + pad, im.height + pad), "white")
    canvas.paste(im, (pad, pad))
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    font = _font(14)
    step = 10 if x1 - x0 > 30 else 5
    for v in range(0, 101, step):
        if x0 <= v <= x1:
            x = pad + (v - x0) / (x1 - x0) * im.width
            d.line([x, pad, x, pad + im.height], fill=(255, 0, 0, 110), width=1)
            d.text((x - 10, 8), str(v), fill=(200, 0, 0, 255), font=font)
        if y0 <= v <= y1:
            y = pad + (v - y0) / (y1 - y0) * im.height
            d.line([pad, y, pad + im.width, y], fill=(255, 0, 0, 110), width=1)
            d.text((2, y - 8), str(v), fill=(200, 0, 0, 255), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB").save(out)
    return out


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    api = Api()
    cmd = argv[0]
    if cmd == "territory":
        title = region_map_titles(api, [argv[1]]).get(argv[1])
        if not title:
            raise SystemExit(f"No region map found on the page for {argv[1]}")
        src = download(api, title)
        print(f"{title}\nsource: {src}\ngridded: {grid(src, pathlib.Path(argv[2]))}")
    elif cmd == "file":
        src = download(api, argv[1])
        print(f"source: {src}\ngridded: {grid(src, pathlib.Path(argv[2]))}")
    elif cmd == "crop":
        src, box, out = pathlib.Path(argv[1]), tuple(float(v) for v in argv[2:6]), pathlib.Path(argv[6])
        print(f"cropped: {grid(src, out, box)}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
