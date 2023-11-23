import math

import  numpy as np
import sys, logging, json, time, os, copy
#from cv2 import cv2
import cv2
def calculatemoveendframe( action):
    step = [(action['movetolocation'][0] - action['movestartlocation'][0])/ (action['moveendframe']-action['movestartframe']),
                (action['movetolocation'][1] - action['movestartlocation'][1])/ (action['moveendframe']-action['movestartframe'])
                ]
    return step


def initialize(job):
    if "jobid" not in job:
        job["jobid"] = str(time.time())

    job["tempfolder"] = os.path.join("sample", "output", job["jobid"])
    job["resultfile"] = os.path.join("sample", "output", f"{job['jobid']}.mp4")
    job["objects"] = {}
    for event in job["events"]:
        if event["action"] == "add":
            _object = {"starttime": event["time"],
                       "startframe": int(job["fps"] *  event["time"]),
                       "location": event["location"],
                       "img": cv2.imread(event["imgfile"], -1)}
            job["objects"][event["objectid"]] = _object

        if event["action"] == "remove":
            job["objects"][event["objectid"]]["endtime"] = event["time"]
            job["objects"][event["objectid"]]["endframe"] = int(job["fps"] *  event["time"])

        if event["action"] == "move":
            if "moveactions" not in _object:
                _object["moveactions"] = []
            moveaction = {"movestarttime": event["time"],
                          "movestartframe": int(job["fps"] *  event["time"]),
                          "moveendtime": event["endtime"],
                          "moveendframe": int(job["fps"] *  event["endtime"]),
                          "movetolocation": event["moveto"],

                          "movecurve": event["track"],  #stright
                          "moveleavetrace": event["leavetrace"]
                          }
            _object["moveactions"].append(moveaction)
            # job["objects"][event["objectid"]]["movestarttime"] = event["time"]
            # job["objects"][event["objectid"]]["movestartframe"] = int(job["fps"] *  event["time"])
            # job["objects"][event["objectid"]]["movetolocation"] = event["moveto"]
            # job["objects"][event["objectid"]]["movespeed"] = event["speed"] #xx points per second
            # job["objects"][event["objectid"]]["movespeedinframe"] = int(event["speed"] / job["fps"])   # xx points per frame
            # job["objects"][event["objectid"]]["movecurve"] = event["track"]
            # job["objects"][event["objectid"]]["moveleavetrace"] = event["leavetrace"]
            # #job["objects"][event["objectid"]]["moveendtime"] = event["leavetrace"]
            # job["objects"][event["objectid"]]["moveendframe"] = calculatemoveendframe(job["objects"][event["objectid"]])

        if event["action"] == "end":
            job["endtime"] = event["time"]
            job["endframe"] = int(job["fps"] *  event["time"])




def work(job):
    os.makedirs(job["tempfolder"], exist_ok=True)
    video_writer = cv2.VideoWriter(animationjob['resultfile'],
                                   cv2.VideoWriter_fourcc('M', 'P', '4', 'V'),
                                   job["fps"],
                                   [job["canvas_size"][1],  job["canvas_size"][0]]
                                   )
    canvas = np.zeros((job["canvas_size"][0], job["canvas_size"][1], 3), dtype="uint8")
    for i in range(job["endframe"]):
        for _objectid in job["objects"]:
            _object = job["objects"][_objectid]
            if "endframe" not in _object:
                _object["endframe"] = job["endframe"]
            if _object["startframe"] <= i <= _object["endframe"]:
                if "moveactions" in _object:
                    for moveaction in _object["moveactions"]:   # there should be only one action at any given time for an object.
                        if moveaction["movestartframe"] <= i <= moveaction["moveendframe"]:
                            # this is for "straight line" moving.
                            if "movestep" not in moveaction:    # initialize move step base on current location
                                moveaction["movestartlocation"] = copy.deepcopy(_object['location'])
                                moveaction["movestep"] = calculatemoveendframe( moveaction)
                            _object["location"][0] = int(moveaction["movestartlocation"][0] +  (i-moveaction["movestartframe"]) * moveaction["movestep"][0])
                            _object["location"][1] = int(moveaction["movestartlocation"][1] +  (i-moveaction["movestartframe"]) * moveaction["movestep"][1])
                            _object["location"][0] = min(max(_object["location"][0], 0), canvas.shape[0])
                            _object["location"][1] = min(max(_object["location"][1], 0), canvas.shape[1])

                height = _object["img"].shape[0]
                if _object["location"][0] + height > canvas.shape[0]:
                    height = canvas.shape[0]-_object["location"][0]
                width = _object["img"].shape[1]
                if _object["location"][1] + width > canvas.shape[1]:
                    width = canvas.shape[1]-_object["location"][1]

                y1, y2 = _object["location"][0], _object["location"][0] + height
                x1, x2 = _object["location"][1], _object["location"][1] + width

                alpha_s = _object["img"][:height, :width, 3] / 255.0
                alpha_l = 1.0 - alpha_s

                for c in range(0, 3):
                    canvas[y1:y2, x1:x2, c] = (alpha_s * _object["img"][:height, :width, c] +
                                              alpha_l * canvas[y1:y2, x1:x2, c])
        cv2.imwrite(os.path.join(job["tempfolder"], f"{i}.png"), canvas)
        video_writer.write(canvas)
    # use ffmpeg to compbine them using the specify fps
    # "ffmpeg -r 1/5 -start_number 2 -i img%03d.png -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4"
    video_writer.release()


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