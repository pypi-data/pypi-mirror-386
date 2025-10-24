from flask import Flask, request
from src.tubecutterdxf import CutBrick, CutSpiral, CutPartline, CutPattern

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello"

@app.route("/cutBrick", methods=["POST"])
def cutBrick():
    f = request.form
    try:
        pattern = CutBrick(f["OD"], f["offsetX"], f["offsetA"], f["cutLength"], f["unCutLength"], f["pitch"], f["instances"], f["variableCutLength"], f["cutIncrease"], f["unCutIncrease"], f["continuous"])
        lines = pattern.getLines()
        config = pattern.dumpConfig()

    except Exception as e:
        print(e)

    # returns lines + config file
    return {"lines": lines, "config": config}

@app.route("/cutSpiral", methods=["POST"])
def cutSpiral():
    f = request.form
    try:
        pattern = CutSpiral(f["OD"], f["offsetX"], f["offsetA"], f["cutLength"], f["numRadialCuts"], f["spacingA"], f["pitch"], f["instances"], f["variableCutLength"], f["cutIncrease"], f["variablePitch"], f["pitchIncrease"], f["continuous"])
        lines = pattern.getLines()
        config = pattern.dumpConfig()
    
    except Exception as e:
        print(e)
    # returns lines + config file
    return {"lines": lines, "config": config}

@app.route("/cutPartline", methods=["POST"])
def cutPartline():
    f = request.form
    try:
        pattern = CutPartline(f["OD"], f["offsetX"])
        lines = pattern.getLines()
        config = pattern.dumpConfig()

    except Exception as e:
        print(e)

    # returns lines + config file
    return {"lines": lines, "config": config}

@app.route("/makeDXF", methods=["POST"])
def makeDXF():
    # returns the DXF built from the config file
    pattern = CutPattern()
    return "DXF"