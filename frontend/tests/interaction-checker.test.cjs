const {test} = require("node:test");
const assert = require("node:assert/strict");

test("button checker handles arrow handlers before onClick", async () => {
  const {inspectButtons} = await import("../scripts/check-product-interactions.mjs");
  const result = inspectButtons('<button onFocus={() => focus()} onClick={() => run()}>Go</button>');
  assert.equal(result.nativeButtons, 1);
  assert.deepEqual(result.failures, []);
});
test("button checker still rejects missing actions", async () => {
  const {inspectButtons} = await import("../scripts/check-product-interactions.mjs");
  assert.equal(inspectButtons('<button onFocus={() => focus()}>Go</button>').failures.length, 1);
});
test("button checker recognises disabled and submit buttons", async () => {
  const {inspectButtons} = await import("../scripts/check-product-interactions.mjs");
  const result = inspectButtons('<><button disabled /><Button type="submit" /><Button onClick={run} /></>');
  assert.equal(result.nativeButtons, 1);
  assert.equal(result.componentButtons, 2);
  assert.deepEqual(result.failures, []);
});
test("button checker does not inspect comments or string examples", async () => {
  const {inspectButtons} = await import("../scripts/check-product-interactions.mjs");
  const result = inspectButtons('/* <button> */ const example = "<Button>";');
  assert.equal(result.nativeButtons + result.componentButtons, 0);
  assert.deepEqual(result.failures, []);
});
