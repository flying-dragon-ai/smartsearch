// The npm launcher needs messages before the Python runtime is available.
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const catalog = require("../src/smart_search/assets/i18n/messages.json");

function getLanguage(argv, env, platform = process.platform, home = os.homedir(), system = Intl.DateTimeFormat().resolvedOptions().locale) {
  let preference;
  for (let index = 0; index < argv.length && argv[index] !== "--"; index++) {
    if (argv[index] === "--lang") preference = argv[++index];
    else if (argv[index].startsWith("--lang=")) preference = argv[index].slice(7);
  }
  if (preference === undefined) preference = env.SMART_SEARCH_LANGUAGE;
  if (preference === undefined) {
    const fallback = path.join(home, ".config", "smart-search");
    let directory = env.SMART_SEARCH_CONFIG_DIR || (platform === "win32" && env.LOCALAPPDATA
      ? path.join(env.LOCALAPPDATA, "smart-search") : fallback);
    if (directory === "~" || directory.startsWith("~/") || directory.startsWith("~\\")) directory = path.join(home, directory.slice(2));
    if (!env.SMART_SEARCH_CONFIG_DIR && platform === "win32" && !fs.existsSync(path.join(directory, "config.json"))) directory = fallback;
    try { preference = JSON.parse(fs.readFileSync(path.join(directory, "config.json"), "utf8")).SMART_SEARCH_LANGUAGE; }
    catch { /* Python reports unreadable preferences once its runtime is available. */ }
  }
  const selected = String(preference || "auto").toLowerCase().replaceAll("_", "-");
  if (/^(zh|en)(-|$)/.test(selected)) return selected.slice(0, 2);
  // Invalid explicit values are rejected by the CLI; bootstrap messages still render.
  const locale = env.LC_ALL || env.LC_MESSAGES || env.LANG || system;
  return /^zh/i.test(locale) ? "zh" : "en";
}

function localize(argv = [], env = process.env) {
  const language = getLanguage(argv, env);
  return {
    language,
    t(source, ...args) {
      const template = catalog[source]?.[language === "zh" ? 0 : 1] || source;
      return template.replace(/\{(\d+)\}/g, (match, index) => args[index] === undefined ? match : String(args[index]));
    }
  };
}

module.exports = { getLanguage, localize };
