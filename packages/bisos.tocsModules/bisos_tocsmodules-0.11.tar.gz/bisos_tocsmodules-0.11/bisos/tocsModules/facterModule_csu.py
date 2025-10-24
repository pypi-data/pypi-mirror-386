# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: A =CS-Unit= as equivalent of facter in py and remotely with rpyc.
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
** This File: /bisos/git/bxRepos/bisos-pip/facter/py3/bisos/facter/facter_csu.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

####+BEGIN: b:py3:file/particulars-csInfo :status "inUse"
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars-csInfo |]]*
#+end_org """
import typing
csInfo: typing.Dict[str, typing.Any] = { 'moduleName': ['facter_csu'], }
csInfo['version'] = '202403270908'
csInfo['status']  = 'inUse'
csInfo['panel'] = 'facter_csu-Panel.org'
csInfo['groupingType'] = 'IcmGroupingType-pkged'
csInfo['cmndParts'] = 'IcmCmndParts[common] IcmCmndParts[param]'
####+END:

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/COMEEGA/_nodeBase_/fullUsagePanel-en.org][BISOS COMEEGA Panel]]
This a =Cs-Unit= for running the equivalent of facter in py and remotely with rpyc.
With BISOS, it is used in CMDB remotely.

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

####+BEGIN: b:py3:file/workbench :outLevel 1
""" #+begin_org
* [[elisp:(org-cycle)][| Workbench |]] :: [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pyclbr %s" (bx:buf-fname))))][pyclbr]] || [[elisp:(python-check (format "/bisos/venv/py3/bisos3/bin/python -m pydoc ./%s" (bx:buf-fname))))][pydoc]] || [[elisp:(python-check (format "/bisos/pipx/bin/pyflakes %s" (bx:buf-fname)))][pyflakes]] | [[elisp:(python-check (format "/bisos/pipx/bin/pychecker %s" (bx:buf-fname))))][pychecker (executes)]] | [[elisp:(python-check (format "/bisos/pipx/bin/pycodestyle %s" (bx:buf-fname))))][pycodestyle]] | [[elisp:(python-check (format "/bisos/pipx/bin/flake8 %s" (bx:buf-fname))))][flake8]] | [[elisp:(python-check (format "/bisos/pipx/bin/pylint %s" (bx:buf-fname))))][pylint]]  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:orgItem/basic :type "=PyImports= "  :title "*Py Library IMPORTS*" :comment "-- Framework and External Packages Imports"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =PyImports=  [[elisp:(outline-show-subtree+toggle)][||]] *Py Library IMPORTS* -- Framework and External Packages Imports  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

# import os
import collections
# import pathlib
# import invoke

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

from bisos.loadAsCs import loadAsCs_csu
from bisos.loadAsCs import abstractLoader

from bisos.b import cmndsSeed

####+BEGIN: b:py3:cs:orgItem/basic :type "=Executes=  "  :title "CSU-Lib Executions" :comment "-- cs.invOutcomeReportControl"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  =Executes=   [[elisp:(outline-show-subtree+toggle)][||]] CSU-Lib Executions -- cs.invOutcomeReportControl  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

# g_svcName = "svcFacter"
# g_rosmu = cs.G.icmMyName()

# cs.invOutcomeReportControl(cmnd=True, ro=True)

####+BEGIN: b:py3:cs:orgItem/section :title "Common Parameters Specification" :comment "based on cs.param.CmndParamDict -- As expected from CSU-s"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  /Section/    [[elisp:(outline-show-subtree+toggle)][||]] *Common Parameters Specification* based on cs.param.CmndParamDict -- As expected from CSU-s  [[elisp:(org-cycle)][| ]]
#+end_org """
####+END:

####+BEGIN: b:py3:cs:func/typing :funcName "commonParamsSpecify" :comment "~CSU Specification~" :funcType "ParSpc" :deco ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  F-T-ParSpc [[elisp:(outline-show-subtree+toggle)][||]] /commonParamsSpecify/  ~CSU Specification~  [[elisp:(org-cycle)][| ]]
#+end_org """
def commonParamsSpecify(
####+END:
        csParams: cs.param.CmndParamDict,
) -> None:
    csParams.parDictAdd(
        parName='targetsFile',
        parDescription=".",
        parDataType=None,
        parDefault=None,
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--targetsFile',
    )
    csParams.parDictAdd(
        parName='targetsNu',
        parDescription=".",
        parDataType=None,
        parDefault=None,
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--targetsNu',
    )
    csParams.parDictAdd(
        parName='cluster',
        parDescription=".",
        parDataType=None,
        parDefault=None,
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--cluster',
    )
    csParams.parDictAdd(
        parName='clustersList',
        parDescription=".",
        parDataType=None,
        parDefault=None,
        parChoices=[],
        argparseShortOpt=None,
        argparseLongOpt='--clustersList',
    )
    csParams.parDictAdd(
        parName='runDisposition',
        parDescription=".",
        parDataType=None,
        parDefault="parallel",
        parChoices=["parallel", "sequential"],
        argparseShortOpt=None,
        argparseLongOpt='--runDisposition',
    )


####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "Direct Command Services" :anchor ""  :extraInfo "Examples and CSs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*     [[elisp:(outline-show-subtree+toggle)][| _Direct Command Services_: |]]  Examples and CSs  [[elisp:(org-shifttab)][<)]] E|
#+end_org """
####+END:

####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "examples_csu" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv "pyKwArgs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<examples_csu>>  =verify= ro=cli pyInv=pyKwArgs   [[elisp:(org-cycle)][| ]]
#+end_org """
class examples_csu(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             pyKwArgs: typing.Any=None,   # pyInv Argument
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
*** Run Results
#+begin_src sh :results output :session shared
facterModule.cs -i examples 
  #+end_src
#+RESULTS:
#+begin_example
| emlOutFilter.sh -i iimToEmlStdout  | emlVisit
facterModule.cs -i visit
emlVisit -v -n showRun -i gotoPanel /bisos/venv/py3/devbin/facterModule.cs
=======  /Upload Python Module/  ==========
facterModule.cs --upload="./facterModuleSample.py"  -i importModule           # Digest the Module
facterModule.cs  -i loaderTypesAdd generic          # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i verify           # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i translateParams           # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i run arg1 secondArg          # Run the module with args+stdin
#######  =Related Commands=  ##########
NOTYET.cs
#######  = Facter Module  Commands=  ##########
facterModule.cs --upload="/bisos/git/auth/bxRepos/bisos-pip/tocsModules/py3/bisos/tocsModules/facterModuleSample.py"  -i targetRun localhost
echo 127.0.0.1 | facterModule.cs --upload="/bisos/git/auth/bxRepos/bisos-pip/tocsModules/py3/bisos/tocsModules/facterModuleSample.py"  -i targetRun localhost
#+end_example

        #+end_org """)

        od = collections.OrderedDict
        cmnd = cs.examples.cmndEnter
        literal = cs.examples.execInsert

        #  -v 1 --callTrackings monitor+ --callTrackings invoke+
        pars_debug_full = od([('verbosity', "1"), ('callTrackings', "monitor+"), ('callTrackings', "invoke+"), ])

        # cmnd('targetRun', csName=csName, pars=(pars_debug_full |pars_upload), comment=f"""# DEBUG Small Batch""",)


        uploadPath = "./genericPyModule.py"
        if pyKwArgs:
            uploadPath =  pyKwArgs['upload']
        else:
            return failed(cmndOutcome)

        # Use an absolute path for upload to avoid relative-path surprises
        uploadPathAbs = str(pathlib.Path(uploadPath).expanduser().resolve())
        uploadPars = od([('upload', uploadPathAbs)])

        oneBaseDir = "/bisos/git/bxRepos/bxObjects/bro_tocsModules/facter/samples/"
        oneTargetFile = oneBaseDir + "targets/examples.tgt"

        targetPathAbs = str(pathlib.Path(oneTargetFile).expanduser().resolve())
        targetFilePars = od([('upload', uploadPathAbs),('targetFile', targetPathAbs) ])

        cs.examples.menuChapter('= Facter Module  Commands=')

        cmnd('targetRun', pars=uploadPars , args="""localhost""")

        cmnd('targetRun', pars=uploadPars , args="""localhost""",
             wrapper=f"echo 127.0.0.1 |",
             )

        cmnd('targetRun', pars=targetFilePars , args="""localhost""",
             wrapper=f"echo 127.0.0.1 |",
             )

        # literal("facter networking.interfaces.lo.bindings[0].address  # Fails, you can't do that")

        return(cmndOutcome)



####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "examples_seed" :comment "" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv "pyKwArgs"
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<examples_seed>>  =verify= ro=cli pyInv=pyKwArgs   [[elisp:(org-cycle)][| ]]
#+end_org """
class examples_seed(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             pyKwArgs: typing.Any=None,   # pyInv Argument
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Basic example command.
        #+end_org """)

        self.captureRunStr(""" #+begin_org
*** Run Results
#+begin_src sh :results output :session shared
facterModule.cs -i examples
  #+end_src
#+RESULTS:
#+begin_example
| emlOutFilter.sh -i iimToEmlStdout  | emlVisit
facterModule.cs -i visit
emlVisit -v -n showRun -i gotoPanel /bisos/venv/py3/devbin/facterModule.cs
=======  /Upload Python Module/  ==========
facterModule.cs --upload="./facterModuleSample.py"  -i importModule           # Digest the Module
facterModule.cs  -i loaderTypesAdd generic          # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i verify           # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i translateParams           # Digest the Module
facterModule.cs --upload="./facterModuleSample.py"  -i run arg1 secondArg          # Run the module with args+stdin
#######  =Related Commands=  ##########
NOTYET.cs
#######  = Facter Module  Commands=  ##########
facterModule.cs --upload="/bisos/git/auth/bxRepos/bisos-pip/tocsModules/py3/bisos/tocsModules/facterModuleSample.py"  -i targetRun localhost
echo 127.0.0.1 | facterModule.cs --upload="/bisos/git/auth/bxRepos/bisos-pip/tocsModules/py3/bisos/tocsModules/facterModuleSample.py"  -i targetRun localhost
#+end_example

        #+end_org """)

        od = collections.OrderedDict
        cmnd = cs.examples.cmndEnter
        literal = cs.examples.execInsert

        uploadPath = "./genericPyModule.py"

        if pyKwArgs:
            uploadPath =  pyKwArgs['upload']
        else:
            return failed(cmndOutcome)

        kwSeedInfo = cmndsSeed.cmndsSeedInfo.kwSeedInfo
        print(f"4444 kwSeedInfo={kwSeedInfo}")
        if kwSeedInfo:
            if kwSeedInfo.get('uploadPath'):
                uploadPath = kwSeedInfo['uploadPath']
        
        # Use an absolute path for upload to avoid relative-path surprises
        uploadPathAbs = str(pathlib.Path(uploadPath).expanduser().resolve())
        uploadPars = od([('upload', uploadPathAbs)])

        targetPathAbs = str(pathlib.Path("~/targets/examples.tgt").expanduser().resolve())
        targetFilePars = od([('upload', uploadPathAbs),('targetFile', targetPathAbs) ])

        cs.examples.menuChapter('= Facter Module  Commands=')

        cmnd('targetRun', pars=uploadPars , args="""localhost""")

        cmnd('targetRun', pars=uploadPars , args="""localhost""",
             wrapper=f"echo 127.0.0.1 |",
             )

        cmnd('targetRun', pars=targetFilePars , args="""localhost""",
             wrapper=f"echo 127.0.0.1 |",
             )

        # literal("facter networking.interfaces.lo.bindings[0].address  # Fails, you can't do that")

        return(cmndOutcome)


####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "targetRun" :comment "" :extent "verify" :ro "cli" :parsMand "upload" :parsOpt "targetFile targetsNu" :argsMin 0 :argsMax 9999 :pyInv ""
""" #+begin_org
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] <<targetRun>>  =verify= parsMand=upload parsOpt=targetFile targetsNu argsMax=9999 ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class targetRun(cs.Cmnd):
    cmndParamsMandatory = [ 'upload', ]
    cmndParamsOptional = [ 'targetFile', 'targetsNu', ]
    cmndArgsLen = {'Min': 0, 'Max': 9999,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
             upload: typing.Optional[str]=None,  # Cs Mandatory Param
             targetFile: typing.Optional[str]=None,  # Cs Optional Param
             targetsNu: typing.Optional[str]=None,  # Cs Optional Param
             argsList: typing.Optional[list[str]]=None,  # CsArgs
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {'upload': upload, 'targetFile': targetFile, 'targetsNu': targetsNu, }
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, argsList).isProblematic():
            return failed(cmndOutcome)
        cmndArgsSpecDict = self.cmndArgsSpec()
        upload = csParam.mappedValue('upload', upload)
        targetFile = csParam.mappedValue('targetFile', targetFile)
        targetsNu = csParam.mappedValue('targetsNu', targetsNu)
####+END:
        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]
        #+end_org """)

        self.captureRunStr(""" #+begin_org
*** Run Results
#+begin_src sh :results output :session shared
echo 127.0.0.1 | facterModule.cs --upload=./facterModuleSample.py  -i targetRun localhost
  #+end_src
#+RESULTS:
: target: localhost
: target: 127.0.0.1

        #+end_org """)

        cmndArgs = self.cmndArgsGet("0&9999", cmndArgsSpecDict, argsList)

        targetsList = []

        if targetFile:
            try:
                with open(targetFile, 'r') as f:
                    fileArgs = f.read().splitlines()
                for each in fileArgs:
                    targetsList.append(each)
            except Exception as e:
                # cmndOutcome.setProblem(f"Cannot open targetFile '{targetFile}': {e}")
                return failed(cmndOutcome)

        def processArgsAndStdin(cmndArgs, process):
            for each in cmndArgs:
                process(each)
            stdinArgs = b_io.stdin.readAsList()
            for each in stdinArgs:
                process(each)

        def process(target):

            targetsList.append(target)
            if rtInv.outs:
                # print(f"target: {target}")
                pass

        processArgsAndStdin(cmndArgs, process)

        # If no targets were collected, ensure targetsNu > 0 else fail
        if not targetsList:
            try:
                tn = int(targetsNu) if targetsNu is not None else 0
            except Exception:
                tn = 0
            if tn <= 0:
                return failed(cmndOutcome)

        print(f"{targetsList}")

        if not (module := loadAsCs_csu.importModule(cmndOutcome=cmndOutcome).pyCmnd(
                upload=upload,
        ).results): return(b_io.eh.badOutcome(cmndOutcome))

        loaderType = abstractLoader.loaderTypes.default()

        kwArgs = loaderType.applicableParams(module,)

        result = loaderType.callEntryPoint(module, targetsList, **kwArgs)

        return cmndOutcome.set(
            opError=b.OpError.Success,
            opResults=result,
        )


####+BEGIN: b:py3:cs:method/args :methodName "cmndArgsSpec" :methodType "anyOrNone" :retType "bool" :deco "default" :argsList "self"
    """ #+begin_org
**  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  Mtd-T-anyOrNone [[elisp:(outline-show-subtree+toggle)][||]] /cmndArgsSpec/ deco=default  deco=default  [[elisp:(org-cycle)][| ]]
    #+end_org """
    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmndArgsSpec(self, ):
####+END:
        """
***** Cmnd Args Specification
"""
        cmndArgsSpecDict = cs.CmndArgsSpecDict()

        cmndArgsSpecDict.argsDictAdd(
            argPosition="0&9999",
            argName="cmndArgs",
            argDefault='',
            argChoices=[],
            argDescription="Targets"
        )

        return cmndArgsSpecDict



####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
