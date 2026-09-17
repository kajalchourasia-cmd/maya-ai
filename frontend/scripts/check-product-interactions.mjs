import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

// Parse TSX rather than stopping at the first ">" inside an arrow function.
export function inspectButtons(source, fileName = "component.tsx") {
  const file = ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const result = { nativeButtons: 0, componentButtons: 0, failures: [] };
  function visit(node) {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = node.tagName.getText(file);
      if (tag === "button" || tag === "Button") {
        const native = tag === "button";
        result[native ? "nativeButtons" : "componentButtons"] += 1;
        const attrs = node.attributes.properties.filter(ts.isJsxAttribute);
        const actionable = attrs.some(attr => ["onClick", "disabled"].includes(attr.name.getText(file)));
        const submit = attrs.some(attr => attr.name.getText(file) === "type" &&
          attr.initializer && ts.isStringLiteral(attr.initializer) && attr.initializer.text === "submit");
        if (!actionable && !submit) {
          const line = file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1;
          result.failures.push(fileName + ":" + line + ": " + tag + " has no action or disabled contract");
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  return result;
}

function main() {
  const root = fileURLToPath(new URL("../app/", import.meta.url));
  const files = [];
  function walk(path) {
    for (const entry of readdirSync(path)) {
      const full = join(path, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (full.endsWith(".tsx")) files.push(full);
    }
  }
  walk(root);
  const failures = [];
  let nativeButtons = 0;
  let componentButtons = 0;
  for (const file of files) {
    const result = inspectButtons(readFileSync(file, "utf8"), file);
    failures.push(...result.failures);
    nativeButtons += result.nativeButtons;
    componentButtons += result.componentButtons;
  }
  if (failures.length) {
    console.error(failures.join("\n"));
    process.exitCode = 1;
  } else {
    console.log(JSON.stringify({ files_checked: files.length, native_buttons_checked: nativeButtons, component_buttons_checked: componentButtons, failures: 0 }));
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
