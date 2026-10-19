"""Build the publicly shareable Relentless Nature free-gift ZIP from approved RN-hosted assets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import urllib.request, json, io, time
MANIFEST = [
  {
    "path": "01_Six_Step_Method/RN_Six_Step_Method_Guide.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Six_Step_Method_Free_Share.pdf",
    "size": 4475319
  },
  {
    "path": "01_Six_Step_Method/RN_Six_Step_Quick_Reference.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Six_Step_Cheat_Sheet_Free_Share.png",
    "size": 137584
  },
  {
    "path": "02_Seven_Day_Clarity_Challenge/RN_Seven_Day_Clarity_Challenge.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Seven_Day_Clarity_Challenge_Free_Share.pdf",
    "size": 1598165
  },
  {
    "path": "02_Seven_Day_Clarity_Challenge/RN_Tracker_and_Reflection.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Seven_Day_Tracker_Reflection_Free_Share.pdf",
    "size": 453060
  },
  {
    "path": "03_Everyday_Support_Pack/RN_Everyday_Support_Pack_Printable.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Everyday_Support_Pack_Printable.pdf",
    "size": 1302090
  },
  {
    "path": "03_Everyday_Support_Pack/01_When_You_Dont_Know_What_to_Say/RN_When_You_Dont_Know_What_to_Say.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_When_You_Dont_Know_What_to_Say.pdf",
    "size": 71616
  },
  {
    "path": "03_Everyday_Support_Pack/01_When_You_Dont_Know_What_to_Say/RN_When_You_Dont_Know_What_to_Say.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_When_You_Dont_Know_What_to_Say.png",
    "size": 242354
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_Cards_Printable.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_Cards_Printable.pdf",
    "size": 1102270
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_01_A_Difference.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_01_A_Difference.png",
    "size": 258571
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_02_What_I_Appreciate.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_02_What_I_Appreciate.png",
    "size": 267673
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_03_Happy_to_Listen.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_03_Happy_to_Listen.png",
    "size": 271274
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_04_It_Mattered.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_04_It_Mattered.png",
    "size": 272900
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_05_A_Moment_to_Remember.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_05_A_Moment_to_Remember.png",
    "size": 256884
  },
  {
    "path": "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/RN_Appreciation_06_Glad_Youre_Here.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Appreciation_06_Glad_Youre_Here.png",
    "size": 266705
  },
  {
    "path": "03_Everyday_Support_Pack/03_A_Small_Place_to_Begin_Again/RN_A_Small_Place_to_Begin_Again.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_A_Small_Place_to_Begin_Again.pdf",
    "size": 88363
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/RN_Pocket_Cards_Printable.pdf",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Pocket_Cards_Printable.pdf",
    "size": 90692
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Phone_Wallpapers/RN_Wallpaper_01_What_Do_I_Know_1440x3120.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Wallpaper_01_What_Do_I_Know_1440x3120.png",
    "size": 799663
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Phone_Wallpapers/RN_Wallpaper_02_Give_Myself_a_Moment_1440x3120.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Wallpaper_02_Give_Myself_a_Moment_1440x3120.png",
    "size": 809778
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Phone_Wallpapers/RN_Wallpaper_03_What_Matters_Here_1440x3120.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Wallpaper_03_What_Matters_Here_1440x3120.png",
    "size": 803658
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Pocket_Cards_PNG/RN_Pocket_01_What_Do_I_Know.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Pocket_01_What_Do_I_Know.png",
    "size": 72913
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Pocket_Cards_PNG/RN_Pocket_02_Give_Myself_a_Moment.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Pocket_02_Give_Myself_a_Moment.png",
    "size": 81149
  },
  {
    "path": "03_Everyday_Support_Pack/04_Take_a_Moment/Pocket_Cards_PNG/RN_Pocket_03_What_Matters_Here.png",
    "url": "https://relentless-nature.com/wp-content/uploads/2026/10/RN_Pocket_03_What_Matters_Here.png",
    "size": 76713
  }
]
README = """RELENTLESS NATURE - SOMETHING USEFUL, FREELY SHARED

The 6-Step Method: Check Yourself -> Pause -> Observe -> Fact vs. Story -> Get Curious -> Choose.
The 7-Day Clarity Challenge with tracker and reflection.
The Everyday Support Pack: conversation starters, appreciation cards, restart worksheet,
phone wallpapers and pocket cards.

These approved share-edition resources are free to save, print, use, and pass along.
No signup, purchase, reply, affiliate enrollment, social post, or promotion is required.
These sharing permissions do not apply to other paid Relentless Nature products.
"""
out=Path("RN_Complete_Free_Gift_Collection.zip")
with ZipFile(out,"w",ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr("README_FIRST.txt", README)
    for entry in MANIFEST:
        request=urllib.request.Request(entry["url"], headers={"User-Agent":"Mozilla/5.0 (compatible; RN-Gifts/1.0)"})
        last=None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    data=response.read()
                break
            except Exception as e:
                last=e
                time.sleep(3*(attempt+1))
        else:
            raise RuntimeError("Asset retrieval failed for "+entry["path"]) from last
        if len(data) != entry["size"]:
            raise RuntimeError(f"Asset size mismatch: {entry['path']}: {len(data)} vs {entry['size']}")
        if entry["path"].endswith(".png") and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Invalid PNG "+entry["path"])
        if entry["path"].endswith(".pdf") and not data.startswith(b"%PDF-"):
            raise RuntimeError("Invalid PDF "+entry["path"])
        z.writestr(entry["path"],data)
with ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist())==23
print("Created",out.name,"containing 23 verified entries",out.stat().st_size,"bytes")
