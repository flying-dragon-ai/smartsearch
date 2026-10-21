const fs = require("node:fs");
const path = require("node:path");

// Launch npm with this Node without shell parsing (also works on Windows).
module.exports = function npmCommand(args) {
  const directory = path.dirname(process.execPath);
  const candidates = [process.env.npm_execpath,
    path.join(directory, "node_modules/npm/bin/npm-cli.js"),
    path.resolve(directory, "../lib/node_modules/npm/bin/npm-cli.js"),
    path.join(directory, "npm")].filter(Boolean);
  const script = candidates.find(file => fs.existsSync(file));
  if (!script) throw new Error("Cannot locate npm for the selected Node.js");
  return [process.execPath, [fs.realpathSync(script), ...args]];
};
