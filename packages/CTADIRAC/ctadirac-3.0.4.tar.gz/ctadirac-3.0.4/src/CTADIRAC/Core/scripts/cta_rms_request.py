#!/bin/env python
"""
Show request given its ID, a jobID or a transformation and a task
Extension of dirac-rms-request with additional options:
--TaskStatus: selection of requests associated to a Transformation based on TaskStatus
--Stat: to print only summary informations
"""
__RCSID__ = "$Id$"

import datetime
import os

import DIRAC
from DIRAC import gLogger
from DIRAC.Core.Base.Script import Script

Script.registerSwitch("", "Job=", "   JobID[,jobID2,...]")
Script.registerSwitch("", "Transformation=", "   transformation ID")
Script.registerSwitch(
    "", "Tasks=", "      Associated to --Transformation, list of taskIDs"
)
Script.registerSwitch("", "TaskStatus=", "      Associated to --Transformation")
Script.registerSwitch("", "Stat", "   Only print summary informations")
Script.registerSwitch("", "Verbose", "   Print more information")
Script.registerSwitch("", "Terse", "   Only print request status")
Script.registerSwitch("", "Full", "   Print full request content")
Script.registerSwitch("", "Status=", "   Select all requests in a given status")
Script.registerSwitch(
    "",
    "Since=",
    "      Associated to --Status, start date yyyy-mm-dd or nb of days (default= -one day",
)
Script.registerSwitch(
    "", "Until=", "      Associated to --Status, end date (default= now"
)
Script.registerSwitch(
    "", "Maximum=", "      Associated to --Status, max number of requests "
)
Script.registerSwitch("", "Reset", "   Reset Failed files to Waiting if any")
Script.registerSwitch("", "Force", "   Force reset even if not Failed")
Script.registerSwitch(
    "",
    "All",
    "      (if --Status Failed) all requests, otherwise exclude irrecoverable failures",
)
Script.registerSwitch("", "FixJob", "   Set job Done if the request is Done")
Script.registerSwitch("", "Cancel", "   Cancel the request")
Script.registerSwitch("", "ListJobs", " List the corresponding jobs")
Script.registerSwitch(
    "", "TargetSE=", " Select request only if that SE is in the targetSEs"
)
Script.setUsageMessage(
    "\n".join(
        [
            __doc__,
            "Usage:",
            f" {Script.scriptName} [option|cfgfile] [request[,request1,...]|<file>",
            "Arguments:",
            " request: a request ID or a unique request name",
            " <file>: a file containing a list of requests (Comma-separated on each line)",
        ]
    )
)

Script.parseCommandLine()


def convertDate(date):
    try:
        value = datetime.datetime.strptime(date, "%Y-%m-%d")
        return value
    except Exception:
        pass
    try:
        value = datetime.datetime.utcnow() - datetime.timedelta(
            hours=int(24 * float(date))
        )
    except Exception:
        gLogger.fatal("Invalid date", date)
        value = None
    return value


@Script()
def main():
    jobs = []
    requestID = 0
    transID = None
    taskIDs = None
    tasks = None
    taskStatus = None
    requests = []
    full = False
    verbose = False
    stat = False
    status = None
    until = None
    since = None
    terse = False
    allR = False
    reset = False
    fixJob = False
    maxRequests = 999999999999
    cancel = False
    listJobs = False
    force = False
    targetSE = set()
    for switch in Script.getUnprocessedSwitches():
        if switch[0] == "Job":
            try:
                jobs = []
                for arg in switch[1].split(","):
                    if os.path.exists(arg):
                        lines = open(arg).readlines()
                        jobs += [
                            int(job.strip())
                            for line in lines
                            for job in line.split(",")
                        ]
                        gLogger.notice(f"Found {len(jobs)} jobs in file {arg}")
                    else:
                        jobs.append(int(arg))
            except TypeError:
                gLogger.fatal("Invalid jobID")
        elif switch[0] == "Transformation":
            try:
                transID = int(switch[1])
            except Exception:
                gLogger.fatal("Invalid transID", switch[1])
        elif switch[0] == "Tasks":
            try:
                taskIDs = [int(task) for task in switch[1].split(",")]
            except Exception:
                gLogger.fatal("Invalid tasks", switch[1])
        elif switch[0] == "TaskStatus":
            taskStatus = switch[1].capitalize()
        elif switch[0] == "Stat":
            stat = True
        elif switch[0] == "Full":
            full = True
        elif switch[0] == "Verbose":
            verbose = True
        elif switch[0] == "Terse":
            terse = True
        elif switch[0] == "All":
            allR = True
        elif switch[0] == "Reset":
            reset = True
        elif switch[0] == "Force":
            force = True
        elif switch[0] == "Status":
            status = switch[1].capitalize()
        elif switch[0] == "Since":
            since = convertDate(switch[1])
        elif switch[0] == "Until":
            until = convertDate(switch[1])
        elif switch[0] == "FixJob":
            fixJob = True
        elif switch[0] == "Cancel":
            cancel = True
        elif switch[0] == "ListJobs":
            listJobs = True
        elif switch[0] == "Maximum":
            try:
                maxRequests = int(switch[1])
            except Exception:
                pass
        elif switch[0] == "TargetSE":
            targetSE = set(switch[1].split(","))

    if reset and not force:
        status = "Failed"
    if fixJob:
        status = "Done"
    if terse:
        verbose = True
    if status:
        if not until:
            until = datetime.datetime.utcnow()
        if not since:
            since = until - datetime.timedelta(hours=24)
    from DIRAC.RequestManagementSystem.Client.ReqClient import ReqClient
    from DIRAC.RequestManagementSystem.Client.ReqClient import (
        printRequest,
        recoverableRequest,
    )
    from DIRAC.TransformationSystem.Client.TransformationClient import (
        TransformationClient,
    )

    reqClient = ReqClient()
    transClient = TransformationClient()

    if transID:
        if not taskIDs:
            condDict = {"TransformationID": transID}
            if taskStatus:
                condDict.update({"ExternalStatus": taskStatus})
            res = transClient.getTransformationTasks(condDict)
            for record in res["Value"]:
                task = record["TaskID"]
                requestID = record["ExternalID"]
                requests.append(requestID)
            if not requests:
                gLogger.error(f"No request found for transformation {transID}")
                DIRAC.exit(0)
        else:
            requests = ["%08d_%08d" % (transID, task) for task in taskIDs]
        allR = True

    elif not jobs:
        requests = []
        # Get full list of arguments, with and without comma
        for arg in [
            x.strip() for arg in Script.getPositionalArgs() for x in arg.split(",")
        ]:
            if os.path.exists(arg):
                lines = open(arg).readlines()
                requests += [
                    reqID.strip() for line in lines for reqID in line.split(",")
                ]
                gLogger.notice(f"Found {len(requests)} requests in file")
            else:
                requests.append(arg)
            allR = True
    else:
        res = reqClient.getRequestIDsForJobs(jobs)
        if not res["OK"]:
            gLogger.fatal("Error getting request for jobs", res["Message"])
            DIRAC.exit(2)
        if res["Value"]["Failed"]:
            gLogger.error(
                "No request found for jobs %s"
                % ",".join(sorted(str(job) for job in res["Value"]["Failed"]))
            )
        requests = sorted(res["Value"]["Successful"].values())
        if requests:
            allR = True
        else:
            DIRAC.exit(0)

    if status and not requests:
        allR = allR or status != "Failed"
        res = reqClient.getRequestIDsList(
            [status], limit=maxRequests, since=since, until=until
        )

        if not res["OK"]:
            gLogger.error("Error getting requests:", res["Message"])
            DIRAC.exit(2)
        requests = [
            reqID
            for reqID, _st, updTime in res["Value"]
            if updTime > since and updTime <= until and reqID
        ]
        gLogger.notice(
            f"Obtained {len(requests)} requests {status} between {since} and {until}"
        )
    if not requests:
        gLogger.notice("No request selected....")
        Script.showHelp(exitCode=2)
    okRequests = []
    warningPrinted = False
    jobIDList = []
    for reqID in requests:
        # We allow reqID to be the requestName if it is unique
        try:
            requestID = int(reqID)
        except ValueError:
            requestID = reqClient.getRequestIDForName(reqID)
            if not requestID["OK"]:
                gLogger.notice(requestID["Message"])
                continue
            requestID = requestID["Value"]

        request = reqClient.peekRequest(requestID)
        if not request["OK"]:
            gLogger.error(request["Message"])
            DIRAC.exit(-1)

        request = request["Value"]
        if not request:
            gLogger.error(f"no such request {requestID}")
            continue
        # If no operation as the targetSE, skip
        if targetSE:
            found = False
            for op in request:
                if op.TargetSE and targetSE.intersection(op.TargetSE.split(",")):
                    found = True
                    break
            if not found:
                continue
        # keep a list of jobIDs if requested
        if request.JobID and listJobs:
            jobIDList.append(request.JobID)

        if status and request.Status != status:
            gLogger.notice(
                "Request %s is not in requested status %s%s"
                % (reqID, status, " (cannot be reset)" if reset else "")
            )
            continue

        if fixJob and request.Status == "Done" and request.JobID:
            # The request is for a job and is Done, verify that the job is in the proper status
            result = reqClient.finalizeRequest(
                request.RequestID, request.JobID, useCertificates=False
            )
            if not result["OK"]:
                gLogger.error("Error finalizing job", result["Message"])
            else:
                gLogger.notice(
                    "Job %d updated to %s" % (request.JobID, result["Value"])
                )
            continue

        if cancel:
            if request.Status not in ("Done", "Failed"):
                ret = reqClient.cancelRequest(requestID)
                if not ret["OK"]:
                    gLogger.error(f"Error canceling request {reqID}", ret["Message"])
                else:
                    gLogger.notice(f"Request {reqID} cancelled")
            else:
                gLogger.notice(
                    f"Request {reqID} is in status {request.Status}, not cancelled"
                )

        elif allR or recoverableRequest(request):
            okRequests.append(str(requestID))
            if reset:
                gLogger.notice(f"============ Request {requestID} =============")
                ret = reqClient.resetFailedRequest(requestID, allR=allR)
                if not ret["OK"]:
                    gLogger.error(
                        f"Error resetting request {requestID}", ret["Message"]
                    )
            else:
                if len(requests) > 1 and not stat:
                    gLogger.notice("\n===================================")
                dbStatus = reqClient.getRequestStatus(requestID).get("Value", "Unknown")
                if not stat:
                    printRequest(
                        request,
                        status=dbStatus,
                        full=full,
                        verbose=verbose,
                        terse=terse,
                    )

    if stat:
        gLogger.notice(
            "Found %d requests with RequestID: %s"
            % (len(requests), ",".join(requestID for requestID in requests))
        )

    if listJobs:
        gLogger.notice(
            f"List of {len(jobIDList)} jobs:\n",
            ",".join(str(jobID) for jobID in jobIDList),
        )

    if status and okRequests:
        from DIRAC.Core.Utilities.List import breakListIntoChunks

        gLogger.notice(f"\nList of {len(okRequests)} selected requests:")
        for reqs in breakListIntoChunks(okRequests, 100):
            gLogger.notice(",".join(reqs))


if __name__ == "__main__":
    main()
