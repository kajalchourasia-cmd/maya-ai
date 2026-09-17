const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const root = path.resolve(__dirname, '..');
const css = fs.readFileSync(path.join(root, 'app/purple-theme.css'), 'utf8');

function luminance(hex) {
  const rgb = hex.match(/[a-f\d]{2}/gi).map(part => {
    const value = parseInt(part, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}
test('energy focus uses a distinct pale blue with readable text in the light theme', () => {
  const guidanceCss = fs.readFileSync(path.join(root, 'app/maya/weekly-guidance.module.css'), 'utf8');
  const background = guidanceCss.match(/\.metrics article:nth-child\(3\)\{background:(#[a-f0-9]{6})/)[1];
  assert.equal(background, '#f0f6fa');
  for (const foreground of ['#526f83', '#493841', '#74666b']) {
    const ratio = (luminance(background) + .05) / (luminance(foreground) + .05);
    assert.ok(ratio >= 4.5, `${foreground} on pale blue: ${ratio}`);
  }
});
test('core purple palette meets normal-text contrast on its surfaces', () => {
  const token = name => css.match(new RegExp(`--${name}:(#[a-f0-9]{6})`))[1];
  for (const foreground of ['dusk-text', 'dusk-soft', 'dusk-accent']) {
    for (const background of ['background', 'dusk-surface', 'dusk-raised']) {
      const ratio = (luminance(token(foreground)) + 0.05) / (luminance(token(background)) + 0.05);
      assert.ok(ratio >= 4.5, `${foreground} on ${background}: ${ratio}`);
    }
  }
});
test('theme control renders an accessible switch without data dependencies', () => {
  const file = path.join(root, 'app/maya/theme-toggle.tsx');
  const source = fs.readFileSync(file, 'utf8');
  const compiled = new Module(file, module);
  compiled.filename = file;
  compiled.paths = Module._nodeModulePaths(path.dirname(file));
  compiled._compile(ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText, file);
  const html = renderToStaticMarkup(React.createElement(compiled.exports.ThemeToggle));
  assert.match(html, /role="switch"/);
  assert.match(html, /aria-checked="false"/);
  assert.match(html, /Light theme/);
  assert.match(fs.readFileSync(path.join(root, 'app/layout.tsx'), 'utf8'), /data-maya-theme="light"/);
  assert.match(html, /aria-label="Purple dark theme"/);
  assert.doesNotMatch(source, /mayaApi|sessionId|localStorage|sessionStorage|fetch\(/);
});
