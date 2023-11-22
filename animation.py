import math

import cv2
import sys, logging, json, time, os

def calculatemoveendframe(_object):
    distance = math.sqrt( (_object["location"][0] - _object["movetolocation"][0]) * (_object["location"][0] - _object["movetolocation"][0]) +
                          (_object["location"][1] - _object["movetolocation"][1]) * (_object["location"][1] - _object["movetolocation"][1]) )
    step = [(_object["movetolocation"][0] - _object["location"][0])/ _object["movespeedinframe"],
                (_object["movetolocation"][1] - _object["location"][1]) / _object["movespeedinframe"]
                ]
    return 1


def initialize(job):
    jobid = str(time.time())
    job["tempfolder"] = os.path.join("sample", "output", jobid)
    job["resultfile"] = os.path.join("sample", "output", f"{jobid}.mp4")
    job["objects"] = {}
    for event in job["events"]:
        if event["action"] == "add":
            _object = {"starttime": event["time"],
                       "startframe": int(job["fps"] *  event["time"]),
                       "location": event["location"]}
            job["objects"][event["objectid"]] = _object

        if event["action"] == "remove":
            job["objects"][event["objectid"]]["endtime"] = event["time"]
            job["objects"][event["objectid"]]["endframe"] = int(job["fps"] *  event["time"])

        if event["action"] == "move":
            job["objects"][event["objectid"]]["movestarttime"] = event["time"]
            job["objects"][event["objectid"]]["movestartframe"] = int(job["fps"] *  event["time"])
            job["objects"][event["objectid"]]["movetolocation"] = event["moveto"]
            job["objects"][event["objectid"]]["movespeed"] = event["speed"] #xx points per second
            job["objects"][event["objectid"]]["movespeedinframe"] = int(event["speed"] / job["fps"])   # xx points per frame
            job["objects"][event["objectid"]]["movecurve"] = event["track"]
            job["objects"][event["objectid"]]["moveleavetrace"] = event["leavetrace"]
            #job["objects"][event["objectid"]]["moveendtime"] = event["leavetrace"]
            job["objects"][event["objectid"]]["moveendframe"] = calculatemoveendframe(job["objects"][event["objectid"]])

        if event["action"] == "end":
            job["endtime"] = event["time"]
            job["endframe"] = int(job["fps"] *  event["time"])


def work(job):
    pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python animation.py sample/sample.json ")
        exit(1)

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s]\t[%(process)s] %(message)s")
    with open(sys.argv[1]) as fp:
        animationjob = json.load(fp)

    initialize(animationjob)
    work(animationjob)
    print(f"done. output is saved in {animationjob['resultfile']}")