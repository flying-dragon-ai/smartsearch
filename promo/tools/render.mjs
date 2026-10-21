#!/usr/bin/env node
// Frame-by-frame renderer for pages that expose window.render(t), t in seconds.
// Node port of scripts/render.py from Kianzzz/xilo-opus-video (MIT). Pages are served
// from a local HTTP server rooted at this promo folder, so ES modules and the fonts in
// node_modules/@fontsource load identically for every frame.
//
//   still:   node tools/render.mjs proposals/plan-b/index.html proposals/previews/plan-b.png --still 2.5
//   video:   node tools/render.mjs film/index.html out/film.mp4 --fps 30 --duration 45 --audio out/mix.wav
//   blur:    ... --subframes 4        (motion blur, render time x4)
//   segment: ... --start 8 --duration 4
//   draft:   ... --size 960x540       (pages scale their 1920x1080 stage to the viewport)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
};

function parseArgs(argv) {
  const a = { size: '1920x1080', fps: 30, start: 0, subframes: 1, crf: 16, _: [] };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith('--')) { a._.push(k); continue; }
    const v = argv[++i];
    a[k.slice(2)] = ['fps', 'start', 'subframes', 'crf', 'still', 'duration'].includes(k.slice(2)) ? Number(v) : v;
  }
  if (a._.length !== 2) {
    console.error('usage: render.mjs <page.html> <out.png|out.mp4> [--still T | --duration S] [--size WxH] [--fps N] [--start S] [--subframes N] [--audio file]');
    process.exit(2);
  }
  return a;
}

function serve(root) {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://local').pathname);
    const file = path.join(root, rel);
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    fs.readFile(file, (err, data) => {
      if (err) { res.writeHead(404).end(); return; }
      res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' });
      res.end(data);
    });
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

function write(stream, buf) {
  return stream.write(buf) ? Promise.resolve() : new Promise(r => stream.once('drain', r));
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  const [W, H] = a.size.toLowerCase().split('x').map(Number);
  const [pageArg, out] = a._;
  const [pagePath, query = ''] = pageArg.split('?');
  const rel = path.relative(ROOT, path.resolve(pagePath)).split(path.sep).join('/');
  if (rel.startsWith('..')) throw new Error(`page must live inside ${ROOT}`);
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });

  const server = await serve(ROOT);
  const url = `http://127.0.0.1:${server.address().port}/${rel}${query ? '?' + query : ''}`;
  const browser = await chromium.launch({ args: ['--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('[page error]', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error(`[page ${m.type()}]`, m.text()); });
  await page.goto(url);
  await page.waitForFunction("typeof window.render === 'function' && (window.ready === undefined || window.ready === true)", null, { timeout: 60000 });
  await page.evaluate(() => document.fonts ? document.fonts.ready.then(() => true) : true);

  const t0 = Date.now();
  if (a.still !== undefined) {
    await page.evaluate(t => window.render(t), a.still);
    await page.screenshot({ path: out, type: 'png' });
    console.log(`${out}: still at t=${a.still}s (${Date.now() - t0} ms)`);
    await browser.close(); server.close(); return;
  }
  if (!a.duration) throw new Error('--duration is required for video output');

  const sub = Math.max(1, a.subframes);
  const frames = Math.round(a.fps * a.duration);
  const blur = sub > 1 ? `tmix=frames=${sub}:weights=${Array(sub).fill(1).join(' ')},select='not(mod(n\\,${sub}))',` : '';
  const cmd = ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(a.fps * sub), '-i', '-'];
  if (a.audio) cmd.push('-ss', String(a.start), '-i', a.audio);
  cmd.push('-vf', `${blur}setpts=N/(${a.fps}*TB),format=yuv420p`, '-r', String(a.fps), '-c:v', 'libx264', '-crf', String(a.crf), '-movflags', '+faststart');
  if (a.audio) cmd.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  cmd.push(out);
  const ff = spawn('ffmpeg', cmd, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));

  const total = frames * sub;
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.render(t), a.start + i / (a.fps * sub));
    await write(ff.stdin, await page.screenshot({ type: 'png' }));
    if (i && i % Math.max(1, Math.floor(total / 10)) === 0) console.log(`  ${i}/${total} samples, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close(); server.close();
  ff.stdin.end();
  if (await done !== 0) throw new Error('ffmpeg failed');
  console.log(`${out}: ${frames} frames x ${sub} samples, ${W}x${H} @ ${a.fps}fps, rendered in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}

main().catch(e => { console.error(e.message); process.exit(1); });
