# Smart Search animations

Code-rendered films for Smart Search. Every page draws one frame per call to `window.render(t)`;
`tools/render.mjs` captures the frames with Playwright and encodes them with ffmpeg. Nothing here is published to npm.

| Film | Length | Contents | Brief |
| --- | --- | --- | --- |
| **同一个问题** (`film/`) | 53 s | The same question asked with the built-in search (grey, 8 fps) and with Smart Search (colour, 60 fps), side by side: Jev routing, search, reading the original page, a cited answer | [film/brief.md](film/brief.md) |
| **配置教程** (`config/`) | 69 s | The Windows App page by page: install the CLI, add and test a provider key, turn on Jev routing, update Skills, settings | [config/brief.md](config/brief.md) |
| **日常使用** (`usage/`) | 62 s | Asking an AI tool, searching and researching in the App, reading Activity, four CLI commands, closing the App | [usage/brief.md](usage/brief.md) |

The README's GIFs in `docs/media/` are cut from these films (see [GIFs](#gifs)). The earlier three proposals are in
[proposals/PLANS.md](proposals/PLANS.md); review notes for the feature film are in [film/REVIEW.md](film/REVIEW.md).

## Build

Requires Node.js 18+, Python 3 with numpy and scipy, ffmpeg on `PATH` and a Playwright Chromium
(`npx playwright install chromium` if you do not have one).

```sh
cd promo
npm install
bash film/build.sh                                  # out/film/smart-search-promo.mp4
bash tools/build.sh config smart-search-config      # out/config/smart-search-config.mp4
bash tools/build.sh usage smart-search-usage        # out/usage/smart-search-usage.mp4
bash tools/build.sh usage smart-search-usage draft  # 960x540 @ 30 fps preview
bash tools/build.sh usage smart-search-usage audio  # rebuild only the sound and remux it
node tools/render.mjs film/index.html out/still.png --still 15.9
```

Each film's `timeline.js` is its one timetable: the picture reads it, and `tools/events.mjs` exports its sound cues.
The feature film has its own score in `film/sound.py`; the tutorials share the calmer score in
`shared/tutorial_sound.py`, built from the same synthesizers. The build peak-limits the mix, normalises it to
-14 LUFS in two linear passes, and limits once more so the encoded file stays under -1 dBTP.

`--size 960x540` renders a draft; `--subframes 4` adds motion blur; `--audio mix.wav` muxes sound.

## GIFs

The tutorials accept `?gif`, which cuts between camera framings instead of easing, so a GIF stores only what changes
inside a shot. Render the GIF sources losslessly (`--crf 0`), so codec noise does not count as change.

```sh
node tools/render.mjs film/index.html out/gif/hero.mp4 --size 1280x720 --fps 15 --start 12.6 --duration 8.8 --crf 0
node tools/render.mjs "usage/index.html?gif" out/gif/ask.mp4 --size 1280x720 --fps 15 --start 3.0 --duration 10.6 --crf 0
node tools/render.mjs "config/index.html?gif" out/gif/config.mp4 --size 1280x720 --fps 15 --start 14.4 --duration 11.2 --crf 0
node tools/render.mjs "usage/index.html?gif" out/gif/usage.mp4 --size 1280x720 --fps 15 --start 17.3 --duration 9.1 --crf 0
ffmpeg -i out/gif/hero.mp4 -vf "fps=15,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" out/gif/hero.gif
```

| GIF in `docs/media/` | Source | Size |
| --- | --- | --- |
| `jev-routing.gif` | feature film 12.6–21.4 s | 3.4 MB |
| `ask-ai.gif` | 日常使用 3.0–13.6 s | 0.7 MB |
| `app-setup.gif` | 配置教程 14.4–25.6 s | 2.1 MB |
| `app-search.gif` | 日常使用 17.3–26.4 s | 1.1 MB |

## Layout

| Path | Contents |
| --- | --- |
| `film/` | The feature film: brief, timetable, page, render logic, score, build wrapper, review notes |
| `config/`, `usage/` | The two tutorials: brief, timetable, page, render logic |
| `shared/app.js`, `shared/app.css` | The Windows App (WinUI 3, light theme) redrawn at 150 %, with its zh-CN strings |
| `shared/tutorial.js`, `shared/tutorial.css` | Tutorial machinery: measured camera framings, pointer path, captions, step chip, cheers |
| `shared/clawd.js`, `shared/actor.js` | Clawd as an 18x10 pixel grid: poses, props, icons; the actor that draws him |
| `shared/motion.js` | Time-only easing, closed-form springs, seeded random, typing rhythm, font preloading |
| `shared/tutorial_sound.py` | The tutorials' score |
| `tools/` | Frame renderer, cue exporter, build script |
| `proposals/` | The three original plans, their preview pages and key frames |
| `assets/` | Smaller copies of the Smart Search icon and the app mascot |

## Credits

- Clawd is Anthropic's mascot. This is an unofficial fan depiction, not affiliated with or endorsed by Anthropic.
- `assets/smart-search-256.png` and `assets/mascot-720.png` are resized copies of Smart Search's own artwork
  (`assets/branding/smart-search.png`, `desktop/windows/Assets/mascot.png`).
- The App screens are a redrawn illustration of the Smart Search Windows App; their text comes from its source.
- Quoted documentation: react.dev `useEffect` reference and "Synchronizing with Effects", checked on 2026-10-20.
- Scores and sound effects are synthesized in `film/sound.py` and `shared/tutorial_sound.py`; no samples are used.
- Fonts (SIL Open Font License 1.1, via Fontsource): Fusion Pixel 12px, Noto Sans SC, ZCOOL KuaiLe, Inter, JetBrains Mono.
- `tools/render.mjs` is a Node port of `scripts/render.py` from [Kianzzz/xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video).
- The Clawd grid follows the derivation in [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar).

Both projects are MIT licensed:

```text
Copyright (c) 2026 周行 (Kianzzz)
Copyright (c) 2026 LemoLab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
