import { spawnSync } from "node:child_process";
import { delimiter, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const env = {
	...process.env,
	PYTHONPATH: [join(root, "src"), process.env.PYTHONPATH].filter(Boolean).join(delimiter),
	PYTHONIOENCODING: "utf-8",
};
const result = spawnSync("python", ["-m", "smart_search.cli", ...process.argv.slice(2)], {
	env,
	stdio: "inherit",
	windowsHide: true,
});
process.exit(result.status ?? 1);
