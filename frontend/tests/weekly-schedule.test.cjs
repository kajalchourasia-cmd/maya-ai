const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const filename = path.resolve(__dirname, '../app/maya/weekly-schedule.tsx');
const compiled = ts.transpileModule(fs.readFileSync(filename,'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
const component = new Module(filename,module);
component.filename=filename;
component.paths=Module._nodeModulePaths(path.dirname(filename));
component._compile(compiled,filename);
const {WeeklySchedule}=component.exports;

test('all seven days visible in accessible comparison table and mobile cards',()=>{
  const items = Array.from({length:7},(_,i)=>[
    {schedule_item_id:'action'+i,day:String(i+1),slot:'Breakfast',origin:'source_linked_catalogue',item:'Meal choices',domain:'nutrition'},
    {schedule_item_id:'claim'+i,day:String(i+1),start:'',item:'One grounded claim',domain:'nutrition'}]).flat();
  const html = renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items}}));
  for(const day of ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']) assert.match(html,new RegExp(day));
  assert.match(html, /<table class="schedule-table"/);
  assert.equal((html.match(/scope="row"/g)||[]).length,7);
  assert.match(html, /class="schedule-mobile"/);
  assert.doesNotMatch(html, /View your day|<details open/);
  assert.equal((html.match(/One grounded claim/g)||[]).length,1);
  assert.match(html,/Guidance retrieved for your plan/);
  assert.match(html,/Breakfast/);
});

test('identical daily reminders appear once without dropping variable daily actions',()=>{
  const items = Array.from({length:7},(_,i)=>[
    {schedule_item_id:'action'+i,day:String(i+1),slot:'Breakfast',origin:'source_linked_catalogue',item:'Choice '+i,domain:'nutrition'},
    {schedule_item_id:'water'+i,day:String(i+1),slot:'Through the day',origin:'source_linked_catalogue',item:'Keep water nearby.',domain:'nutrition'}]).flat();
  const html=renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items}}));
  assert.equal((html.match(/Keep water nearby/g)||[]).length,1);
  assert.match(html,/Every day of your week/);
  for(let i=0;i<7;i++) assert.match(html,new RegExp('Choice '+i));
});

test('partial reminders are not promoted to every day and gaps remain explicit',()=>{
  const items=[{schedule_item_id:'a',day:'1',slot:'Breakfast',item:'Monday choice',domain:'nutrition'},{schedule_item_id:'b',day:'2',slot:'Movement',item:'Tuesday movement',domain:'movement'}];
  const html=renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items}}));
  assert.match(html,/Not scheduled/);
  assert.doesNotMatch(html,/Every day of your week/);
});

test('known meal components become choices without deleting their preparation guidance',()=>{
  const item={schedule_item_id:'a',day:'1',slot:'Breakfast',origin:'source_linked_catalogue',domain:'nutrition',item:'Choose a protein component: Dal OR Tofu. Add a suitable starchy food and vegetables or fruit to make a varied meal; check all ingredients.'};
  const html=renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items:[item]}}));
  assert.match(html,/<li>Dal<\/li>/);assert.match(html,/<li>Tofu<\/li>/);assert.match(html,/Add a suitable starchy food/);
});

test('old evidence-only schedules remain readable without invented meal components',()=>{
  const html = renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items:[{schedule_item_id:'old',day:'1',start:'',domain:'movement',item:'Original claim'}]}}));
  assert.match(html,/Original claim/);
  assert.doesNotMatch(html,/Breakfast/);
});

test('nutrition references never claim calculated or consumed meal totals',()=>{
  const schedule={items:[{schedule_item_id:'a',day:'1',domain:'nutrition',item:'A meal idea'}]};
  const nutritionReferences=[{id:'protein',title:'Protein',reference:'71 g / day',basis:'General reference, not a personal target',source_links:[]}];
  const html=renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule,nutritionReferences}));
  assert.match(html,/Daily nutrition references/);assert.match(html,/71 g \/ day/);
  assert.match(html,/Menu totals: not calculated/);assert.match(html,/not a record of food eaten/);
  assert.match(html,/Your one-day outline/);assert.doesNotMatch(html,/Monday to Sunday|>Monday</);
  const movement=renderToStaticMarkup(React.createElement(WeeklySchedule,{schedule:{items:[{...schedule.items[0],domain:'movement'}]},nutritionReferences}));
  assert.doesNotMatch(movement,/Daily nutrition references/);
});
