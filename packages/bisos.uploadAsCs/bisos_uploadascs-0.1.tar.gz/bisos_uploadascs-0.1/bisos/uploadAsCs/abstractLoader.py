# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: A =CS-Lib= for Managing RO (Remote Operation) Control File Parameters as a ClsFp
#+end_org """

####+BEGIN: b:py3:cs:file/dblockControls :classification "cs-u"
""" #+begin_org
* [[elisp:(org-cycle)][| /Control Parameters Of This File/ |]] :: dblk ctrls classifications=cs-u
#+BEGIN_SRC emacs-lisp
(setq-local b:dblockControls t) ; (setq-local b:dblockControls nil)
(put 'b:dblockControls 'py3:cs:Classification "cs-u") ; one of cs-mu, cs-u, cs-lib, bpf-lib, pyLibPure
#+END_SRC
#+RESULTS:
: cs-u
#+end_org """
####+END:

####+BEGIN: b:prog:file/proclamations :outLevel 1
""" #+begin_org
* *[[elisp:(org-cycle)][| Proclamations |]]* :: Libre-Halaal Software --- Part Of BISOS ---  Poly-COMEEGA Format.
** This is Libre-Halaal Software. © Neda Communications, Inc. Subject to AGPL.
** It is part of BISOS (ByStar Internet Services OS)
** Best read and edited  with Blee in Poly-COMEEGA (Polymode Colaborative Org-Mode Enhance Emacs Generalized Authorship)
#+end_org """
####+END:

####+BEGIN: b:prog:file/particulars :authors ("./inserts/authors-mb.org")
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars |]]* :: Authors, version
** This File: /bisos/git/auth/bxRepos/bisos-pip/debian/py3/bisos/debian/configFile.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:python:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
from enum import verify
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['configFile'], }
csInfo['version'] = '202305114855'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'configFile-Panel.org'
csInfo['groupingType'] = 'IcmGroupingType-pkged'
csInfo['cmndParts'] = 'IcmCmndParts[common] IcmCmndParts[param]'
####+END:

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/PyFwrk/bisos-pip/bisos.cs/_nodeBase_/fullUsagePanel-en.org][PyFwrk bisos.b.cs Panel For RO]] ||
Module description comes here.
** Relevant Panels:
** Status: In use with BISOS
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO complete fileName in particulars.
#+end_org """

####+BEGIN: b:prog:file/orgTopControls :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Controls |]] :: [[elisp:(delete-other-windows)][(1)]] | [[elisp:(show-all)][Show-All]]  [[elisp:(org-shifttab)][Overview]]  [[elisp:(progn (org-shifttab) (org-content))][Content]] | [[file:Panel.org][Panel]] | [[elisp:(blee:ppmm:org-mode-toggle)][Nat]] | [[elisp:(bx:org:run-me)][Run]] | [[elisp:(bx:org:run-me-eml)][RunEml]] | [[elisp:(progn (save-buffer) (kill-buffer))][S&Q]]  [[elisp:(save-buffer)][Save]]  [[elisp:(kill-buffer)][Quit]] [[elisp:(org-cycle)][| ]]
** /Version Control/ ::  [[elisp:(call-interactively (quote cvs-update))][cvs-update]]  [[elisp:(vc-update)][vc-update]] | [[elisp:(bx:org:agenda:this-file-otherWin)][Agenda-List]]  [[elisp:(bx:org:todo:this-file-otherWin)][ToDo-List]]

#+end_org """
####+END:

####+BEGIN: b:python:file/workbench :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Workbench |]] :: [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pyclbr %s" (bx:buf-fname))))][pyclbr]] || [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pydoc ./%s" (bx:buf-fname))))][pydoc]] || [[elisp:(python-check (format "/bisos/pipx/bin/pyflakes %s" (bx:buf-fname)))][pyflakes]] | [[elisp:(python-check (format "/bisos/pipx/bin/pychecker %s" (bx:buf-fname))))][pychecker (executes)]] | [[elisp:(python-check (format "/bisos/pipx/bin/pycodestyle %s" (bx:buf-fname))))][pycodestyle]] | [[elisp:(python-check (format "/bisos/pipx/bin/flake8 %s" (bx:buf-fname))))][flake8]] | [[elisp:(python-check (format "/bisos/pipx/bin/pylint %s" (bx:buf-fname))))][pylint]]  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:orgItem/basic :type "=PyImports= " :title "*Py Library IMPORTS*" :comment "-- with classification based framework/imports"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =PyImports=  [[elisp:(outline-show-subtree+toggle)][||]] *Py Library IMPORTS* -- with classification based framework/imports  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:framework/imports :basedOn "classification"
""" #+begin_org
** Imports Based On Classification=cs-u
#+end_org """
from bisos import b
from bisos.b import cs
from bisos.b import b_io
from bisos.common import csParam

import collections
####+END:

import pathlib
import types

import os
import abc

import os
# import subprocess

import logging

log = logging.getLogger(__name__)

import sys
import argparse


####+BEGIN: bx:cs:py3:section :title "Configuration File Manager"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  /Section/    [[elisp:(outline-show-subtree+toggle)][||]] *Configuration File Manager*  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:class/decl :className "PyModuleImporter" :superClass "object" :comment "" :classType "basic"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Cls-basic  [[elisp:(outline-show-subtree+toggle)][||]] /PyModuleImporter/  superClass=object =A Singlton for mapping type to DigestLoadedAs=  [[elisp:(org-cycle)][| ]]
#+end_org """
class PyModuleImporter(object):
####+END:
    """
** Abstraction of a Module Importer for 'uploadedModule'
"""

    def __init__(
            self,
            filePath: str= "",
    ):
        self.filePath = filePath

    def importModule(self,) ->  types.ModuleType | None:
        "Import File As uploadedModule"

        module = b.importFile.importFileAs("uploadedModule", self.filePath)
        self.module = module

        return module




####+BEGIN: b:py3:class/decl :className "AbstractLoader" :superClass "abc.ABC" :comment "Representing a module type" :classType "abs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Cls-abs    [[elisp:(outline-show-subtree+toggle)][||]] /AbstractLoader/  superClass=abc.ABC =Representing a module type=  [[elisp:(org-cycle)][| ]]
#+end_org """
class AbstractLoader(abc.ABC):
####+END:
    """
** An Abstract Loader to be made concrete.
"""

####+BEGIN: b:py3:cs:method/typing :methodName "__init__" :deco "default"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-     [[elisp:(outline-show-subtree+toggle)][||]] /__init__/  deco=default  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def __init__(
####+END:
            self,
            loaderType: typing.AnyStr = "",
    ):
        self.loaderType = loaderType

####+BEGIN: b:py3:cs:method/typing :methodName "callEntryPoint" :deco "abc.abstractmethod"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-     [[elisp:(outline-show-subtree+toggle)][||]] /callEntryPoint/  deco=abc.abstractmethod  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @abc.abstractmethod
    def callEntryPoint(
####+END:
            self,
            module: types.ModuleType,
            *args: typing.Any,
            **kwargs: typing.Any,
    ) -> None:
        """ #+begin_org
*** [[elisp:(org-cycle)][| DocStr| ]]
        #+end_org """
        return

####+BEGIN: b:py3:cs:method/typing :methodName "translateParams" :deco "abc.abstractmethod"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-     [[elisp:(outline-show-subtree+toggle)][||]] /translateParams/  deco=abc.abstractmethod  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @abc.abstractmethod
    def translateParams(
####+END:
            self,
            module: types.ModuleType,
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """ #+begin_org
*** [[elisp:(org-cycle)][| DocStr| ]]
        #+end_org """

        return None

####+BEGIN: b:py3:cs:method/typing :methodName "verify" :deco "abc.abstractmethod"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-     [[elisp:(outline-show-subtree+toggle)][||]] /verify/  deco=abc.abstractmethod  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @abc.abstractmethod
    def verify(
####+END:
            self,
            module: types.ModuleType,
    ) -> bool:
        """ #+begin_org
*** [[elisp:(org-cycle)][| DocStr| ]]
        #+end_org """

        return False

####+BEGIN: b:py3:cs:method/typing :methodName "applicableParams" :deco ""
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-     [[elisp:(outline-show-subtree+toggle)][||]] /applicableParams/   [[elisp:(org-cycle)][| ]]
    #+end_org """
    def applicableParams(
####+END:
            self,
            module: types.ModuleType,
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """ #+begin_org
*** [[elisp:(org-cycle)][| DocStr| ]] module is an imported python module that must have a function called genericCliParams.

        The return value is then the KWARGS to be passed to callEntryPoint as **kwargs.
        Where the parCliName is the keyword and the value is taken from command line arguments.
        #+end_org """

        genericParams = self.translateParams(module)

        inArgv = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)

        # Add one --long option per generic param
        for eachGenericParam in genericParams:
            if not eachGenericParam or not isinstance(eachGenericParam, (list, tuple)):
                continue
            parCliName = eachGenericParam[0]
            parDescription = eachGenericParam[2] if len(eachGenericParam) > 2 else ''
            longOpt = f"--{parCliName}"
            parser.add_argument(longOpt, dest=parCliName, nargs='?', help=parDescription)

        ns, _ = parser.parse_known_args(inArgv)

        # Only include kwargs for options explicitly present on the command line
        kwargs: dict[str, typing.Any] = {}
        for eachGenericParam in genericParams:
            if not eachGenericParam or not isinstance(eachGenericParam, (list, tuple)):
                continue
            parCliName = eachGenericParam[0]
            longOpt = f"--{parCliName}"
            if any(a == longOpt or a.startswith(longOpt + "=") for a in inArgv):
                val = getattr(ns, parCliName, None)
                # treat presence of boolean-like flags without value as True
                parDataType = eachGenericParam[3] if len(eachGenericParam) > 3 else None
                if val is None and isinstance(parDataType, str) and 'bool' in parDataType.lower():
                    val = True
                kwargs[parCliName] = val

        return kwargs




####+BEGIN: b:py3:class/decl :className "LoaderTypes" :superClass "object" :comment "A Singlton for mapping type to DigestLoadedAs" :classType "basic"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Cls-basic  [[elisp:(outline-show-subtree+toggle)][||]] /LoaderTypes/  superClass=object =A Singlton for mapping type to DigestLoadedAs=  [[elisp:(org-cycle)][| ]]
#+end_org """
class LoaderTypes(object):
####+END:
    """
** Abstraction of list of types of loaders
"""
    _instance = None

    # Singleton using New
    def __new__(cls):
        if cls._instance is None:
            # print('Creating the object')
            cls._instance = super(__class__, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    def __init__(
            self,
    ):
        self.defaultLoader = None

    def add(self, name: str, loader: AbstractLoader) ->  AbstractLoader:
        "Add"
        self.defaultLoader = loader
        return self.defaultLoader

    def get(self, name: str) -> AbstractLoader | None:
        ""
        return self.defaultLoader

    def default(self,) -> AbstractLoader | None:
        ""
        return self.defaultLoader


loaderTypes = LoaderTypes()



####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
