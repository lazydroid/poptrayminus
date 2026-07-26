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

### py3 / qt5 conversion leftovers

The 1.5.0 conversion left a few things behind that have since been fixed:

* Qt4 settings API -- `QSettings.value()` returns a plain object on Qt5, so `.toString()` / `.toInt()` and the `QVariant` wrappers around `setValue()` / `setData()` are gone.
* signal connections written as `QtCore.QObject.<widget>.<signal>(type).connect(...)`, which never connected anything -- the protocol combo did not update the port field and the context menu actions did nothing.
* `QVBoxLayout.setMargin()` and `QtWidgets.QKeySequence`, both Qt4-only, used to kill the app whenever the preview or about window was opened.
* python3 `base64` wants bytes -- saving an account from the settings dialog used to die silently, without writing anything.
* python3 integer division -- window and column sizes are computed with `//` now, `resize()` and `setColumnWidth()` do not take floats.
* python3 `poplib` returns bytes -- UIDL and message data are decoded before use, so preview and delete work again (they were permanently disabled before, as the `+OK` check silently failed).

### distribution
I tried to distribute this by myself before, and that was quite a pain in the behind, though, poptrayminus has found its way into a few linux distributions (thank you, guys).

Now, with all source code available and unlimited rights to make any changes you may do anything you like, package it with anything you want and have fun doing that.
