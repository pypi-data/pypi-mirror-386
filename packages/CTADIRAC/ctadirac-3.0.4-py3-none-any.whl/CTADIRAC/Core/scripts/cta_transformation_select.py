#!/usr/bin/env python

"""
  Get transformations with a given Status
"""

__RCSID__ = "$Id$"

import DIRAC
from DIRAC.Core.Base.Script import Script
from DIRAC.TransformationSystem.Client.TransformationClient import TransformationClient


@Script()
def main():
    Script.registerSwitch("", "Status=", "status")
    Script.parseCommandLine()

    status = None

    for switch in Script.getUnprocessedSwitches():
        if switch[0] == "Status":
            status = switch[1].capitalize()

    tc = TransformationClient()
    res = tc.getTransformationWithStatus(status)

    if not res["OK"]:
        DIRAC.gLogger.error(res["Message"])
        DIRAC.exit(-1)

    transIDs = res["Value"]

    if transIDs:
        DIRAC.gLogger.notice(
            f"Found {len(transIDs)} transformations with status {status}"
        )
    else:
        DIRAC.gLogger.notice("No transformations selected with status", status)
        DIRAC.exit(0)

    strTransIDs = []
    for transID in transIDs:
        strTransIDs.append(str(transID))

    DIRAC.gLogger.notice(f"{','.join(strTransIDs)}")

    DIRAC.exit(0)


if __name__ == "__main__":
    main()
