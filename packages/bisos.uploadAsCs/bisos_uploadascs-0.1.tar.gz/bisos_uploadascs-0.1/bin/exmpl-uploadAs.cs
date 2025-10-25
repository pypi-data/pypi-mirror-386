#!/usr/bin/env python

####+BEGIN: b:prog:file/particulars :authors ("./inserts/authors-mb.org")
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars |]]* :: Authors, version
** This File: /bisos/git/auth/bxRepos/bisos-pip/loadAsCs/py3/bin/exmpl-loadAs.cs
** File True Name: /bisos/git/auth/bxRepos/bisos-pip/loadAsCs/py3/bin/exmpl-loadAs.cs
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

from bisos import b
from bisos.b import cs

from bisos.b import b_io

from bisos.basics import pathPlus
from pathlib import Path

from bisos.uploadAsCs import uploadAsCs_seed

uploadAsCs_seed.setup(
    seedType="common",
)

def examples_csu() -> None:
    cs.examples.menuChapter(f'*Seed Extensions*')
    cs.examples.cmndEnter('symlinksToPoly', comment=" # Updatres Symlinks to Poly")

