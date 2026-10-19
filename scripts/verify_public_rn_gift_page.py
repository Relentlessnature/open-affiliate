"""Anonymous external verification for the RN public free-gift page."""
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from pathlib import Path
import ast, re, sys, time, json
URL="https://relentless-nature.com/free-gifts/"
ZIP_URL="https://github.com/Relentlessnature/open-affiliate/releases/download/free-gifts-2026-10-19/RN_Complete_Free_Gift_Collection.zip"
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="a" and attrs.get("href"):self.urls.append(urljoin(URL,attrs["href"]))
        if tag=="img" and attrs.get("src"):self.images.append(urljoin(URL,attrs["src"]))
req=Request(URL,headers={"User-Agent":"Mozilla/5.0 (RN Public Gift Verification)"})
with urlopen(req,timeout=35) as resp:
    status=resp.status
    finalurl=resp.url
    html=resp.read().decode("utf-8","replace")
assert status==200 and "free-gifts" in finalurl, (status,finalurl)
assert "Something useful, freely shared" in html, "Gift heading absent"
assert "Download all the gifts" in html, "Primary gift button absent"
assert "post-password-form" not in html, "Page unexpectedly password protected"
assert "wp-login.php?redirect_to" not in finalurl, "Login redirect"
links=Links();links.feed(html)
assert ZIP_URL in links.urls, "Complete ZIP link missing"
s=Path("scripts/build_public_rn_gifts.py").read_text()
node=next(node for node in ast.parse(s).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="MANIFEST" for t in node.targets))
manifest=ast.literal_eval(node.value)
missing=[p["url"] for p in manifest if p["url"] not in links.urls]
assert not missing, f"Missing individual download links: {len(missing)}"
# Broad physical-street-address text check: do not echo any candidate value.
from html import unescape
visible=unescape(re.sub(r"<[^>]+>"," ",re.sub(r"<(script|style)[^>]*>.*?</\1>"," ",html,flags=re.S|re.I)))
pattern=re.compile(r"\b\d{1,6}\s+(?:[A-Za-z.-]+\s+){1,5}(?:Street|Road|Lane|Avenue|Drive|Boulevard|Court|Terrace|Way|Place)\b",re.I)
assert not pattern.search(visible), "Possible street address in public page"
print("ANONYMOUS HTML CHECK PASS",json.dumps({"http":status,"page":finalurl,"download_links":len(links.urls),"manifest_files":len(manifest),"preview_images":len(links.images),"privacy_pattern":"pass"}))
# Download and open the actual public ZIP (not a local copy or session attachment).
from zipfile import ZipFile
from io import BytesIO
from pypdf import PdfReader
from PIL import Image
request=Request(ZIP_URL, headers={"User-Agent":"Mozilla/5.0 (RN Public Gift Verification)"})
with urlopen(request,timeout=120) as res:
    bundle_bytes=res.read()
with ZipFile(BytesIO(bundle_bytes)) as collection:
    assert collection.testzip() is None, "Public ZIP failed CRC"
    names=collection.namelist()
    assert len(names)==23, ("Incomplete archive",len(names))
    assert any("Six_Step_Method_Guide.pdf" in n for n in names)
    assert any("Seven_Day_Clarity_Challenge.pdf" in n for n in names)
    assert all(any(n.startswith(prefix) for n in names) for prefix in [
        "03_Everyday_Support_Pack/01_When_You_Dont_Know_What_to_Say/",
        "03_Everyday_Support_Pack/02_Pass_Something_Good_Along/",
        "03_Everyday_Support_Pack/03_A_Small_Place_to_Begin_Again/",
        "03_Everyday_Support_Pack/04_Take_a_Moment/"])
    safe_text=collection.read("README_FIRST.txt").decode("utf-8")
    for name in names:
        data=collection.read(name)
        if name.endswith(".pdf"):
            doc=PdfReader(BytesIO(data))
            assert len(doc.pages)>0
            safe_text += "\\n" + "\\n".join(p.extract_text() or "" for p in doc.pages)
        if name.endswith(".png"):
            with Image.open(BytesIO(data)) as img: img.verify()
    candidates=[m.group(0) for m in pattern.finditer(safe_text)]
    candidates=[x for x in candidates if not re.search(r"\bA\s+Small\s+Place\b", x, re.I)]
    assert not candidates, "Potential street address inside ZIP"
    assert "PAUSE" in safe_text.upper(), "Approved Pause step missing"
    print("COMPLETE ZIP PASS",json.dumps({"bytes":len(bundle_bytes),"entries":len(names),"pdfs":sum(n.endswith(".pdf") for n in names),"pngs":sum(n.endswith(".png") for n in names),"privacy_pattern":"pass","crc":"pass"}))

# Browser test of desktop & mobile responsive rendering.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
for label,width,height in [("desktop",1440,900),("mobile",390,844)]:
    options=Options();options.add_argument("--headless=new");options.add_argument("--no-sandbox");options.add_argument("--disable-dev-shm-usage");options.add_argument(f"--window-size={width},{height}")
    driver=webdriver.Chrome(options=options)
    try:
        driver.set_window_size(width,height)
        driver.get(URL)
        time.sleep(3)
        actual=driver.execute_script("return {vw:window.innerWidth,sw:document.documentElement.scrollWidth,body:document.body.innerText};")
        assert "Something useful, freely shared" in actual["body"], label+" heading missing"
        assert actual["sw"] <= actual["vw"]+8, f"{label} horizontal clipping vw={actual['vw']} sw={actual['sw']}"
        giftlinks=driver.find_elements(By.CSS_SELECTOR, "a[href*='RN_Complete_Free_Gift_Collection.zip']")
        assert any(x.is_displayed() for x in giftlinks), label+" download-all button not visible"
        buttons=driver.find_elements(By.CSS_SELECTOR, ".wp-block-button__link")
        assert len(buttons)>=5, label+" buttons missing"
        Path("qa_screenshots").mkdir(exist_ok=True)
        driver.save_screenshot(f"qa_screenshots/{label}.png")
        print("BROWSER PASS",json.dumps({"viewport":label,"width":actual["vw"],"scroll_width":actual["sw"],"buttons":len(buttons),"zip_visible":True}))
    finally:
        driver.quit()
