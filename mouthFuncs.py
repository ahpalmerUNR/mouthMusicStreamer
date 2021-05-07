# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-01-28 21:38:05
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-05-06 13:51:43

gridSizeEyes = 16.0
gridSizeMouth = 32.0
gridHMouth = 8
gridHEyes = 15
gridWMouth = 10
gridWEyes = 20
imageWidth = 320.0
imageHeight = 240.0

def setGridSize(imageW,imageH):
	global imageWidth,imageHeight
	imageWidth = imageW
	imageHeight = imageH
	setGridSizeMouth()
	setGridSizeEyes()

def setGridSizeMouth():
	global gridHMouth,gridWMouth
	gridHMouth = int(imageHeight/gridSizeMouth) + 1 if imageHeight%gridSizeMouth > 0 else int(imageHeight/gridSizeMouth)
	gridWMouth = int(imageWidth/gridSizeMouth) + 1 if imageWidth%gridSizeMouth > 0 else int(imageWidth/gridSizeMouth)

def setGridSizeEyes():
	global gridHEyes,gridWEyes
	gridHEyes = int(imageHeight/gridSizeEyes) + 1 if imageHeight%gridSizeEyes > 0 else int(imageHeight/gridSizeEyes)
	gridWEyes = int(imageWidth/gridSizeEyes) + 1 if imageWidth%gridSizeEyes > 0 else int(imageWidth/gridSizeEyes)
	
def decodeLabel(label):
	labelMouth = label[0]
	labelEyes = label[1]
	foundValues = {}

	if labelMouth.device == "cuda":
		labelMouth = labelMouth.to('cpu')
		labelEyes = labelEyes.to('cpu')

	#Parts Cells
	lipCell = labelMouth[0,0].argmax()
	tongueCell = labelMouth[0,1].argmax()
	leftEyeCell = labelEyes[0,0].argmax()
	rightEyeCell = labelEyes[0,1].argmax()
	browCell = labelEyes[0,2].argmax()
	
	
	lipCell = getGridCoords(lipCell,gridWMouth)
	tongueCell = getGridCoords(tongueCell,gridWMouth)
	leftEyeCell = getGridCoords(leftEyeCell,gridWEyes)
	rightEyeCell = getGridCoords(rightEyeCell,gridWEyes)
	browCell = getGridCoords(browCell,gridWEyes)

  ## Fill Dict
	#Mouth Values
	foundValues["lipConf"] = getGridItem(labelMouth,0,lipCell)
	foundValues["tongueConf"] = getGridItem(labelMouth,1,tongueCell)
	foundValues["lipPosition"] = getPositionFromCell(labelMouth,3,4,lipCell,gridSizeMouth)
	foundValues["tonguePosition"] = getPositionFromCell(labelMouth,5,6,tongueCell,gridSizeMouth)
	triggerValues = getMouthTriggerFromLabel(labelMouth,tongueCell)
	foundValues["mouthTrigger"] = triggerValues[1]
	foundValues["mouthTriggerConf"] = triggerValues[0]
	foundValues["mouthIntensity"] = int(getGridItem(labelMouth,2,lipCell)*100)
	
	#Eye Values
	foundValues["leftEyeConf"] = getGridItem(labelEyes,0,leftEyeCell)
	foundValues["rightEyeConf"] = getGridItem(labelEyes,1,rightEyeCell)
	foundValues["leftBrowConf"] = getGridItem(labelEyes,2,browCell)
	foundValues["leftEyePosition"] = getPositionFromCell(labelEyes,4,5,leftEyeCell,gridSizeEyes)
	foundValues["rightEyePosition"] = getPositionFromCell(labelEyes,6,7,rightEyeCell,gridSizeEyes)
	foundValues["leftBrowPosition"] = getPositionFromCell(labelEyes,8,9,browCell,gridSizeEyes)
	foundValues["leftBrowBoxWidth"] = int(getGridItem(labelEyes,10,browCell)*imageWidth)
	foundValues["leftBrowBoxHeight"] = int(getGridItem(labelEyes,11,browCell)*imageHeight)
	triggerValues = getEyeTriggerFromLabel(labelEyes,leftEyeCell)
	foundValues["eyeTrigger"] = triggerValues[1]
	foundValues["eyeTriggerConf"] = triggerValues[0]
	foundValues["eyeIntensity"] = int(getGridItem(labelEyes,3,leftEyeCell)*100)

	return foundValues

def getGridCoords(cellNumber,cellSizes):
	return int(cellNumber/cellSizes),int(cellNumber%cellSizes)

def getGridItem(label,index,cell):
	return label[0,index,cell[0],cell[1]].item()

def getPositionFromCell(label,indexX,indexY,cell,gridSize):
	xVal = int(getGridItem(label,indexX,cell)*gridSize + gridSize*cell[1])
	yVal = int(getGridItem(label,indexY,cell)*gridSize + gridSize*cell[0])
	return xVal,yVal

def getMouthTriggerFromLabel(label,cell):
	compareList = [(getGridItem(label,7,cell),"None"),(getGridItem(label,8,cell),"Talking"),(getGridItem(label,9,cell),"Tongue Out"),(getGridItem(label,10,cell),"Pucker Lips"),(getGridItem(label,11,cell),"In Cheek")]
	maxItem = max(compareList,key=lambda x:x[0])
	return maxItem
	
def getEyeTriggerFromLabel(label,cell):
	compareList = [(getGridItem(label,12,cell),"None"),(getGridItem(label,13,cell),"Left Wink"),(getGridItem(label,14,cell),"Right Wink"),(getGridItem(label,15,cell),"Left Brow")]
	maxItem = max(compareList,key=lambda x:x[0])
	return maxItem

def rescaleLabelPositions(labelDict,scales):
	wScale,hScale = scales
	labelDict["tonguePosition"] = (int(labelDict["tonguePosition"][0]/wScale),int(labelDict["tonguePosition"][1]/hScale))
	labelDict["lipPosition"] = (int(labelDict["lipPosition"][0]/wScale),int(labelDict["lipPosition"][1]/hScale))
	labelDict["leftEyePosition"] = (int(labelDict["leftEyePosition"][0]/wScale),int(labelDict["leftEyePosition"][1]/hScale))
	labelDict["rightEyePosition"] = (int(labelDict["rightEyePosition"][0]/wScale),int(labelDict["rightEyePosition"][1]/hScale))
	labelDict["leftBrowPosition"] = (int(labelDict["leftBrowPosition"][0]/wScale),int(labelDict["leftBrowPosition"][1]/hScale))
	labelDict["leftBrowBoxWidth"] = int(labelDict["leftBrowBoxWidth"]/wScale)
	labelDict["leftBrowBoxHeight"] = int(labelDict["leftBrowBoxHeight"]/hScale)
