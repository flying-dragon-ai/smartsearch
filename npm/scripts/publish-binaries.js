// Publish only after every native platform has built and passed packed-install
// smoke tests. Publishing the main package is the final step.
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const npmCommand = require("./npm-command");
const manifest = require("../../package.json");
const [directory, tag] = process.argv.slice(2);
if (!directory || !/^[a-z][a-z0-9-]*$/.test(tag || "")) throw new Error("Expected artifact directory and npm dist-tag");
function npm(args) {
  const [node, argv] = npmCommand(args);
  const result = spawnSync(node, argv, { encoding: "utf8", windowsHide: true });
  if (result.error) throw result.error;
  return result;
}
function published(name) {
  const result = npm(["view", `${name}@${manifest.version}`, "--json"]);
  if (result.status === 0) return JSON.parse(result.stdout);
  if ((result.stderr + result.stdout).includes("E404")) return null;
  throw new Error(result.stderr || result.stdout);
}
const existingMain = published(manifest.name);
if (existingMain) {
  const expected = Object.entries(manifest.optionalDependencies);
  const actual = existingMain.optionalDependencies || {};
  const samePlatforms = expected.length === Object.keys(actual).length
    && expected.every(([name, version]) => actual[name] === version);
  if (!existingMain.smartSearchBinary || !samePlatforms) {
    throw new Error("This npm version already exists with a different runtime layout. Bump the version; published packages cannot be replaced.");
  }
}
const packages = Object.keys(manifest.optionalDependencies).map(name => ({
  name, file: path.join(directory, `${name.replace(/^@/, "").replace("/", "-")}-${manifest.version}.tgz`)
}));
for (const entry of packages) {
  if (!fs.existsSync(entry.file)) throw new Error(`Missing required native artifact: ${entry.file}`);
}
for (const { name, file } of [...packages, { name: manifest.name, file: "." }]) {
  if (published(name)) { console.log(`Already published: ${name}@${manifest.version}`); continue; }
  const result = npm(["publish", file, "--access", "public", "--provenance", "--tag", tag]);
  process.stdout.write(result.stdout);
  if (result.status !== 0) throw new Error(result.stderr);
}
