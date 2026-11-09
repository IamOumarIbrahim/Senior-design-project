from playwright.sync_api import sync_playwright
import pathlib, sys
base = pathlib.Path('ui').resolve().as_uri()
jobs = [('ui_tablet_light', '/tablet.html?theme=light&state=ok', 1024, 600),
        ('ui_tablet_dark', '/tablet.html?theme=dark&state=drowsy', 1024, 600),
        ('ui_tablet_cal', '/tablet.html?theme=light&state=cal', 1024, 600),
        ('ui_dashboard', '/dashboard.html', 1536, 1000)]
with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    for name, url, w, h in jobs:
        pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2)
        pg.goto(base + url); pg.wait_for_timeout(500); pg.screenshot(path=f'out/{name}.png'); pg.close()
    b.close()
print('ok')
