const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..", "..");
const packageJson = JSON.parse(fs.readFileSync(path.join(packageRoot, "package.json"), "utf8"));

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || packageRoot,
    env: options.env || process.env,
    encoding: "utf8",
    shell: options.shell || false,
    stdio: options.capture ? "pipe" : "inherit",
    windowsHide: true
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    if (options.capture) {
      process.stdout.write(result.stdout || "");
      process.stderr.write(result.stderr || "");
    }
    throw new Error(`${command} ${args.join(" ")} exited with ${result.status || 1}.`);
  }

  return result.stdout || "";
}

function runNpm(args, options = {}) {
  const [node, arguments_] = require("./npm-command")(args);
  return run(node, arguments_, options);
}

const nativeDirectory = process.argv[2];
assert.ok(nativeDirectory, "Usage: node npm/scripts/smoke-packed-install.js <platform-package-directory>");

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "smart-search-tarball-"));
const tarballDir = path.join(tempRoot, "tarball");
const installPrefix = path.join(tempRoot, "install");
const callerCwd = path.join(tempRoot, "caller");
const homeDir = path.join(tempRoot, "home");
fs.mkdirSync(tarballDir);
fs.mkdirSync(callerCwd);
fs.mkdirSync(homeDir);

const packed = JSON.parse(
  runNpm(["pack", "--json", "--pack-destination", tarballDir], { capture: true })
);
assert.equal(packed.length, 1, "npm pack must produce exactly one tarball");
assert.ok(packed[0].files.some(file => file.path === "npm/bin/smart-search.js"));
assert.ok(!packed[0].files.some(file => file.path.endsWith(".py") || file.path.includes("postinstall")), "main package must not install source Python");
const nativePacked = JSON.parse(runNpm(["pack", path.resolve(nativeDirectory), "--json", "--pack-destination", tarballDir], { capture: true }))[0];
assert.ok(nativePacked.files.some(file => /runtime\/smart-search\/smart-search(?:\.exe)?$/.test(file.path)));
assert.ok(nativePacked.files.some(file => /(?:libpython|Python|python313\.dll)/i.test(file.path)), "native package must contain its interpreter");

const tarballPath = path.join(tarballDir, packed[0].filename);
assert.ok(fs.existsSync(tarballPath), `npm pack did not create ${tarballPath}`);
runNpm(["install", "--offline", "--ignore-scripts", "--global", "--no-audit", "--no-fund", "--prefix", installPrefix,
  tarballPath, path.join(tarballDir, nativePacked.filename)]);

const installedRoot = path.join(installPrefix, process.platform === "win32" ? "" : "lib", "node_modules", "@konbakuyomu", "smart-search");
const wrapperPath = path.join(installedRoot, "npm", "bin", "smart-search.js");
assert.ok(fs.existsSync(wrapperPath), "packed install is missing the smart-search wrapper");

const isolatedEnv = {
  ...process.env,
  HOME: homeDir,
  USERPROFILE: homeDir,
  SMART_SEARCH_CONFIG_DIR: path.join(tempRoot, "config"),
  SMART_SEARCH_LANGUAGE: "en",
  PATH: callerCwd,
  PYTHONHOME: path.join(tempRoot, "broken-python"),
  PYTHONPATH: path.join(tempRoot, "broken-modules"),
  VIRTUAL_ENV: path.join(tempRoot, "broken-venv"),
  CONDA_PREFIX: path.join(tempRoot, "broken-conda"),
  SMART_SEARCH_PYTHON: path.join(tempRoot, "missing-python"),
  _PYI_APPLICATION_HOME_DIR: path.join(tempRoot, "wrong-pyinstaller"),
  INIT_CWD: path.join(tempRoot, "wrong-cwd")
};
const version = run(process.execPath, [wrapperPath, "--version"], {
  cwd: callerCwd,
  env: isolatedEnv,
  capture: true
});
assert.match(version, new RegExp(`smart-search ${packageJson.version.replaceAll(".", "\\.")}`));
for (const [language, heading] of [["zh", "用法"], ["en", "usage"]]) {
  const help = run(process.execPath, [wrapperPath, "config", "list", "--help", "--lang", language], {
    cwd: callerCwd, env: isolatedEnv, capture: true
  });
  assert.ok(help.includes(heading), `installed package is missing ${language} help`);
  const route = JSON.parse(run(process.execPath, [wrapperPath, "route", "用户 query", "--router-mode", "rules", "--lang", language], {
    cwd: callerCwd, env: isolatedEnv, capture: true
  }));
  assert.equal(route.query, "用户 query");
  assert.equal(route.executed_search, false);
}
run(process.execPath, [wrapperPath, "regression"], { cwd: callerCwd, env: isolatedEnv, capture: true });
const smokeOutput = run(process.execPath, [wrapperPath, "smoke", "--mock", "--format", "json"], {
  cwd: callerCwd,
  env: isolatedEnv,
  capture: true
});
assert.equal(JSON.parse(smokeOutput).ok, true, "packed mock smoke must report ok=true");

const uiCheck = JSON.parse(
  run(process.execPath, [wrapperPath, "ui", "--check", "--format", "json"], {
    cwd: callerCwd,
    env: isolatedEnv,
    capture: true
  })
);
assert.equal(uiCheck.ok, true, "packed install must be able to resolve the config UI page");
assert.ok(uiCheck.asset_bytes > 1000, "packed config UI page must not be empty");

const skillsUpdate = JSON.parse(
  run(
    process.execPath,
    [
      wrapperPath,
      "skills",
      "update",
      "--targets",
      "opencode",
      "--skills-root",
      homeDir,
      "--format",
      "json"
    ],
    { cwd: callerCwd, env: isolatedEnv, capture: true }
  )
);
assert.equal(skillsUpdate.ok, true, "packed OpenCode skill update must report ok=true");
assert.equal(skillsUpdate.installed_count, 1, "packed OpenCode skill update must install one target");
const opencodeSkill = path.join(homeDir, ".config", "opencode", "skills", "smart-search-cli", "SKILL.md");
assert.ok(fs.existsSync(opencodeSkill), "packed OpenCode skill update must use the canonical global path");

const skillsStatus = JSON.parse(
  run(
    process.execPath,
    [
      wrapperPath,
      "skills",
      "status",
      "--targets",
      "opencode",
      "--skills-root",
      homeDir,
      "--format",
      "json"
    ],
    { cwd: callerCwd, env: isolatedEnv, capture: true }
  )
);
assert.equal(skillsStatus.targets[0].status, "up_to_date", "packed OpenCode status must inspect the canonical global path");

const capabilities = JSON.parse(run(process.execPath, [wrapperPath, "--desktop-capabilities"], { cwd: callerCwd, env: isolatedEnv, capture: true }));
assert.equal(capabilities.product, "smart-search");
assert.equal(capabilities.desktop_protocol_version, 1);
assert.equal(capabilities.version, packageJson.version);
const protocol = spawnSync(process.execPath, [wrapperPath, "--desktop-backend"], {
  cwd: callerCwd, env: isolatedEnv, encoding: "utf8", timeout: 60000,
  input: JSON.stringify({ id: 1, method: "initialize", params: { protocol_version: 1, independent_cli: true, enable_update_checks: false, config_dir: path.join(tempRoot, "protocol-config") } }) + "\n"
    + JSON.stringify({ id: 2, method: "shutdown", params: {} }) + "\n"
});
assert.equal(protocol.status, 0, protocol.stderr);
const messages = protocol.stdout.trim().split("\n").map(line => JSON.parse(line));
assert.equal(messages.find(message => message.id === 1)?.result?.version, packageJson.version);
assert.ok(messages.find(message => message.id === 2)?.result);
assert.equal(fs.existsSync(path.join(installedRoot, ".smart-search-python")), false);
runNpm(["uninstall", "--global", "--prefix", installPrefix, packageJson.name]);
assert.equal(fs.existsSync(wrapperPath), false);
assert.ok(fs.existsSync(opencodeSkill), "uninstall must preserve Skills");
console.log(`PASS: npm packed install/uninstall, no Python on PATH, poisoned Python environment, UTF-8, Skills and App protocol (${installPrefix})`);
