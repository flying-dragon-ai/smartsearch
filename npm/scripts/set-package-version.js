const fs = require("node:fs");
const path = require("node:path");

const version = process.argv[2];
if (!version || !/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version)) {
  console.error("Usage: node npm/scripts/set-package-version.js <version>");
  process.exit(1);
}

const packageRoot = path.resolve(__dirname, "..", "..");
const packageJsonPath = path.join(packageRoot, "package.json");
const packageLockPath = path.join(packageRoot, "package-lock.json");
const pyprojectPath = path.join(packageRoot, "pyproject.toml");

function writeJsonVersion(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  data.version = version;
  const root = data.packages?.[""] || data;
  if (root.optionalDependencies) {
    for (const name of Object.keys(root.optionalDependencies)) root.optionalDependencies[name] = version;
  }
  if (data.packages) {
    for (const name of Object.keys(root.optionalDependencies || {})) {
      const [, platform, architecture] = name.match(/-(darwin|win32|linux)-(x64|arm64)$/);
      const basename = name.split("/")[1];
      data.packages[`node_modules/${name}`] = {
        version, resolved: `https://registry.npmjs.org/${name}/-/${basename}-${version}.tgz`,
        cpu: [architecture], os: [platform], optional: true, license: "MIT"
      };
      if (platform === "linux") data.packages[`node_modules/${name}`].libc = ["glibc"];
    }
  }
  if (data.packages && data.packages[""]) {
    data.packages[""].version = version;
  }
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

writeJsonVersion(packageJsonPath);
writeJsonVersion(packageLockPath);

const pyproject = fs.readFileSync(pyprojectPath, "utf8");
const versionPattern = /^version = ".*"$/m;
if (!versionPattern.test(pyproject)) {
  console.error("Could not find the project.version field in pyproject.toml.");
  process.exit(1);
}

fs.writeFileSync(pyprojectPath, pyproject.replace(versionPattern, `version = "${version}"`));
console.log(`Set package version to ${version}.`);
