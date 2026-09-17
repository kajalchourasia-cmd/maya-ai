const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const Module = require('node:module');
const path = require('node:path');
const filename = path.resolve(__dirname, '../lib/local-api-bridge.ts');
const mod = new Module(filename, module);
mod._compile(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,filename);
const {bridgeAccess, bridgeSessionCookie} = mod.exports;
const cfg = {mode:'private_development',origin:'http://127.0.0.1:5180',token:'synthetic-unit-test-token-not-a-secret-123456'};
function req(extra={}, method='POST') { return new Request('http://127.0.0.1:5180/api/maya/v1/chat',{method,headers:{host:'127.0.0.1:5180',origin:cfg.origin,'sec-fetch-site':'same-origin',...extra}}); }
test('normal same-origin chat uses fixed approved path',()=>assert.equal(bridgeAccess(req(),['v1','chat'],cfg).upstreamPath,'/v1/chat'));
test('session cookie follows proxy path without weakening protections',()=>{
  assert.equal(bridgeSessionCookie('maya_session=test; HttpOnly; Max-Age=3600; Path=/v1; SameSite=strict'), 'maya_session=test; HttpOnly; Max-Age=3600; Path=/api/maya/v1; SameSite=strict');
  assert.equal(bridgeSessionCookie('unrelated=value; Path=/v1'),null);
});
test('no activation / wrong token config blocks bridge',()=>{
  assert.equal(bridgeAccess(req(),['v1','chat'],{}).allowed,false);
  assert.equal(bridgeAccess(req(),['v1','chat'],{...cfg,token:'short'}).allowed,false);
});
test('remote origins, DNS rebinding host and cross-site calls blocked',()=>{
  for(const headers of [{origin:'https://evil.example'},{host:'evil.example'},{'sec-fetch-site':'cross-site'},{origin:''}]) assert.equal(bridgeAccess(req(headers),['v1','chat'],cfg).allowed,false);
});
test('fixtures, arbitrary upstream routes and traversal are blocked',()=>{
  for(const route of [['v1','demo','chat'],['v1','..','chat'],['health'],['https:','other']]) assert.equal(bridgeAccess(req(),route,cfg).allowed,false);
});
test('UUID-scoped reads only; method restrictions retained',()=>{
  assert.equal(bridgeAccess(req({},'GET'),['v1','home','00000000-0000-0000-0000-000000000000'],cfg).allowed,true);
  assert.equal(bridgeAccess(req({},'GET'),['v1','chat'],cfg).allowed,false);
  assert.equal(bridgeAccess(req(),['v1','home','00000000-0000-0000-0000-000000000000'],cfg).allowed,false);
});
