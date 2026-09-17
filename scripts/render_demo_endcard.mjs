import fs from 'node:fs/promises';
import { chromium } from 'file:///C:/Users/Hrishikesh/Developer/genai/Capstone%20Project/demo-video/node_modules/playwright/index.mjs';
const out = 'C:/Users/Hrishikesh/Developer/maya-ai-product-preview/reports/local/demo-video-20260917';
const browser = await chromium.launch({headless:true});
const page = await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:5180/', {waitUntil:'networkidle'});
const mark = await page.locator('.brand svg').first().evaluate(el=>el.outerHTML);
// A clearly editorial closing card, separate from the captured application.
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;background:#fff9fc;color:#392b37;font-family:'Segoe UI',sans-serif;width:1920px;height:1080px;overflow:hidden}
.wash{position:absolute;width:1100px;height:1100px;right:-420px;top:-470px;background:radial-gradient(circle,rgba(233,203,217,.55),rgba(252,241,247,.2) 52%,transparent 70%)}
.wash.second{left:-450px;top:370px;background:radial-gradient(circle,rgba(217,230,219,.45),transparent 67%)}
.center{position:absolute;left:180px;right:180px;top:230px;text-align:center}
.brand{display:flex;align-items:center;justify-content:center;gap:18px;font-weight:650;font-size:54px;letter-spacing:-2px;color:#603249}.brand svg{width:44px;height:58px;stroke:#ad5b7b;stroke-width:1.4}
.kicker{margin:42px 0 24px;text-transform:uppercase;letter-spacing:5px;font-size:17px;color:#966b82}
h1{font-family:Georgia,serif;font-weight:400;font-size:94px;line-height:1.17;letter-spacing:-2px;margin:0}h1 em{font-style:normal;color:#a65678}
.line{margin:32px auto;width:64px;height:2px;background:#d2aec0}
p{font-size:27px;line-height:1.5;color:#766575;margin:0}
.team{position:absolute;bottom:134px;left:0;right:0;text-align:center;font-size:15px;letter-spacing:3px;color:#9b8495}
</style></head><body><div class="wash"></div><div class="wash second"></div><main class="center"><div class="brand">${mark}<span>maya</span></div><div class="kicker">Thoughtful care, week by week</div><h1>A clearer next step.<br><em>A little more wonder.</em></h1><div class="line"></div><p>For mothers-to-be and new mothers.</p></main><div class="team">GROUP 62 · MAYA AI</div></body></html>`;
await fs.writeFile(out+'/endcard.html',html,'utf8');
await page.setContent(html);
await page.evaluate(()=>document.fonts.ready);
await page.screenshot({path:out+'/endcard.png'});
await browser.close();
console.log(out+'/endcard.png');
