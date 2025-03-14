import json
import math


def createAutosamplerPosition(sampleNum : int):
    if sampleNum == 999:
        return {
            "rack":999,"row":0,"col":0
        }
    rack = math.floor(sampleNum/60)
    col = math.floor((sampleNum - (rack*60))/12)
    row = sampleNum % 12
    return {
        "rack": rack,
        "row": row,
        "col": col,
    }

def createBasicDilutionRun(sampleVolume:int,dilutionVolume :int):
    output : list[dict] = []
    for sampleNum in ( list(range(60))+ list(range(120,180)) ):
        asPos = createAutosamplerPosition(sampleNum)
        rinse = createAutosamplerPosition(999)
        output.append({
            "presample": None,
            "sample": {
                "position": asPos,
                "volume": sampleVolume,
                "waitSeconds":0
            },
            "predispense": {
                "position": rinse,
                "volume":0,
                "waitSeconds":1
            },
            "dispense": {
                "position": createAutosamplerPosition( sampleNum + 60 ),
                "volume": dilutionVolume,
                "waitSeconds": 0
            },
            "postdispense": {
                "position": rinse,
                "volume": 3000,
                "waitSeconds":0
            }
        })
    return output


def createBasicDispenseRun(dilutionVolume :int):
    output : list[dict] = []
    for dispenseNum in range(240):
        asPos = createAutosamplerPosition(dispenseNum)
        rinse = createAutosamplerPosition(999)
        output.append({
            "presample": None,
            "sample": None,
            "predispense": None,
            "dispense": {
                "position": asPos,
                "volume": dilutionVolume,
                "waitSeconds": 0
            },
            "postdispense": None
        })
    return output



if __name__ == "__main__":
    out = createBasicDispenseRun(6000)
    with open("defaultDispense.json", "w") as outfile:
        json.dump(out, outfile)