#!/usr/bin/env node

// npm selects the native package; Python and every Python dependency live in it.
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const manifest = require("../../package.json");

function fail(message) {
  console.error(`smart-search: ${message}\nReinstall with: npm install -g ${manifest.name}@${manifest.version} --include=optional`);
  process.exit(1);
}

const platformPackage = `${manifest.name}-${process.platform}-${process.arch}`;
if (!manifest.optionalDependencies?.[platformPackage]) fail(`Unsupported platform: ${process.platform}/${process.arch}.`);
if (process.platform === "linux" && !process.report.getReport().header.glibcVersionRuntime) {
  fail("The Linux binary requires glibc; musl/Alpine is not supported.");
}
let binary;
try {
  const packageFile = require.resolve(`${platformPackage}/package.json`);
  const platformManifest = JSON.parse(fs.readFileSync(packageFile, "utf8"));
  if (platformManifest.version !== manifest.version) throw new Error("Native package version mismatch");
  binary = path.join(path.dirname(packageFile), "runtime", "smart-search", process.platform === "win32" ? "smart-search.exe" : "smart-search");
  fs.accessSync(binary, process.platform === "win32" ? fs.constants.F_OK : fs.constants.X_OK);
} catch (error) {
  fail(`Native package ${platformPackage}@${manifest.version} is missing or damaged (${error.message}).`);
}

// A caller's virtualenv, Conda, or embedded Python must not configure this
// interpreter. Business configuration and proxy variables remain available.
const environment = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !/^(PYTHON|CONDA|_CE_|_PYI_|PYINSTALLER_|VIRTUAL_ENV(?:_|$)|_MEIPASS2$|SMART_SEARCH_PYTHON$)/i.test(key)));
environment.PYTHONUTF8 = "1";
environment.PYTHONIOENCODING = "utf-8";
environment.PYINSTALLER_RESET_ENVIRONMENT = "1";
environment.SMART_SEARCH_PACKAGE_ROOT = path.resolve(__dirname, "../..");
environment.SMART_SEARCH_NODE_PATH = process.execPath;

const child = spawn(binary, process.argv.slice(2), {
  cwd: process.cwd(), env: environment, stdio: "inherit", windowsHide: true
});
for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.on(signal, () => { if (!child.killed) child.kill(signal); });
}
child.on("error", error => fail(`Cannot start the packaged runtime: ${error.message}`));
child.on("exit", (code, signal) => process.exit(code ?? (128 + (os.constants.signals[signal] || 1))));
