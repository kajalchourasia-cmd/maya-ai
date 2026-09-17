// Run with: node --test tests/journey-progress.test.cjs
// Render the real TSX component without a browser or backend. Styles remain
// class names here; their actual layout is checked separately in the browser.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function loadComponent(relative) {
const filename = path.resolve(__dirname, '../app/maya/', relative);
const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
}).outputText;
const componentModule = new Module(filename, module);
componentModule.filename = filename;
componentModule.paths = Module._nodeModulePaths(path.dirname(filename));
const originalRequire = componentModule.require.bind(componentModule);
componentModule.require = name => name.endsWith('.module.css')
  ? { __esModule: true, default: new Proxy({}, { get: (_, key) => String(key) }) }
  : name === './journey-hormones' ? loadComponent('journey-hormones.tsx') : originalRequire(name);
componentModule._compile(compiled, filename);
return componentModule.exports;
}
const { JourneyProgress, DashboardMetrics, NutritionGuidance, NutritionReferenceStrip } = loadComponent('weekly-guidance.tsx');
const { hormoneAtPoint, hormoneTooltipPosition } = loadComponent('journey-hormones.tsx');

function render(start, end = start, stage = 'pregnancy', maternalFact = undefined) {
  const phaseFor = week => week < 14 ? 'First trimester' : week < 28 ? 'Second trimester' : 'Third trimester';
  const phase = stage === 'postpartum' ? 'Early recovery'
    : phaseFor(start) === phaseFor(end) ? phaseFor(start) : `${phaseFor(start)} / ${phaseFor(end)}`;
  const scale = stage === 'postpartum' ? 12 : 40;
  return renderToStaticMarkup(React.createElement(JourneyProgress, { home: {
    journey: { stage }, dashboard_guidance: { overview_content: {maternal_fact: maternalFact}, journey: {
      start, end, range: start !== end, phase, label: `${stage} week ${start}`,
      progress_start: Math.min(start / scale, 1) * 100,
      progress_end: Math.min(end / scale, 1) * 100,
      progress_label: stage === 'postpartum' ? 'Not a recovery score' : 'Pregnancy timeline toward 40 weeks',
    } },
  } }));
}

for (const week of [1, 6, 13, 14, 26, 27, 28, 36, 40, 41, 42]) {
  test(`week ${week} uses its own marker and correct trimester`, () => {
    const html = render(week);
    assert.match(html, /Your body’s changing rhythm/);
    assert.match(html, /Explore the hormone patterns that support pregnancy, week by week\./);
    assert.match(html, new RegExp(`<output class="exploringLabel">Week ${week}<span`));
    assert.doesNotMatch(html, /<output[^>]*>Exploring/);
    assert.match(html, new RegExp(`Current week ${week}`));
    const expected = week < 14 ? 'First' : week < 28 ? 'Second' : 'Third';
    assert.match(html, new RegExp(`${expected} trimester</output>`));
    assert.doesNotMatch(html, /class="phaseLabels"|Your journey · week|You are here/);
    assert.match(html, new RegExp(`Return to your onboarding week ${week}`));
    assert.match(html, /<details class="hormoneGuide">/);
    assert.match(html,/not your hormone levels/);
    assert.match(html,/type="range"/);
    assert.match(html,/Explore a pregnancy week/);
    assert.match(html,/Relaxin/);
    assert.match(html,/Prolactin/);
  });
}

test('month range keeps a shaded span instead of a false exact week', () => {
  const html = render(10, 14);
  assert.match(html, /Weeks 10–14 · approximate/);
  assert.doesNotMatch(html, /Return to your onboarding week/);
  assert.doesNotMatch(html, /aria-current="step"|YOU ARE HERE|data-state="current"/);
  assert.match(html, /First trimester and Second trimester highlighted/);
});

test('every plotted hormone has a plain-language explanation accessible without hover', () => {
  const html = render(22);
  for (const explanation of ['hCG (supports early pregnancy)', 'Progesterone (helps maintain pregnancy)', 'Estrogen (supports pregnancy-related growth)']) {
    assert.ok(html.includes(`aria-label="${explanation}"`));
  }
  assert.doesNotMatch(html, /happy hormone|calm hormone/);
});

test('hover identifies each curve and ignores empty graph space', () => {
  assert.equal(hormoneAtPoint(10,34),0); // hCG peak
  assert.equal(hormoneAtPoint(20,132-43*.98),1); // progesterone anchor
  assert.equal(hormoneAtPoint(20,132-40*.98),2); // estrogen anchor
  assert.equal(hormoneAtPoint(22,5),null);
  assert.equal(hormoneAtPoint(0,132),null);
  assert.equal(hormoneAtPoint(41,34),null);
});

test('tooltip follows the pointer below it and stays within the chart horizontally', () => {
  assert.deepEqual(hormoneTooltipPosition(100,40,700),{left:112,top:54,width:310});
  assert.deepEqual(hormoneTooltipPosition(200,70,700),{left:212,top:84,width:310});
  assert.deepEqual(hormoneTooltipPosition(690,80,700),{left:382,top:94,width:310});
  assert.deepEqual(hormoneTooltipPosition(140,20,280),{left:8,top:34,width:264});
});

test('postpartum retains recovery timeline, not pregnancy trimesters', () => {
  const html = render(6, 6, 'postpartum');
  assert.match(html, /Early recovery/);
  assert.match(html, /Recovery happens at your own pace/);
  assert.match(html, /width:50%/);
  assert.doesNotMatch(html, /Growing, one week|First trimester|YOU ARE HERE/);
});

test('maternal fact follows chart, has tiny icon and no redundant trimester note', () => {
  const html = render(26,26,'pregnancy',{title:'A pause',body:'Take time for yourself.',source_links:[]});
  assert.ok(html.indexOf('aria-label="A LITTLE ABOUT YOU"') > html.indexOf('Educational hormone patterns'));
  assert.doesNotMatch(html, /journeyNote|Your second trimester/);
  assert.match(html, /class="factLabel"><svg/);
  assert.match(html, /<h3>A pause<\/h3>/);
});

test('overview renders exactly the four agreed cards', () => {
  const html = renderToStaticMarkup(React.createElement(DashboardMetrics,{editDetails:()=>{},home:{
    journey:{stage:'pregnancy'},dashboard_guidance:{journey:{range:false,start:26,phase:'Second trimester'},
      nutrition_focus:'Iron + Calcium',nutrition_focus_detail:'A varied diet',movement_focus:'At your pace',movement_focus_detail:'Comfort first',
      overview_content:{energy:{title:'A pause to recharge',body:'Take a comfortable pause.',source_links:[]}}},
  }}));
  assert.equal((html.match(/<article>/g)||[]).length,4);
  for(const label of ['YOUR JOURNEY','NUTRITION FOCUS','ENERGY FOCUS','MOVEMENT FOCUS']) assert.ok(html.includes(label));
  assert.doesNotMatch(html,/YOUR CHANGING BODY|NEXT APPOINTMENT|You will feel/);
});

test('nutrition groups preserve every section once and keep unknown categories visible',()=>{
  const ids=['allergy-exclusions','stage-nutrition','heartburn-adjustment','protein','iron','calcium','folate','hydration','supplements','food-safety','future-section'];
  const nutrition=ids.map(id=>({id,title:`Title ${id}`,summary:`Summary ${id}`,tone:id.includes('allergy')||id.includes('heartburn')?'context':'general',reference:null,basis:null,food_options:[],bullets:[],source_links:[]}));
  const html=renderToStaticMarkup(React.createElement(NutritionGuidance,{guidance:{nutrition,unmatched_allergies:[],reference_note:'Reference',food_note:'Food note'}}));
  for(const group of ['Shaped around you','Your everyday nourishment','Supplements &amp; food safety']) assert.ok(html.includes(group));
  for(const id of ids) assert.equal(html.split(`Title ${id}`).length-1,1);
});

test('nutrition strip reuses sourced values and links to the matching full guidance',()=>{
  const sections=[{id:'protein',reference:'71 g / day',bullets:[]},{id:'folate',reference:'600 mcg DFE / day',bullets:[]},{id:'hydration',reference:null,bullets:['General pregnancy reference: 8–12 US cups of water daily (about 1.9–2.8 litres).']}];
  const html=renderToStaticMarkup(React.createElement(NutritionReferenceStrip,{sections}));
  for(const text of ['71 g / day','600 mcg DFE / day','8–12 US cups / day','not an intake tracker','href="#guidance-protein"']) assert.ok(html.includes(text));
  assert.doesNotMatch(html,/progressbar|Consumed|27 mg/);
});

test('nutrition strip never reinstates a withheld fluid target or fabricates missing nutrients',()=>{
  const html=renderToStaticMarkup(React.createElement(NutritionReferenceStrip,{sections:[{id:'hydration',reference:null,bullets:['Your reported restrictions take priority; confirm a fluid target with your care team.']}]}));
  assert.match(html,/Follow your care guidance/);
  assert.doesNotMatch(html,/8–12|71 g|Iron|Calcium|Folate/);
  assert.equal(renderToStaticMarkup(React.createElement(NutritionReferenceStrip,{sections:[]})), '');
});
