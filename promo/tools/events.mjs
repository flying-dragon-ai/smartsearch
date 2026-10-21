#!/usr/bin/env node
// Writes a film's sound cues to JSON so the synthesizer reads the same timetable as the picture.
//   node tools/events.mjs film/timeline.js out/film/events.json
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [mod, out] = process.argv.slice(2);
if (!mod || !out) { console.error('usage: events.mjs <timeline.js> <out.json>'); process.exit(2); }
const tl = await import(pathToFileURL(path.resolve(mod)).href);
mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
const events = tl.events();
writeFileSync(out, JSON.stringify({ dur: tl.DUR, bpm: tl.BPM, T: tl.T, events }, null, 1));
console.log(`${out}: ${events.length} cues over ${tl.DUR}s`);
