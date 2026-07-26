# poptrayminus
POP3 mailbox monitor with tray icon notifications and preview/delete functions for spam control PopTray Minus is a Linux clone of original PopTray written in Python/Qt. PopTray Minus lives happily in the tray, regularly checks message headers in POP3 mailbox, applies basic filters based on from/to/subj contents, allows a sneak peek to preview the message body and, of course, features a very handy delete button to manually remove unwanted messages.

### A bit of history
poptrayminus was written around or before 2009, happily used for many years, but with the untimely demise of python2 I have to rewrite that in py3 / qt5. At the same time, I'm trying to put together all old versions I have in the same repository, so you can easily check to see how it evolved.

### Installation

I don't have any GPG-protected channel for distribution, so you may just download .deb package from this page and install it using your favourite software manager. It should work with python3 and should automatically install all dependencies, `python-chardet`, `python-qt5` and maybe a couple of others. If you want to use python2/qt4 -- stick with version 1.4 -- that's the latest one that works on python2.

## Development

If you want to develop and package this yourself, you'll need to install `devscripts`. The original project configuration was created using `dch --create` and the installation package can be created using `debuild --no-tgz-check` running in `poptrayminus` folder (where all these `debian/` folders and `setup.py` scripts are)

### tests

There is a small pytest suite in `tests/`, covering the settings storage, the POP3 handling and the message filtering logic. Run it with `python3 -m pytest tests` (needs `pytest`, `PyQt5` and `chardet`); the GUI parts run headless via `QT_QPA_PLATFORM=offscreen`, which the tests set for you.

Every push and pull request runs `flake8` and the suite on python 3.9 and 3.12, see `.github/workflows/ci.yml`.

### py3 / qt5 conversion leftovers

The 1.5.0 conversion left a few things behind that have since been fixed:

* Qt4 settings API -- `QSettings.value()` returns a plain object on Qt5, so `.toString()` / `.toInt()` and the `QVariant` wrappers around `setValue()` / `setData()` are gone.
* signal connections written as `QtCore.QObject.<widget>.<signal>(type).connect(...)`, which never connected anything -- the protocol combo did not update the port field and the context menu actions did nothing.
* `QVBoxLayout.setMargin()` and `QtWidgets.QKeySequence`, both Qt4-only, used to kill the app whenever the preview or about window was opened.
* python3 `base64` wants bytes -- saving an account from the settings dialog used to die silently, without writing anything.
* python3 integer division -- window and column sizes are computed with `//` now, `resize()` and `setColumnWidth()` do not take floats.
* python3 `poplib` returns bytes -- UIDL and message data are decoded before use, so preview and delete work again (they were permanently disabled before, as the `+OK` check silently failed).

### other fixes

* `-debug` is a command line switch again, it used to be hardwired to `True` -- every run dumped all the message headers and the whole settings dict, including the password, to stdout.
* encoded headers (`=?utf-8?B?...?=`) are decoded, so non-ascii subjects and names are readable in the message list.
* removing more than one account no longer takes out the wrong tabs in the main window, and an account with no name shows `user@host` instead of `None`.
* if the desktop has no system tray, the main window is shown right away and closing it quits -- the app used to start up completely invisible, with no way out but `kill`.

### message cache

The headers of the messages already seen are kept in `~/.cache/poptrayminus/{host}_{md5(user)}.json.gz` (`$XDG_CACHE_HOME` is honoured), so a big mailbox is not pulled through POP3 all over again on every start -- only the UIDLs that are not in the cache get fetched. The cache is written after every scan, is per account, and is simply ignored (and refilled) when it is missing, unreadable or written by another version. Servers with no UIDL support get no cache, as message numbers are not stable enough to key anything on.

Message bodies are cached too, but only lazily: the text of a message is kept the first time you preview it, so opening it again is instant and works with the server down. Scans still pull headers only (`TOP n 0`), as fetching every body up front would be exactly the bandwidth hog this is meant to avoid. The bodies are capped at `CACHE_BODIES` messages and `CACHE_BODY_BYTES` of text, dropping the least recently read ones.

It is gzipped json rather than a pickle on purpose: `pickle.load()` would run whatever ends up in that file, and `zcat` on the cache still shows you what is in there.

### distribution
I tried to distribute this by myself before, and that was quite a pain in the behind, though, poptrayminus has found its way into a few linux distributions (thank you, guys).

Now, with all source code available and unlimited rights to make any changes you may do anything you like, package it with anything you want and have fun doing that.
