const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..", "..");
const publicSkillRoot = path.join(packageRoot, "skills", "smart-search-cli");
const packagedSkillRoot = path.join(
  packageRoot,
  "src",
  "smart_search",
  "assets",
  "skills",
  "smart-search-cli"
);

function readTree(root) {
  const files = new Map();
  const pending = [root];

  while (pending.length) {
    const current = pending.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (entry.name === ".DS_Store") continue;
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        pending.push(entryPath);
      } else if (entry.isFile()) {
        files.set(path.relative(root, entryPath).split(path.sep).join("/"), fs.readFileSync(entryPath));
      }
    }
  }

  return files;
}

const publicFiles = readTree(publicSkillRoot);
const packagedFiles = readTree(packagedSkillRoot);

assert.deepEqual(
  [...publicFiles.keys()].sort(),
  [...packagedFiles.keys()].sort(),
  "public and packaged skill files must have the same paths"
);

for (const [relativePath, publicContent] of publicFiles) {
  assert.deepEqual(
    publicContent,
    packagedFiles.get(relativePath),
    `public and packaged skill files differ: ${relativePath}`
  );
}

console.log(`Verified ${publicFiles.size} public and packaged smart-search-cli skill files match.`);
