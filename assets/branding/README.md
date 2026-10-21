# Smart Search icon

- `source.png` is the original transparent artwork, supplied on 2026-09-20.
  It is preserved unchanged and is never used as a generated output.
- `smart-search.png` is the owner's complete 1024 x 1024 Icon Composer export,
  supplied on 2026-09-21 as `Untitled-iOS-Default-1024@1x.png`. Keep the file
  unchanged, including its Display P3 profile, transparency and 16-bit colour.
- `../../desktop/packaging/macos/SmartSearch.icon/` is the original `Untitled.icon`
  document, renamed for the application. Its layers and embedded source PNG are
  preserved unchanged so the icon remains editable in Icon Composer.

Regenerate the Windows PNG/ICO, fallback macOS ICNS and embedded Web UI icons:

```sh
mise run desktop:icons
```

The task uses the project Python and a pinned Pillow dependency through `uv` on
macOS and Windows. It copies the exported PNG byte for byte and resizes its full
canvas for smaller icons, without trimming, adding margins or changing the design.
`desktop/scripts/Build-Icons.ps1` delegates to the same task for compatibility.

The macOS app build compiles `SmartSearch.icon` using Xcode's asset compiler and
packages its `Assets.car` and generated `SmartSearch.icns` for the system app icon.
It also copies `smart-search.png` for the in-app branding. To compile only the
native icon resources:

```sh
mise run desktop:macos:icon
```

The default output is `.desktop-artifacts/icons/macos/`. Packaged Windows builds
and the Web UI consume the committed generated resources. macOS builds compile
the committed Icon Composer document, with no dependency on Desktop files.
