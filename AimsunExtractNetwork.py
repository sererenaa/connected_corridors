from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *
#from AAPI import *

import datetime
import pickle
import sys
import csv
import os

def ExtractJunctionInformation(model,outputLocation):

    #####################Get the junction information#####################
    junctionInfFileName=outputLocation+'\JunctionInf.txt'
    #print junctionInfFileName
    junctionInfFile = open(junctionInfFileName, 'w')

    global DefaultAngle

    # Get the number of nodes
    numJunction=0
    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKNode")):
        numJunction = numJunction+ len(types)
    junctionInfFile.write('Number of junctions:\n')
    junctionInfFile.write(('%i\n') % numJunction)
    junctionInfFile.write('\n')

    # Loop for each junction
    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKNode")):
        for junctionObj in types.itervalues():
            junctionInfFile.write(
                'Junction ID,Name, External ID, Signalized,# of incoming sections,# of outgoing sections, # of turns\n')

            junctionID = junctionObj.getId()  # Get the junction ID
            junctionExtID = junctionObj.getExternalId()  # Get the external ID
            junctionName = junctionObj.getName()  # Get name of the junction

            numEntranceSections = junctionObj.getNumEntranceSections()  # Get the number of entrance sections
            numExitSections = junctionObj.getNumExitSections()  # Get the number of exit sections
            entranceSections = junctionObj.getEntranceSections()  # Get the list of GKSection objects
            exitSections = junctionObj.getExitSections()

            turns=junctionObj.getTurnings()
            numTurn = len(turns)  # Get the number of turns

            signalGroupList = junctionObj.getSignals()  # Check whether a junction is signalzied or not
            if len(signalGroupList) == 0:
                signalized = 0
            else:
                signalized = 1

            # Write the first line
            junctionInfFile.write('%i,%s,%s,%i,%i,%i,%i\n' % (
            junctionID, junctionName, junctionExtID, signalized, numEntranceSections, numExitSections, numTurn))
            # Write the entrance sections
            junctionInfFile.write("Entrances links:\n")
            for j in range(numEntranceSections - 1):
                junctionInfFile.write(("%i,") % entranceSections[j].getId())
            junctionInfFile.write(("%i\n") % entranceSections[numEntranceSections - 1].getId())
            # Write the exit sections
            junctionInfFile.write("Exit links:\n")
            for j in range(numExitSections - 1):
                junctionInfFile.write(("%i,") % exitSections[j].getId())
            junctionInfFile.write(("%i\n") % exitSections[numExitSections - 1].getId())

            ## Update the turning description
            UpdateTurningDescription(numEntranceSections, entranceSections, junctionObj, DefaultAngle)

            # Write the turn information
            junctionInfFile.write(
                "Turning movements:turnID,origSectionID,destSectionID,origFromLane,origToLane,destFromLane,destToLane, description, turn speed\n")
            for j in range(numTurn):
                turnObj = turns[j]
                origin=turnObj.getOrigin()
                destination=turnObj.getDestination()

                originObj = model.getCatalog().find(origin.getId())  # Get the section object
                numLanesOrigin=len(originObj.getLanes())
                destinationObj = model.getCatalog().find(destination.getId())  # Get the section object
                numLanesDest = len(destinationObj.getLanes())

                turnAngle=turnObj.calcAngleBridge()
                # FromLane: leftmost lane number (GKTurning)/ rightmost lane number (API/our definition)
                # ToLane: rightmost lane number /leftmost lane number (API/our definition)
                # Note: lanes are organized from right to left in our output!!
                # It is different from the definition in the GKSection function
                junctionInfFile.write("%i,%i,%i,%i,%i,%i,%i,%s,%i,%.4f\n" % (
                    turnObj.getId(), origin.getId(), destination.getId(), numLanesOrigin-turnObj.getOriginToLane(),
                    numLanesOrigin-turnObj.getOriginFromLane(),numLanesDest-turnObj.getDestinationToLane(),
                    numLanesDest-turnObj.getDestinationFromLane(), turnObj.getDescription(),turnObj.getSpeed()*0.621371,turnAngle))

            # Write the turn orders by section from left to right
            junctionInfFile.write(
                "Turning movements ordered from left to right in a give section: section ID, # of turns, [turn IDs]\n")
            for j in range(numEntranceSections):
                string = str(entranceSections[j].getId()) + ','
                turnInfSection = junctionObj.getFromTurningsOrderedFromLeftToRight(entranceSections[j])
                string = string + str(len(turnInfSection)) + ','
                for k in range(len(turnInfSection) - 1):
                    string = string + str(turnInfSection[k].getId()) + ','
                string = string + str(turnInfSection[len(turnInfSection) - 1].getId()) + '\n'
                junctionInfFile.write(string)
            junctionInfFile.write("\n")
    return 0

def UpdateTurningDescription(numEntranceSections,entranceSections,junctionObj,DefaultAngle):
    # This function is used to update the turning description in Aimsun
    # Francois has added descriptions to some turning movements
    # (pertected left, permissive left, U turn, two way stopbar)

    for j in range(numEntranceSections):
        turnInfSection = junctionObj.getFromTurningsOrderedFromLeftToRight(entranceSections[j])
        # Get the turning movements from left to right


        #Returns the angle, in degrees, between the last segment of the origin section and
        #  the turn line. When going clockwise the angle will be negative and when going
        # counterclockwise the angle will be positive

        # Get the turn with the minumum angle
        curAddr = 0
        minAngle = abs(turnInfSection[0].calcAngleBridge())
        descriptions=[]
        leftTurnIdx=[]
        lastLeftIdx=[]
        for k in range(len(turnInfSection)):
            individualDescription=turnInfSection[k].getDescription()
            descriptions.append(individualDescription)
            if(individualDescription is not None): # If we have additional descriptions from the model
                # Check whether it is a left-turn movement or not
                idxLeft=False
                if (individualDescription.find("Left")>=0):
                    idxLeft=True
                idxUTurn=False
                if (individualDescription.find("U Turn")>=0):
                    idxUTurn=True
                if(idxLeft or idxUTurn): # If yes
                    leftTurnIdx.append(1)
                    lastLeftIdx=k # Get the index of the last left turn movement
                else: # If no
                    leftTurnIdx.append(0)
            else: # No additional description
                leftTurnIdx.append(0)

            # Get the minimum angle
            if(minAngle>abs(turnInfSection[k].calcAngleBridge())):
                curAddr=k
                minAngle = abs(turnInfSection[k].calcAngleBridge())

        if(sum(leftTurnIdx)==0): # No additional description to help?
            if minAngle <=DefaultAngle: # Through movement
                turnInfSection[curAddr].setDescription('Through'+':'+descriptions[curAddr])
                for t in range(curAddr): # Set turns on the left to be Left Turn
                    turnInfSection[t].setDescription('Left Turn'+':'+descriptions[t])
                for t in range(curAddr+1,len(turnInfSection)): # Set turns on the right to be Right Turn
                    turnInfSection[t].setDescription('Right Turn'+':'+descriptions[t])
            else:
                if len(turnInfSection)==3:
                    # It is possible for some special case that Through movement has
                    # a big turning angle, then Overwrite it
                    # In the case of three movements, we consider they are left, through, and right
                    turnInfSection[0].setDescription('Left Turn'+':'+descriptions[0])
                    turnInfSection[1].setDescription('Through'+':'+descriptions[1])
                    turnInfSection[2].setDescription('Right Turn'+':'+descriptions[2])

                elif (turnInfSection[curAddr].calcAngleBridge()>DefaultAngle): # Have a bigger angle to the left
                    for t in range(curAddr+1): # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn'+':'+descriptions[t])
                    for t in range(curAddr+1,len(turnInfSection)): # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn'+':'+descriptions[t])

                elif (turnInfSection[curAddr].calcAngleBridge()<-DefaultAngle): # Have a bigger angle to the right
                    for t in range(curAddr): # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn'+':'+descriptions[t])
                    for t in range(curAddr,len(turnInfSection)): # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn'+':'+descriptions[t])
        else: # Has additional descriptions
            if minAngle <= DefaultAngle: # It is probably a through movement
                if lastLeftIdx<curAddr: # Yes, it is!
                    for t in range(curAddr):  # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn' + ':' + descriptions[t])
                    turnInfSection[curAddr].setDescription('Through' + ':' + descriptions[curAddr])
                    for t in range(curAddr+1,len(turnInfSection)):  # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn' + ':' + descriptions[t])
                else: # If, it is not! No through movements!
                    for t in range(lastLeftIdx+1):  # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn' + ':' + descriptions[t])
                    for t in range(lastLeftIdx+1,len(turnInfSection)):  # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn' + ':' + descriptions[t])
            else:
                if len(turnInfSection)==3 and lastLeftIdx==0:
                    # It is possible for some special case that Through movement has
                    # a big turning angle, then Overwrite it
                    # In the case of three movements, we consider they are left, through, and right
                    turnInfSection[0].setDescription('Left Turn'+':'+descriptions[0])
                    turnInfSection[1].setDescription('Through'+':'+descriptions[1])
                    turnInfSection[2].setDescription('Right Turn'+':'+descriptions[2])

                elif (turnInfSection[curAddr].calcAngleBridge() > DefaultAngle):  # Have a bigger angle to the left
                    if lastLeftIdx>curAddr:
                        curAddr=lastLeftIdx

                    for t in range(curAddr+1):  # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn' + ':' + descriptions[t])
                    for t in range(curAddr+1,len(turnInfSection)):  # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn' + ':' + descriptions[t])

                elif (turnInfSection[curAddr].calcAngleBridge() < -DefaultAngle):  # Have a bigger angle to the right
                    if lastLeftIdx >=curAddr:
                        curAddr = lastLeftIdx+1

                    for t in range(curAddr):  # Set turns on the left to be Left Turn
                        turnInfSection[t].setDescription('Left Turn' + ':' + descriptions[t])
                    for t in range(curAddr, len(turnInfSection)):  # Set turns on the right to be Right Turn
                        turnInfSection[t].setDescription('Right Turn' + ':' + descriptions[t])

def ExtractSectionInformation(model,outputLocation):

    ####################Get the section information#####################
    sectionInfFileName=outputLocation+'\SectionInf.txt'
    sectionInfFile = open(sectionInfFileName, 'w')

    translator=GKCoordinateTranslator(model)

    # Get the number of sections
    numSection=0
    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKSection")):
        numSection=numSection+len(types)
    sectionInfFile.write('Number of sections:\n')
    sectionInfFile.write(('%i\n') % numSection)
    sectionInfFile.write('\n')

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKSection")):
        for sectionObj in types.itervalues():
            sectionID = sectionObj.getId()  # Get the section ID
            sectionExtID = sectionObj.getExternalId()  # Get the section external ID
            sectionName = sectionObj.getName()  # Get the section name

            # Write the first line
            lanes=sectionObj.getLanes()
            totLane=len(lanes)
            points = sectionObj.calculatePolyline()  # Get the shape files
            totPoint = len(points)
            sectionInfFile.write('Section ID,Name,External ID,# of lanes,# of points\n')
            sectionInfFile.write('%i,%s,%s,%i,%i\n' % (sectionID, sectionName, sectionExtID, totLane,totPoint))

            # Write the lane lengths
            sectionInfFile.write("Lane lengths:\n")
            for j in range(totLane - 1):  # Loop for each lane: from leftmost to rightmost
                length = float(sectionObj.getLaneLength(j)) * 3.28084
                sectionInfFile.write(("%.4f,") % length)  # Get the lane length in feet
            length = float(sectionObj.getLaneLength(totLane - 1)) * 3.28084
            sectionInfFile.write(("%.4f\n") % length)

            # Write the lane starting point
            sectionInfFile.write("Initial starting point (initial offset):\n")
            #An entry side lane have initialOffset equal to 0.0 and finalOffset equal to the length of the side lane.
            # An exit side lane have initialOffset equal to the length of the side lane (but negative) and finalOffset equal to 0.0.
            for j in range(totLane - 1):  # Loop for each lane: from leftmost to rightmost
                sectionLane = sectionObj.getLane(j)  # Get the section_lane object
                sectionInfFile.write(("%.4f,") % (sectionLane.getInitialOffset() * 3.28084))  # Get the initial offset
            sectionLane = sectionObj.getLane(totLane - 1)  # Get the section_lane object
            sectionInfFile.write(("%.4f\n") % (sectionLane.getInitialOffset() * 3.28084))

            # Write the lane properties
            sectionInfFile.write("Is full lane:\n")
            for j in range(totLane - 1):  # Loop for each lane: from leftmost to rightmost
                sectionLane = sectionObj.getLane(j)  # Get the section_lane object
                sectionInfFile.write(("%i,") % sectionLane.isFullLane())  # Get the lane status
            sectionLane = sectionObj.getLane(totLane - 1)  # Get the section_lane object
            sectionInfFile.write(("%i\n") % sectionLane.isFullLane())  # Get the lane status: To find whether it is a full lane: use to identify left-turn and right-turn pockets

            # Write the shape files
            sectionInfFile.write("Shape points:\n")
            for j in range(totPoint-1):
                point= translator.toDegrees(points[j])
                sectionInfFile.write(("%.6f,%.6f,") % (point.x,point.y))
            point = translator.toDegrees(points[totPoint-1])
            sectionInfFile.write(("%.6f,%.6f\n") % (point.x, point.y))

            sectionInfFile.write("\n")
    return 0


DefaultAngle=8
gui=GKGUISystem.getGUISystem().getActiveGui()
model = gui.getActiveModel()
outputLocation='C:\Users\Serena\connected_corridors'

# Call to extract junction information
print 'Extract junction information!'
ExtractJunctionInformation(model,outputLocation)

# Call to extract Section information
print 'Extract section information!'
ExtractSectionInformation(model,outputLocation)
print 'Done with network extraction!'