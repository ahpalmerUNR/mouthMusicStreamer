# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-01-28 21:38:05
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-01-28 21:57:00

gridSize = 32.0
gridH = 8
gridW = 10
imageW = 240.0
imageH = 320.0

def setGridSize(imageWidth,imageHeight):
	global imageW,imageH,gridH,gridW
	imageW = imageWidth
	imageH = imageHeight
	gridH = int(imageH/gridSize) + 1 if imageH%gridSize > 0 else int(imageH/gridSize)
	gridW = int(imageW/gridSize) + 1 if imageW%gridSize > 0 else int(imageW/gridSize)
	
def decodeLabel(label):
	foundValues = {}
	# Identify Tongue and Lip Cells
	tongueCell = label[0,3].argmax() 
	lipCell = label[0,0].argmax()
	tongueCell = int(tongueCell/gridW),int(tongueCell%gridW)
	lipCell = int(lipCell/gridW),int(lipCell%gridW)
	# Decode Label
	foundValues["lipPosition"] = int(label[0,1,lipCell[0],lipCell[1]].item()*gridSize + gridSize*lipCell[1]),int(label[0,2,lipCell[0],lipCell[1]].item()*gridSize + gridSize*lipCell[0])
	foundValues["tonguePosition"] = int(label[0,6,tongueCell[0],tongueCell[1]].item()*gridSize + gridSize*tongueCell[1]),int(label[0,7,tongueCell[0],tongueCell[1]].item()*gridSize + gridSize*tongueCell[0])
	foundValues["tongueOut"] = label[0,4,tongueCell[0],tongueCell[1]].item()
	foundValues["intensity"] = int(label[0,5,tongueCell[0],tongueCell[1]].item()*100)
	foundValues["lipConf"] = label[0,0,lipCell[0],lipCell[1]].item()
	foundValues["tongueConf"] = label[0,3,tongueCell[0],tongueCell[1]].item()
	return foundValues