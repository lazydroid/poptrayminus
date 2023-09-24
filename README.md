# poptrayminus
POP3 mailbox monitor with tray icon notifications and preview/delete functions for spam control PopTray Minus is a Linux clone of original PopTray written in Python/Qt. PopTray Minus lives happily in the tray, regularly checks message headers in POP3 mailbox, applies basic filters based on from/to/subj contents, allows a sneak peek to preview the message body and, of course, features a very handy delete button to manually remove unwanted messages.

### A bit of history
poptrayminus was written around or before 2009, happily used for many years, but with the untimely demise of python2 I have to rewrite that in py3 / qt5. At the same time, I'm trying to put together all old versions I have in the same repository, so you can easily check to see how it evolved.

### Installation

I don't have any GPG-protected channel for distribution, so you may just download .deb package from this page and install it using your favourite software manager. It should work with python3 and should automatically install all dependencies, `python-chardet`, `python-qt5` and maybe a couple of others. If you want to use python2/qt4 -- stick with version 1.4 -- that's the latest one that works on python2.

## Development

If you want to develop and package this yourself, you'll need to install `devscripts`. The original project configuration was created using `dch --create` and the installation package can be created using `debuild --no-tgz-check` running in `poptrayminus` folder (where all these `debian/` folders and `setup.py` scripts are)

### distribution
I tried to distribute this by myself before, and that was quite a pain in the behind, though, poptrayminus has found its way into a few linux distributions (thank you, guys).

Now, with all source code available and unlimited rights to make any changes you may do anything you like, package it with anything you want and have fun doing that.
