from tubecutterdxf import CutPattern, CutBrick, CutSpiral, CutPartline
from tubecutterdxf import INCH, MM
from math import pi

def demoBrick(OD = 0.016 * INCH, continuous = False):
    pattern = CutPattern()

    pattern.add(CutPartline(OD))
    pattern.add(CutBrick(
                        OD=OD,
                        offsetX=0.1 * INCH, 
                        offsetA=30,
                        cutLength=90,
                        numRadialCuts=2,
                        spacingA=45,
                        pitch=0.01 * INCH, 
                        instances=20,
                        variableCutLength=False, 
                        cutIncrease=0,
                        variablePitch=False,
                        pitchIncrease=0,
                        continuous=continuous))
    
    pattern.draw()
    pattern.save('demo/demoBrick')

def demoSpiral(OD = 0.016 * INCH, continuous = False):
    pattern = CutPattern()

    pattern.add(CutPartline(OD))
    pattern.add(CutSpiral(
                        OD=OD,
                        offsetX=0.1 * INCH, 
                        offsetA=30,
                        cutLength=90,
                        unCutLength=45,
                        pitch=0.01 * INCH, 
                        instances=20,
                        variableCutLength=False, 
                        cutIncrease=0,
                        unCutIncrease=0,
                        continuous=continuous))
    
    pattern.draw()
    pattern.save('demo/demoSpiral')

def linkedCuts(OD = 0.016 * INCH, continuous = False):
    pattern = CutPattern()

    # Cut Constant Spline
    splinesConst = 3
    lengthConst = 6 * INCH
    pitch = 0.0023 * INCH
    instancesConst = int(lengthConst / pitch)
    cutStart = (360 / 4 * 3) / splinesConst  # 3:1, Cut:Uncut

    cutOne = CutBrick(OD, 0, 0, cutStart, splinesConst, 33, pitch, instancesConst, continuous=continuous)
    
    # Cut Variable Spline
    splinesVary = 3
    lengthVary = 3 * INCH
    pitchStart = 0.0023 * INCH
    pitchEnd = 0.006 * INCH
    avgPitch = (pitchEnd + pitchStart) / 2
    instancesVary = int(lengthVary / avgPitch)
    pitchChange = (pitchEnd - pitchStart) / instancesVary

    cutStart = (360 / 4 * 3) / splinesVary  # 3:1, Cut:Uncut
    cutEnd = (0.002 * INCH / (OD * pi)) * 360
    cutChange = - (cutStart - cutEnd) / instancesVary
    
    offsetX = cutOne.xNext
    offsetA = cutOne.yNext / cutOne.c * 360

    cutTwo = CutBrick(OD, offsetX, offsetA, cutStart, splinesVary, 33, pitchStart, instancesVary, True, cutChange, True, pitchChange, continuous=continuous)

    pattern.add(cutOne)
    pattern.add(cutTwo)

    # Save File
    p1 = str(round(pitch / INCH, 5)).split('.')[1]
    p2 = str(round(pitchEnd / INCH, 5)).split('.')[1]
    l1 = str(round(lengthConst / INCH))
    l2 = str(round(lengthVary / INCH))

    filename = f'demo/linkedCuts_p{p1}x{l1}_p{p2}x{l2}'
    pattern.draw()
    pattern.save(filename)
    print(f'{instancesConst*splinesConst + instancesVary*splinesVary} Cuts')

if __name__ == '__main__':
    # Human Readable
    # demoBrick()
    # demoSpiral()
    linkedCuts()

    # Final
    # demoBrick(continuous=True)
    # demoSpiral(continuous=True)
    # linkedCuts(continuous=True)