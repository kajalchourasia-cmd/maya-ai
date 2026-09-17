const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
function load(relative) {
  const file = path.join(root, relative);
  const m = new Module(file, module);
  m.filename = file;
  m.paths = Module._nodeModulePaths(path.dirname(file));
  const original = m.require.bind(m);
  m.require = name => name === './baby-growth-library' ? load('app/baby-growth-library.ts') : original(name);
  m._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, file);
  return m.exports;
}
const { getGrowthMeasurements } = load('app/growth-measurements.ts');
const { babyGrowthLibrary } = load('app/baby-growth-library.ts');
const { growthAssetBounds } = load('app/growth-asset-bounds.ts');

test('every supported week has deterministic references, with no invented early weights', () => {
  for (let week = 1; week <= 41; week++) {
    const result = getGrowthMeasurements(week);
    assert.equal(result.week, week);
    assert.deepEqual(result, getGrowthMeasurements(week));
    if (week >= 8) {
      assert.match(result.length, /^~/);
      assert.match(result.weight, /^~/);
      assert.ok(result.lengthSource.url.startsWith('https://'));
      assert.ok(result.weightSource.url.startsWith('https://'));
    } else {
      assert.equal(result.weight, null);
      if (week >= 4) assert.match(result.length, /mm$/);
      else assert.equal(result.length, null);
    }
  }
  for (const invalid of [0, 42, 12.5, NaN]) assert.equal(getGrowthMeasurements(invalid), null);
});
test('representative weeks match the fixed sources and expose the length method change', () => {
  assert.equal(getGrowthMeasurements(12).length, '~5.4 cm');
  assert.equal(getGrowthMeasurements(12).weight, '~14 g');
  assert.equal(getGrowthMeasurements(26).length, '~35.6 cm');
  assert.equal(getGrowthMeasurements(26).weight, '~856 g');
  assert.equal(getGrowthMeasurements(41).weight, '~3,597 g');
  assert.match(getGrowthMeasurements(19).lengthBasis, /crown/);
  assert.equal(getGrowthMeasurements(20).lengthBasis, 'Head to heel');
});
test('all mapped artwork has valid visible bounds and an existing file', () => {
  for (const row of babyGrowthLibrary) for (const asset of [row.babyAsset, row.comparisonAsset].filter(Boolean)) {
    const { size: [width, height], bounds: [x, y, right, bottom] } = growthAssetBounds[asset];
    assert.ok(fs.existsSync(path.join(root, 'public', asset)));
    assert.ok(x >= 0 && y >= 0 && right > x && bottom > y && right <= width && bottom <= height);
  }
});
test('dashboard uses clean measurements and balanced imagery, not review-pending labels', () => {
  const src = fs.readFileSync(path.join(root, 'app/maya/dashboard.tsx'), 'utf8');
  const component = src.slice(src.indexOf('function PregnancyComparison'), src.indexOf('const pregnancyFaqs'));
  assert.match(component, /getGrowthMeasurements\(preview.exact_week\)/);
  assert.match(component, /This week, your baby is about the size/);
  assert.equal((component.match(/<BalancedGrowthImage /g) || []).length, 2);
  assert.doesNotMatch(component, /Product review pending|Illustrative size comparison|General week length|General week weight/);
  assert.match(component, /range_confirmation/);
  assert.doesNotMatch(component, /About these estimates|playful comparison/);
  assert.match(component, /Visual estimates only; your scan is your baby’s individual reference\./);
  assert.doesNotMatch(component, /VIEW ALL 41 WEEKS|THIS WEEK’S DEVELOPMENT/);
  assert.match(component, /A LITTLE ABOUT YOUR BABY/);
});
