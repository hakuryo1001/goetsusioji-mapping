# Font setup for this workspace

Cursor/VS Code **cannot** point `editor.fontFamily` at a `.ttf` file in the repo. The font must be **installed on macOS** first; workspace settings only choose which installed family name to use.

## 1. Install the project font (once)

From the repo root:

```bash
mkdir -p ~/Library/Fonts
cp goetsusioji.ttf ~/Library/Fonts/Goetsusioji.ttf
```

Then **reload the window** (Command Palette → “Developer: Reload Window”).

The file’s internal metadata still says “Source Han Serif CN”, but installing it as `Goetsusioji.ttf` under `~/Library/Fonts/` is enough for macOS to register the **Goetsusioji** family name from the filename in many cases. If PUA still look wrong, use the renamed install below.

### Optional: install with an explicit “Goetsusioji” family name

```bash
python3 scripts/install_font_macos.py
```

That writes a name-patched copy to `~/Library/Fonts/Goetsusioji.ttf`.

## 2. Open this folder as the workspace root

`.vscode/settings.json` applies when **`goetsuese-typer` is the opened folder** (or the root of a `.code-workspace` file).

If you use a **multi-root** workspace (e.g. parent `goetsuese/` with several repos), subfolder `.vscode/settings.json` is **not** loaded automatically. Either:

- open `goetsuese-typer` directly, or  
- add the font settings to your `.code-workspace` file for this folder.

## 3. What the settings do

`editor.fontFamily` in this folder replaces your global stack for the editor. Goetsu BMP PUA (`U+F021`–`U+F545`) come from Source Han / Goetsusioji, not Jyutcitzi (`U+F0000+`).
