// Keep the main npm package, platform dependency pins, lockfile and Python metadata together.
const { execFileSync } = require("node:child_process");
const path = require("node:path");
execFileSync(process.execPath, [path.join(__dirname, "set-package-version.js"), require("../../package.json").version], { stdio: "inherit" });
