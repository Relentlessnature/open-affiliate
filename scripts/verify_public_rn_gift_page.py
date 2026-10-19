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
