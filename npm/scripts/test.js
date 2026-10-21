const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { spawnSync } = require("node:child_process");
const root = path.resolve(__dirname, "../..");
const packageJson = require("../../package.json");
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "smart-search-launcher-"));
try {
  fs.mkdirSync(path.join(temp, "npm/bin"), { recursive: true });
  fs.copyFileSync(path.join(root, "npm/bin/smart-search.js"), path.join(temp, "npm/bin/smart-search.js"));
  fs.writeFileSync(path.join(temp, "package.json"), JSON.stringify(packageJson));
  const launch = () => spawnSync(process.execPath, [path.join(temp, "npm/bin/smart-search.js"), "--version"], {
    env: { ...process.env, PATH: temp, PYTHONHOME: "/invalid-python", SMART_SEARCH_PYTHON: "/invalid-python" }, encoding: "utf8"
  });
  let result = launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /missing or damaged/);
  assert.match(result.stderr, /--include=optional/);
  assert.equal(fs.existsSync(path.join(temp, ".smart-search-python")), false);
  const platformName = `${packageJson.name}-${process.platform}-${process.arch}`;
  const native = path.join(temp, "node_modules", platformName);
  fs.mkdirSync(native, { recursive: true });
  fs.writeFileSync(path.join(native, "package.json"), JSON.stringify({ name: platformName, version: "0.0.0" }));
  result = launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /version mismatch/);
  fs.writeFileSync(path.join(temp, "package.json"), JSON.stringify({ ...packageJson, optionalDependencies: {} }));
  result = launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Unsupported platform/);
  console.log("PASS: missing binary, mismatched version, unsupported platform; no Python fallback");
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
