const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Module=require('node:module');
const ts=require('typescript');
const React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');
const filename=path.resolve(__dirname,'../app/maya/week-highlights.tsx');
const component=new Module(filename,module);
component.filename=filename;component.paths=Module._nodeModulePaths(path.dirname(filename));
component._compile(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,filename);
const {WeekHighlights}=component.exports;
const home={confirmed_context:{symptoms:['Heartburn']},dashboard_guidance:{nutrition_focus:'Iron + Calcium',nutrition_focus_detail:'General overview',nutrition:[{id:'stage-nutrition',summary:'Middle-stage guidance'}],movement_focus:'Comfort',movement_focus_detail:'Adapt your pace.',symptoms:[{id:'reported-symptoms',summary:'These are entries.'},{id:'heartburn',summary:'Small, regular meals.'}],overview_content:{energy:{title:'Take a pause',body:'Make room for rest.'}}}};

test('all four highlights use actual dashboard content and category actions',()=>{
  const opened=[];
  const tree=WeekHighlights({home,openTab:id=>opened.push(id),buildPlan:()=>opened.push('build'),hasPlan:false});
  const html=renderToStaticMarkup(tree);
  for(const text of ['Nutrition','Movement','Symptoms','Self-love','Middle-stage guidance','Small, regular meals.','Create my weekly plan']) assert.ok(html.includes(text));
  function visit(node){if(!node || typeof node!=='object')return;if(node.type==='button')node.props.onClick();React.Children.forEach(node.props?.children,visit);}
  visit(tree);
  assert.deepEqual(opened,['nutrition','movement','symptoms','wellbeing','build']);
});

test('no symptoms are invented and existing plan offers rebuild',()=>{
  const changed=structuredClone(home);changed.confirmed_context.symptoms=[];changed.dashboard_guidance.symptoms=[{id:'reported-symptoms',summary:'No symptoms reported.'}];
  const html=renderToStaticMarkup(React.createElement(WeekHighlights,{home:changed,openTab:()=>{},buildPlan:()=>{},hasPlan:true}));
  assert.match(html,/No symptoms reported/);assert.doesNotMatch(html,/Heartburn/);assert.match(html,/Rebuild my weekly plan/);
});

test('overview plan action opens Plans and requests one real balanced build',()=>{
  const source=fs.readFileSync(path.resolve(__dirname,'../app/maya/dashboard.tsx'),'utf8');
  const action=source.slice(source.indexOf('const buildFromHighlights'),source.indexOf('const cardAction'));
  for(const expected of ["setRequestedFocus('balanced')",'setPendingAutoBuild(true)',"setActiveTab('plans')"])assert.ok(action.includes(expected));
  assert.ok(source.includes('if (!autoBuild || autoStarted.current) return'));
});
