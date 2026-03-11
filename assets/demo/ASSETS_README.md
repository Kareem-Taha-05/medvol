# Demo Assets

This folder contains all visual assets for the README and documentation site.

## Files expected here

| File | Dimensions | Max size | Purpose |
|------|-----------|----------|---------|
| `demo.gif` | 800×450px | 8 MB | README hero — the most important asset |
| `screenshot_main.png` | 1920×1080px | — | Full window, all four panels loaded |
| `screenshot_3d.png` | 960×960px | — | 3D volume render close-up |
| `screenshot_axial.png` | 480×480px | — | Axial slice view with crosshair |

These files are not committed to the repo until they are recorded.
Add them here, then reference them from README.md and docs/index.md.

---

## Recording the demo GIF

### Recommended tools

- **macOS**: [Kap](https://getkap.co) — free, exports high-quality GIF via Gifski
- **Windows**: [ScreenToGif](https://www.screentogif.com) — free, direct GIF export
- **Linux**: [Peek](https://github.com/phw/peek) or `ffmpeg` + `gifski`

### Recording script (what to show — follow this exactly)

**Total: 12 seconds at 15fps**

| Time | Action |
|------|--------|
| 0:00–0:01 | App is open, phosphor UI visible, command bar in focus |
| 0:01–0:04 | Click **NIFTI FILE**, select a brain file. Pause 0.5s on the dialog. |
| 0:04–0:06 | All four panels snap to life — all three slice views + 3D volume |
| 0:06–0:10 | Slowly click-drag across the axial view. Crosshairs move, sagittal and coronal update |
| 0:10–0:12 | Move mouse to the 3D panel and slowly rotate the volume |

**Tips:**
- Use a real brain NIfTI (IXI dataset T1 works well) for the most impressive render
- Record at your native resolution, then downscale to 800×450
- Keep dead time (pauses with no motion) under 0.5 seconds
- Set the app window to ~1400×850px before recording for clean proportions

### Gifski export settings (macOS Kap)

- FPS: 15
- Quality: 85%
- Width: 800px (height auto)

### ffmpeg conversion (alternative)

```bash
# Convert a screen recording to GIF via Gifski
ffmpeg -i recording.mov -vf "fps=15,scale=800:-1" frames/frame%04d.png
gifski --fps 15 --quality 85 -o demo.gif frames/*.png
```

---

## Screenshots

Capture after recording the GIF — use the same dataset.

```bash
# On Linux with scrot:
scrot screenshot_main.png -d 2

# On macOS: Cmd+Shift+4 → select window
```

Crop `screenshot_3d.png` to show only the left VTK panel at ~960×960.
Crop `screenshot_axial.png` to show only the axial slice row at ~480×260.
