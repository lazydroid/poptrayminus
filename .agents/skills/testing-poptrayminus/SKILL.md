---
name: testing-poptrayminus
description: How to run and GUI-test the poptrayminus PyQt5 tray app end-to-end, including a dummy POP3 server and known py3/Qt4 leftovers that block the UI.
---

# Testing poptrayminus

Single-script app: `python3 poptrayminus/poptrayminus`. Deps: PyQt5, chardet (pytest for the suite).
Unit tests: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests -q`.

## Config

Settings live in `~/.poptrayrc` (QSettings NativeFormat ini). Back it up before testing and
restore afterwards. Prefer creating the account through the Settings dialog. If saving via OK
silently kills the process (`base64.b64encode(str)` TypeError in `save_data()` — fixed as of
the py3-runtime-fixes work, but check), fall back to pre-seeding the file:

```ini
[account0]
name=dummy
host=127.0.0.1
port=1110
user=tester
passwd=<base64 of the password>
interval=30
protocol=POP3
```

With no config at all, launching goes straight to the Settings dialog; click `+` to get an
account form (an empty config produces zero tabs).

## Reaching the main window

The main window is only shown by clicking the `QSystemTrayIcon`. Many test desktops (e.g. the
Plasma panel here) have **no system tray**, and `xdotool windowmap` maps the window but it is
never painted. Best fix — provide a real tray instead of patching the app:

```bash
sudo apt-get install -y stalonetray
cd /tmp && DISPLAY=:0 setsid nohup stalonetray --geometry 3x1+860+120 --icon-size 24 \
    > /tmp/stalonetray.log 2>&1 < /dev/null & disown
```

Start stalonetray **before** the app. Left-click the docked icon to toggle the main window,
right-click for the About/Settings/Quit menu. Only patch `form.showNormal()` into `__main__`
as a last resort, and revert it.

Note: background processes started with a plain `&` may be reaped between tool calls — use
`setsid nohup ... < /dev/null & disown` for both the app and the dummy server, and re-check
with `pgrep -af`. `/tmp` may also be wiped between sessions, so re-create the server script.

## Testing the no-tray fallback (and anything needing a genuinely tray-less desktop)

`QSystemTrayIcon.isSystemTrayAvailable()` returns **true** on the Plasma-ish `:0` desktop even
with no visible tray (KDE DBus services), and killing plasmashell/kded5 does not reliably flip
it. Use a nested X server instead:

```bash
sudo apt-get install -y xserver-xephyr openbox
DISPLAY=:0 setsid nohup Xephyr :7 -screen 900x600 -ac > /tmp/xephyr.log 2>&1 < /dev/null & disown
DISPLAY=:7 setsid nohup openbox > /tmp/openbox.log 2>&1 < /dev/null & disown   # gives a titlebar/close button
DISPLAY=:7 python3 poptrayminus/poptrayminus
```

On `:7` tray availability is correctly false. Xephyr alone has **no window manager**, so there
is no close button — start openbox if you need to test the titlebar close path. Verify process
liveness with `pgrep -x python3` + `/proc/<pid>/cmdline` rather than `pgrep -af <pattern>`,
which also matches your own shell wrapper and gives false "alive" results.

## Checking stdout / the `-debug` flag

Redirected stdout is block-buffered, so a `timeout N python3 ...` run loses the printed settings
dump. Always use `python3 -u` when asserting on stdout content.

## Dummy POP3 server

For retrieval/preview/delete testing, run a small python `socketserver` implementing
USER/PASS/STAT/LIST/UIDL/TOP/RETR/DELE/QUIT on `127.0.0.1:1110`. Requirements:
`LIST <n>` must answer `+OK <n> <size>`, `TOP <n> 0` must return headers, and **UIDL must be
implemented** — without UIDL the Preview and Delete buttons stay disabled. Keep the deleted
set global so deletions persist across connections. Log DELE/RETR to a file to assert on them.
Add an `X-Spam-Score` header to at least one message to exercise the score column colouring.

## Known py3/Qt4 leftovers that may still block the GUI

These have bitten testing before; if the app dies or buttons stay disabled, check them first
(they may already be fixed — verify rather than assume):

* `save_data()`: `base64.b64encode(str(...))` TypeError → OK button kills the app.
* `setColumnWidth(1, self.size().width()/4)` and `resize(width, height)` with float args.
* `strip_err(e[0])` on a `poplib.error_proto` → not subscriptable.
* `check_error()` compares `bytes` to `'+OK'` → UIDL silently dropped → Preview/Delete disabled.
* `BrowserForm`: `layout.setMargin(0)` and `QtWidgets.QKeySequence` are Qt4-only → Preview and
  About crash. Use `setContentsMargins` / `QtGui.QKeySequence`.
* `str(item.data(1, Qt.UserRole))` on a bytes UIDL yields `"b'UID0001'"` → delete/preview
  KeyError. Keep the stored value as-is or decode it.

Temporary patches for the above are acceptable to reach later steps, but revert with
`git checkout -- poptrayminus/poptrayminus` and report them instead of committing.

## Devin Secrets Needed

None — no real mail account is required.
