"""Publishable, non-destructive return-link editions of the approved public gifts.

Original downloads remain untouched. All inputs are public RN resources. No
subscriber data, credentials, paid-library files, or private addresses are used.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request
from zipfile import ZipFile, ZIP_DEFLATED

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
import qrcode

GIFT = "https://relentless-nature.com/free-gifts/"
UPDATES = GIFT + "#free-gift-updates"
VISIBLE = "relentless-nature.com/free-gifts/"
COMPANION = "RN_More_Free_Resources_and_Optional_Updates.pdf"
COMPANION_URL = "https://relentless-nature.com/wp-content/uploads/2026/10/" + COMPANION
COMPANION_SHA = "99f53e20edf33478d028f3c964f3a9721eb2a21c27ab290e1b71394780e4dcbd"
ROOT = Path("rn-gifts-return-links")
CACHE = ROOT / "originals"
ASSETS = ROOT / "assets"
RELEASE_TAG = "free-gifts-return-links-2026-10-21"
RELEASE_BASE = "https://github.com/Relentlessnature/open-affiliate/releases/download/" + RELEASE_TAG + "/"
INK = (55 / 255, 32 / 255, 82 / 255)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_manifest() -> tuple[list[dict], str]:
    # Read data without executing the original script or rebuilding its release.
    tree = ast.parse(Path("scripts/build_public_rn_gifts.py").read_text())
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"MANIFEST", "README"}:
                    values[target.id] = ast.literal_eval(node.value)
    assert len(values["MANIFEST"]) == 29
    return values["MANIFEST"], values["README"]


def fetch(url: str, path: Path, expected_size: int | None = None) -> bytes:
    if path.exists():
        data = path.read_bytes()
    else:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RN-Gift-Return-Links/1.0"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        path.write_bytes(data)
    if expected_size is not None and len(data) != expected_size:
        raise ValueError("Original size changed: " + path.name)
    signature = b"%PDF-" if path.suffix.lower() == ".pdf" else b"\x89PNG\r\n\x1a\n"
    if len(data) < 1024 or not data.startswith(signature):
        raise ValueError("Invalid source: " + path.name)
    return data


def qr_png(url: str = GIFT) -> bytes:
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4, box_size=8)
    code.add_data(url)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white").convert("RGB")
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


QR = qr_png()


def add_link(page, rect, uri):
    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(rect), "uri": uri})


def small_footer(page):
    # This area is blank in the three inspected one-page originals. Keep the
    # original footer, page dimensions, writing spaces and cut lines intact.
    page.insert_text((48, 720), "Find more free resources", fontname="hebo", fontsize=8.5, color=INK)
    page.insert_text((48, 734), "Optional email updates: " + VISIBLE, fontsize=8, color=INK)
    add_link(page, (46, 709, 260, 723), GIFT)
    add_link(page, (46, 724, 440, 737), UPDATES)
    rect = fitz.Rect(506, 678, 560, 732)
    page.insert_image(rect, stream=QR)
    add_link(page, rect, GIFT)


def cut_card_links(page, kind):
    # Add links inside each cut-out rather than relying on a sheet footer.
    if kind == "pocket":
        for y in (175, 328, 481):
            for x in (45, 315):
                rect = fitz.Rect(x + 202, y + 91, x + 244, y + 133)
                page.insert_image(rect, stream=QR)
                add_link(page, rect, GIFT)
                text_rect = fitz.Rect(x + 10, y + 133, x + 193, y + 141)
                result = page.insert_textbox(text_rect, VISIBLE, fontsize=5.5, color=INK, align=1)
                assert result >= 0
                add_link(page, text_rect, GIFT)
    elif kind == "appreciation":
        for y in (118, 338, 558):
            for x in (81, 315):
                rect = fitz.Rect(x + 164, y + 154, x + 206, y + 196)
                page.insert_image(rect, stream=QR)
                add_link(page, rect, GIFT)
                text_rect = fitz.Rect(x + 12, y + 204, x + 204, y + 212)
                result = page.insert_textbox(text_rect, VISIBLE, fontsize=5.2, color=INK, align=1)
                assert result >= 0
                add_link(page, text_rect, GIFT)


def update_pdf(source: Path, output: Path, companion: bytes) -> dict:
    original = fitz.open(source)
    document = fitz.open(source)
    before = [p.get_text() for p in original]
    dimensions = [(p.rect.width, p.rect.height) for p in original]
    name = source.name
    inline = name in {
        "RN_When_You_Dont_Know_What_to_Say.pdf",
        "RN_A_Small_Place_to_Begin_Again.pdf",
        "RN_Pocket_Cards_Printable.pdf",
    }
    if name == "RN_Pocket_Cards_Printable.pdf":
        cut_card_links(document[0], "pocket")
    if name == "RN_Appreciation_Cards_Printable.pdf":
        cut_card_links(document[0], "appreciation")
    if name == "RN_Everyday_Support_Pack_Printable.pdf":
        cut_card_links(document[2], "appreciation")
        cut_card_links(document[4], "pocket")
    if inline:
        small_footer(document[0])
    else:
        return_page = fitz.open(stream=companion, filetype="pdf")
        document.insert_pdf(return_page)
        return_page.close()
    # Keep original metadata and useful text; no rasterizing or page shrinking.
    document.save(output, garbage=3, deflate=True)
    document.close()
    check = fitz.open(output)
    assert len(check) == len(original) + (0 if inline else 1)
    for index, text in enumerate(before):
        assert check[index].rect.width == dimensions[index][0]
        assert check[index].rect.height == dimensions[index][1]
        assert text in check[index].get_text(), (name, index, "original text changed")
    uris = [link.get("uri") for p in check for link in p.get_links()]
    assert GIFT in uris and UPDATES in uris, name
    # Render-preservation check for all untouched original pages.
    touched = {0} if inline or name == "RN_Appreciation_Cards_Printable.pdf" else set()
    if name == "RN_Everyday_Support_Pack_Printable.pdf":
        touched = {2, 4}
    unchanged = 0
    for index in range(len(original)):
        if index not in touched:
            a = original[index].get_pixmap(matrix=fitz.Matrix(.5, .5), alpha=False)
            b = check[index].get_pixmap(matrix=fitz.Matrix(.5, .5), alpha=False)
            assert a.samples == b.samples, (name, index, "unexpected visual change")
            unchanged += 1
    report = {"original_pages": len(original), "updated_pages": len(check),
              "original_text_preserved": True, "original_dimensions_preserved": True,
              "unchanged_pages_pixel_checked": unchanged, "return_links": uris.count(GIFT),
              "optional_signup_links": uris.count(UPDATES)}
    check.close()
    original.close()
    return report


def update_image(source: Path, output: Path) -> dict:
    image = Image.open(source).convert("RGB")
    old_size = image.size
    name = source.name
    if "Cheat_Sheet" in name:
        expanded = Image.new("RGB", (image.width, image.height + 190), "#fffdfa")
        expanded.paste(image, (0, 0))
        image = expanded
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    def center(text, y, size, left=0, right=None):
        right = image.width if right is None else right
        font = ImageFont.truetype(font_path, size)
        bounds = draw.textbbox((0, 0), text, font=font)
        draw.text((left + (right - left - (bounds[2] - bounds[0])) / 2, y), text, font=font, fill="#372052")

    def qr(x, y, size):
        code = Image.open(io.BytesIO(QR)).convert("RGB")
        image.paste(code.resize((size, size), Image.Resampling.NEAREST), (x, y))

    if "Wallpaper" in name:
        center("More free gifts + optional email updates", 2945, 24)
        center(VISIBLE, 2983, 28)
    elif "Pocket_" in name:
        center(VISIBLE, 746, 23)
        qr(1110, 485, 240)
    elif "Appreciation_" in name:
        center(VISIBLE, 1361, 27)
        qr(1118, 1100, 240)
    elif "When_You" in name:
        center("More free gifts + optional email updates", 1905, 22)
        center(VISIBLE, 1938, 22)
        qr(1300, 1720, 132)
    elif "Cheat_Sheet" in name:
        top = old_size[1]
        center("More free gifts + optional email updates", top + 40, 27, 30, image.width - 210)
        center(VISIBLE, top + 90, 30, 30, image.width - 210)
        qr(image.width - 184, top + 20, 148)
    else:
        raise ValueError("Unrecognized image layout: " + name)
    if "Cheat_Sheet" not in name:
        assert image.size == old_size, name
    image.save(output, "PNG", optimize=True)
    return {"original_dimensions": old_size, "updated_dimensions": image.size,
            "qr_included": "Wallpaper" not in name,
            "original_artwork_preserved": True}


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    manifest, readme = original_manifest()
    companion = fetch(COMPANION_URL, CACHE / COMPANION)
    assert sha(companion) == COMPANION_SHA, "Return-page source changed"
    (ASSETS / COMPANION).write_bytes(companion)
    results = []
    for entry in manifest:
        name = entry["url"].rsplit("/", 1)[-1]
        source = CACHE / name
        original_bytes = fetch(entry["url"], source, entry.get("size"))
        output = ASSETS / name
        details = update_pdf(source, output, companion) if name.endswith(".pdf") else update_image(source, output)
        results.append({"source_url": entry["url"], "filename": name, "bundle_path": entry["path"],
                        "source_sha256": sha(original_bytes), "sha256": sha(output.read_bytes()),
                        "url": RELEASE_BASE + name, "bytes": output.stat().st_size, **details})
        print("Validated", name, flush=True)
    notes = """\nRETURN-LINK EDITION - OCTOBER 21, 2026
Find more free resources: https://relentless-nature.com/free-gifts/
Optional email updates: https://relentless-nature.com/free-gifts/#free-gift-updates

QR codes open a resource page; scanning does not subscribe you.
Email updates require a separate voluntary signup. Unsubscribe anytime.
The original content and sharing permissions remain unchanged.
The one-page conversation guide, restart worksheet, and pocket-card sheet
remain one page. Other PDF files include one optional return-links page.
Print only the resource pages you need. Cut-out card sizes are unchanged.
Phone wallpaper dimensions are unchanged. The quick-reference image has an
added return-link footer beneath the original artwork.
"""
    bundle = ASSETS / "RN_Complete_Free_Gift_Collection.zip"
    with ZipFile(bundle, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("README_FIRST.txt", readme + notes)
        archive.writestr("More_Free_Resources_and_Optional_Updates.pdf", companion)
        for item in results:
            archive.write(ASSETS / item["filename"], item["bundle_path"])
    with ZipFile(bundle) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == 31
        for item in results:
            assert sha(archive.read(item["bundle_path"])) == item["sha256"]
    report = {"release_tag": RELEASE_TAG, "gift_count": 29,
              "pdf_count": sum(x["filename"].endswith(".pdf") for x in results),
              "png_count": sum(x["filename"].endswith(".png") for x in results),
              "bundle_entries": 31, "bundle_sha256": sha(bundle.read_bytes()),
              "bundle_url": RELEASE_BASE + bundle.name, "assets": results}
    (ROOT / "verification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "assets"}, indent=2))


if __name__ == "__main__":
    main()
