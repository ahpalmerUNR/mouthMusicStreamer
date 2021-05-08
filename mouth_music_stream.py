# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-01-19 15:34:08
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-05-08 16:58:29
import MouthMusicModel as mmodel
import mouthFuncs as mfunc 

import torch
import time
import cv2 as cv
import numpy as np

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from oscpy.client import OSCClient

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu" )

# Default Values
streamIP = "127.0.0.1"
streamPort = 6730

streamCheekIntensityTopic = "/tongue_gestures/cheek_intensity"
streamHorizontalTopic = "/tongue_gestures/horizontal"
streamVerticalTopic = "/tongue_gestures/vertical"
streamPuckerTopic = "/tongue_gestures/pucker"
streamTongueOutTopic = "/tongue_gestures/tongue_out"
streamNumberOfPositions = 100

streamRightEyeTopic = "/tongue_gestures/right_eye"
streamLeftEyeTopic = "/tongue_gestures/left_eye"
streamLeftBrowTopic = "/tongue_gestures/brow"

streamMouthTopicEndControl = [None,None]
streamEyeTopicEndControl = [None,None]

capture = cv.VideoCapture(0)
captureWidth = 640
captureHeight = 480
captureShowBoxOnRecord = False

lipOffset = (0,2)
lipCircleRadius = 10
mouthDetectionConfidenceThreshold = 0.3
tongueDetectionConfidenceThreshold = 0.2
eyeDetectionConfidenceThreshold = 0.2
mouthIntensityThreshold = 15
eyeIntensityThreshold = 15

model = []
mouthModel = []
eyeModel = []

# Flow control and tkinter image workaround list
stopCurent = True
tkimg = [None]

def main():
	global mouthModel,eyeModel
	try:
		loadSettings()
	except Exception as e:
		print("Settings Reset to Default")
		saveSettings()
	setInputVideoSize(capture,captureWidth,captureHeight)
	mouthModel,eyeModel = mmodel.loadModel("","mouthmodel.pt") # Uses model base name (arg 1) in local directory (arg 0)
	if torch.cuda.is_available():
		mouthModel.to(device)
		eyeModel.to(device)
	root = tk.Tk()
	root.geometry("900x600")
	app = Application(master=root)
	app.mainloop()
	if torch.cuda.is_available():
		torch.cuda.empty_cache()

def loadSettings():
	global streamIP,streamPort,streamVerticalTopic,streamHorizontalTopic,streamNumberOfPositions,streamPuckerTopic,streamTongueOutTopic
	global streamRightEyeTopic,streamLeftEyeTopic,streamLeftBrowTopic
	global lipOffset,lipCircleRadius,captureShowBoxOnRecord,captureWidth,captureHeight
	global mouthDetectionConfidenceThreshold,tongueDetectionConfidenceThreshold,eyeDetectionConfidenceThreshold,mouthIntensityThreshold,eyeIntensityThreshold
	global streamCheekIntensityTopic
	with open("mouthMusicSettings.txt", "r") as file:
		streamIP = file.readline().replace("\n","")
		streamPort = int(file.readline().replace("\n",""))
		streamCheekIntensityTopic = file.readline().replace("\n","")
		streamHorizontalTopic = file.readline().replace("\n","")
		streamVerticalTopic = file.readline().replace("\n","")
		streamPuckerTopic = file.readline().replace("\n","")
		streamTongueOutTopic = file.readline().replace("\n","")
		streamRightEyeTopic = file.readline().replace("\n","")
		streamLeftEyeTopic = file.readline().replace("\n","")
		streamLeftBrowTopic = file.readline().replace("\n","")
		streamNumberOfPositions = int(file.readline().replace("\n",""))
		captureWidth = int(file.readline().replace("\n",""))
		captureHeight = int(file.readline().replace("\n",""))
		lipOffset = int(file.readline().replace("\n","")), int(file.readline().replace("\n",""))
		lipCircleRadius = int(file.readline().replace("\n",""))
		mouthDetectionConfidenceThreshold = float(file.readline().replace("\n",""))
		tongueDetectionConfidenceThreshold = float(file.readline().replace("\n",""))
		eyeDetectionConfidenceThreshold = float(file.readline().replace("\n",""))
		mouthIntensityThreshold = int(file.readline().replace("\n",""))
		eyeIntensityThreshold = int(file.readline().replace("\n",""))
		stringIn = file.readline().replace("\n","")
		captureShowBoxOnRecord	= False if stringIn == "False" else True
		
def saveSettings():
	with open("mouthMusicSettings.txt", "w") as file:
		file.write(streamIP+"\n")
		file.write("%d\n"%streamPort)
		file.write(streamCheekIntensityTopic+"\n")
		file.write(streamHorizontalTopic + "\n")
		file.write(streamVerticalTopic+"\n")
		file.write(streamPuckerTopic+"\n")
		file.write(streamTongueOutTopic+"\n")
		file.write(streamRightEyeTopic+"\n")
		file.write(streamLeftEyeTopic+"\n")
		file.write(streamLeftBrowTopic+"\n")
		file.write("%d\n"%streamNumberOfPositions)
		file.write("%d\n"%captureWidth)
		file.write("%d\n"%captureHeight)
		file.write("%d\n"%lipOffset[0])
		file.write("%d\n"%lipOffset[1])
		file.write("%d\n"%lipCircleRadius)
		file.write("%f\n"%mouthDetectionConfidenceThreshold)
		file.write("%f\n"%tongueDetectionConfidenceThreshold)
		file.write("%f\n"%eyeDetectionConfidenceThreshold)
		file.write("%d\n"%mouthIntensityThreshold)
		file.write("%d\n"%eyeIntensityThreshold)
		file.write("%r\n"%captureShowBoxOnRecord)
		
def setInputVideoSize(captureObject,xDimPx,yDimPx):
	retx = captureObject.set(3,xDimPx)
	rety = captureObject.set(4,yDimPx)
	return retx and rety
		
class Application(tk.Frame):
	"""Class for application"""
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.pack({"fill":"both","expand":True})
		self.drawHome()
		self.winfo_toplevel().title("Mouth Music")
		
	def drawHome(self):
		self.clearFrame()
		self.packButton("Stream",self.drawStream)
		self.packButton("Stream and Record",self.drawRecord)
		self.packButton("Position Viewer",self.drawPositioner)
		self.packButton("Settings",self.drawSettings)
		self.packButton("Test Speed",self.drawSpeedTest)
		
	def clearFrame(self):
		for widget in self.winfo_children():
			widget.destroy()
			
	def packButton(self,text,command,color="black",side="top",fill="none",parentFrame=None):
		if parentFrame != None:
			newButton = tk.Button(parentFrame)
		else:
			newButton = tk.Button(self)
		newButton["text"] = text
		newButton["fg"] = color
		newButton["command"] = command
		if fill == "none":
			newButton["width"] = 15
		expand = True if fill != "none" else False
		newButton.pack({"side":side,"fill":fill,"expand":expand})

	def drawStream(self):
		setStopCurrent(False)
		self.addBackToHomeButton()
		runAndStreamDetections(self.master)
		
	def drawRecord(self):
		setStopCurrent(False)
		self.addBackToHomeButton()
		fileTypes = [('AVI video', '*.avi')]
		suppliedFileStream = filedialog.asksaveasfile(filetypes = fileTypes, defaultextension = fileTypes)
		recordAndStreamDetections(self.master,suppliedFileStream.name)
		
	def drawPositioner(self):
		setStopCurrent(False)
		self.clearFrame()
		imageTKLabel = tk.Label(self)
		imageTKLabel.pack()
					
		def updateImage(parent,label):
			updateImageAndDetections(parent,label)
			if not stopCurent:
				parent.master.update_idletasks()
				parent.master.after(15,lambda:updateImage(parent,label))
		
		def shiftLipOffsetXY(xShift,yShift):
			global lipOffset
			lipOffset = lipOffset[0] + xShift, lipOffset[1] + yShift
			
		def stepLipCircleRadius(radiusChange):
			global lipCircleRadius
			lipCircleRadius = lipCircleRadius + radiusChange
		
		def packPositionerButtons(parent):
			childFrame = tk.Frame(parent)
			parent.packButton("Shift Up",lambda:shiftLipOffsetXY(0,-1),side="left",parentFrame = childFrame)
			parent.packButton("Shift Down",lambda:shiftLipOffsetXY(0,+1),side="left",parentFrame = childFrame)
			parent.packButton("Shift Left",lambda:shiftLipOffsetXY(-1,0),side="left",parentFrame = childFrame)
			parent.packButton("Shift Right",lambda:shiftLipOffsetXY(+1,0),side="left",parentFrame = childFrame)
			parent.packButton("Increase Radius",lambda:stepLipCircleRadius(1),side="left",parentFrame = childFrame)
			parent.packButton("Decrease Radius",lambda:stepLipCircleRadius(-1),side="left",parentFrame = childFrame)
			childFrame.pack({"side":"top","fill":"both","expand":True})
	
		updateImage(self,imageTKLabel)
		packPositionerButtons(self)
		self.addBackToHomeButton(withClear = False)
		self.packButton("Save",saveSettings,side="right",fill="x")
		
	def drawSettings(self):
		self.clearFrame()
		updateSettings = self.packSettingsAndGetButtonCommand()
		self.addBackToHomeButton(withClear = False)
		self.packButton("Save",updateSettings,side="right",fill="x")
	
	def drawSpeedTest(self):
		setStopCurrent(False)
		self.clearFrame()
		
		def insertSubFrameWithLabel(parentFrame,variableName,currentValue):
			childFrame = tk.Frame(parentFrame)
			variableNameLabel = tk.Label(childFrame,text = variableName)
			variableNameLabel.pack({"side":"left"})
			variableValueLabel = tk.Label(childFrame,text = currentValue)
			variableValueLabel.pack({"side":"left"})
			childFrame.pack({"side":"top","fill":"both","expand":True})
			return variableValueLabel
			
		def updateLabelValues(input):
			maxVal,avgVal,minVal = input
			maxValLabel.config(text = maxVal)
			minValLabel.config(text = minVal)
			avgValLabel.config(text = avgVal)
			
		def runTest(parent):
			updateLabelValues(timeStreamAndGetStats(parent,speedLabel))
			
		speedLabel = insertSubFrameWithLabel(self,"Speed (FPS)  = ",0.0)
		maxValLabel = insertSubFrameWithLabel(self,"Max (FPS)    = ",0.0)
		avgValLabel = insertSubFrameWithLabel(self,"Average (FPS)=",0.0)
		minValLabel = insertSubFrameWithLabel(self,"Min (FPS)    =",0.0)
		self.addBackToHomeButton(withClear = False)
		self.packButton("RunTest",lambda:runTest(self),side="right",fill="x")
	
	def addBackToHomeButton(self,withClear=True):
		if withClear:
			self.clearFrame()
			
		def stopProcessClearFrameAndRedrawHome(frame):
			setStopCurrent(True)
			frame.clearFrame()
			frame.drawHome()
			
		self.packButton("Back",lambda:stopProcessClearFrameAndRedrawHome(self),color="red",side="left",fill="x")
		
	def packSettingsAndGetButtonCommand(self):
		settingsChildFrame = tk.Frame(self)
		settingEntriesDict = {}
		checkButtonVariable = tk.IntVar(value=captureShowBoxOnRecord)

		def setBoxOnRecordSetting():
			global captureShowBoxOnRecord
			if checkButtonVariable.get() == 1:
				captureShowBoxOnRecord = True
			else:
				captureShowBoxOnRecord = False

		def updateSettingsAndSave(settingEntriesDict):
			global streamIP,streamPort,streamVerticalTopic,streamHorizontalTopic,streamNumberOfPositions,streamPuckerTopic,streamTongueOutTopic
			global streamCheekIntensityTopic
			global streamRightEyeTopic,streamLeftEyeTopic,streamLeftBrowTopic
			global captureWidth,captureHeight
			global mouthDetectionConfidenceThreshold,tongueDetectionConfidenceThreshold,eyeDetectionConfidenceThreshold,mouthIntensityThreshold,eyeIntensityThreshold
			streamIP = settingEntriesDict["IP"].get()
			streamPort = int(settingEntriesDict["Port"].get())
			streamVerticalTopic = settingEntriesDict["Vertical Topic"].get()
			streamHorizontalTopic = settingEntriesDict["Horizontal Topic"].get()
			streamPuckerTopic = settingEntriesDict["Pucker Topic"].get()
			streamTongueOutTopic = settingEntriesDict["Tongue Out Topic"].get()
			streamCheekIntensityTopic = settingEntriesDict["Cheek Intensity Topic"].get()
			streamRightEyeTopic = settingEntriesDict["Left Wink Topic"].get()
			streamLeftEyeTopic = settingEntriesDict["Right Wink Topic"].get()
			streamLeftBrowTopic = settingEntriesDict["Left Brow Topic"].get()
			streamNumberOfPositions = int(settingEntriesDict["Number of Positions"].get())
			captureWidth = int(settingEntriesDict["Image Width(Pixels)"].get())
			captureHeight = int(settingEntriesDict["Image Height(Pixels)"].get())
			mouthDetectionConfidenceThreshold = float(settingEntriesDict["Mouth Gesture Detection Threshold (0.0 to 1.0)"].get())
			tongueDetectionConfidenceThreshold = float(settingEntriesDict["Tongue Detection Threshold (0.0 to 1.0)"].get())
			eyeDetectionConfidenceThreshold = float(settingEntriesDict["Eye Gesture Detection Threshold (0.0 to 1.0)"].get())
			mouthIntensityThreshold = int(settingEntriesDict["Mouth Trigger Intensity Threshold (0 to 100)"].get())
			eyeIntensityThreshold = int(settingEntriesDict["Eye Trigger Intensity Threshold (0 to 100)"].get())
			saveSettings()
			setInputVideoSize(capture,captureWidth,captureHeight)
			
		def insertSubFrameWithLabelAndEntry(parentFrame,settingEntriesDict,entryName,currentValue):
			childFrame = tk.Frame(parentFrame)
			label = tk.Label(childFrame,text = entryName)
			label.pack({"side":"left"})
			settingEntriesDict[entryName] = tk.Entry(childFrame,width=50)
			settingEntriesDict[entryName].insert(0,currentValue)
			settingEntriesDict[entryName].pack({"side":"right"})
			childFrame.pack({"side":"top","fill":"both","expand":True})
		
		def insertSubframeWithCheckbox(parentFrame,boxText,boxVariable,onvalue,offvalue,boxCommand):
			childFrame = tk.Frame(parentFrame)
			checkButton = tk.Checkbutton(childFrame, text = boxText, variable = boxVariable, onvalue = onvalue, offvalue = offvalue,command = boxCommand)
			checkButton.pack({"side":"left","fill":"both","expand":True})
			childFrame.pack({"side":"top","fill":"x","expand":True})

		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"IP",streamIP)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Port",streamPort)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Vertical Topic",streamVerticalTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Horizontal Topic",streamHorizontalTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Pucker Topic",streamPuckerTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Tongue Out Topic",streamTongueOutTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Cheek Intensity Topic",streamCheekIntensityTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Left Wink Topic",streamLeftEyeTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Right Wink Topic",streamRightEyeTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Left Brow Topic",streamLeftBrowTopic)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Number of Positions",streamNumberOfPositions)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Image Width(Pixels)",captureWidth)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Image Height(Pixels)",captureHeight)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Mouth Gesture Detection Threshold (0.0 to 1.0)",mouthDetectionConfidenceThreshold)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Tongue Detection Threshold (0.0 to 1.0)",tongueDetectionConfidenceThreshold)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Eye Gesture Detection Threshold (0.0 to 1.0)",eyeDetectionConfidenceThreshold)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Mouth Trigger Intensity Threshold (0 to 100)",mouthIntensityThreshold)
		insertSubFrameWithLabelAndEntry(settingsChildFrame,settingEntriesDict,"Eye Trigger Intensity Threshold (0 to 100)",eyeIntensityThreshold)
		insertSubframeWithCheckbox(settingsChildFrame,"Detection Box on Video",checkButtonVariable,1,0,setBoxOnRecordSetting)
		settingsChildFrame.pack({"side":"top","fill":"both","expand":True})
		return lambda:updateSettingsAndSave(settingEntriesDict)
			
def setStopCurrent(value):
	global stopCurent
	stopCurent = value
	
def runAndStreamDetections(tkRoot,recordFileName=None,recordWriter=None):
	streamClient = OSCClient(streamIP,streamPort)
	while not stopCurent:
		tkRoot.update()
		sendFrameToModelAndProcessOuput(streamClient,recordFileName=recordFileName,recordWriter=recordWriter)
	
def recordAndStreamDetections(tkRoot,recordFileName="output.avi"):
	fourcc = cv.VideoWriter_fourcc(*'XVID')
	recordWriter = cv.VideoWriter()
	recordWriter.open(recordFileName, fourcc, 30.0, (captureWidth,  captureHeight),True)
	runAndStreamDetections(tkRoot,recordFileName,recordWriter)
	recordWriter.release()

def updateImageAndDetections(parent,imageLabel):
	streamClient = OSCClient(streamIP,streamPort)
	processedModelOuputDict,image = sendFrameToModelAndProcessOuput(streamClient,withViz=True)
	image = addDetectionsToImage(image,processedModelOuputDict)
	image = addOffsetAndCircleToImage(image,processedModelOuputDict["lipPosition"])
	placeOpenCVImageInTK(image,imageLabel)

def timeStreamAndGetStats(tkRoot,speedLabel):
	streamClient = OSCClient(streamIP,streamPort)
	timeDiffs = []
	itter = 0
	while not stopCurent and itter < 120:
		start = time.perf_counter()
		tkRoot.update_idletasks()
		sendFrameToModelAndProcessOuput(streamClient)
		end = time.perf_counter()
		speed = 1/(end-start)
		speedLabel.config(text = speed)
		if itter >= 30:
			timeDiffs.append(end-start)
		itter = itter + 1
	maxVal = 1/min(timeDiffs)
	minVal = 1/max(timeDiffs)
	average = len(timeDiffs)/sum(timeDiffs)
	return maxVal,average,minVal
	
def sendFrameToModelAndProcessOuput(streamClient=None,withViz=False,recordFileName=None,recordWriter=None):
	modelInput,image = getFrame(320,240)
	mouthModelOutput = mouthModel.forward(modelInput)
	eyeModelOutput = eyeModel.forward(modelInput)
	processedModelOuputDict = processModelOuput([mouthModelOutput,eyeModelOutput])
	if streamClient != None:
		streamModelOutput(processedModelOuputDict,streamClient)
	if recordFileName != None:
		recordFrame(recordWriter,image,processedModelOuputDict)
	if withViz:
		return processedModelOuputDict,image

def addDetectionsToImage(image,processedModelOuputDict):
	scales = getWHscales(320,240)
	mfunc.rescaleLabelPositions(processedModelOuputDict,scales)
	cv.circle(image,processedModelOuputDict["lipPosition"], 2,(255,0,145),2)
	cv.circle(image,processedModelOuputDict["leftEyePosition"], 2,(17,255,0),2)
	cv.circle(image,processedModelOuputDict["rightEyePosition"], 2,(255,255,0),2)
	cv.rectangle(image,(int(processedModelOuputDict["leftBrowPosition"][0] - .5*processedModelOuputDict["leftBrowBoxWidth"]),int(processedModelOuputDict["leftBrowPosition"][1] - .5*processedModelOuputDict["leftBrowBoxHeight"])),(int(processedModelOuputDict["leftBrowPosition"][0] + .5*processedModelOuputDict["leftBrowBoxWidth"]),int(processedModelOuputDict["leftBrowPosition"][1] + .5*processedModelOuputDict["leftBrowBoxHeight"])),(0,180,200),2)

	if processedModelOuputDict["mouthIntensity"] >= mouthIntensityThreshold and processedModelOuputDict["mouthTriggerConf"] >= mouthDetectionConfidenceThreshold:
		if processedModelOuputDict["mouthTrigger"] == "In Cheek" and processedModelOuputDict["tongueConf"] >= tongueDetectionConfidenceThreshold:
			cv.circle(image,processedModelOuputDict["tonguePosition"], 2,(0,255,255),2)
		
		if processedModelOuputDict["mouthTrigger"] != "None":
			position = processedModelOuputDict["lipPosition"]
			cv.putText(image,processedModelOuputDict["mouthTrigger"],(position[0]-40,position[1]),cv.FONT_HERSHEY_SIMPLEX,1,(0,0,255))

	if processedModelOuputDict["eyeIntensity"] >= eyeIntensityThreshold and processedModelOuputDict["eyeTriggerConf"] >= eyeDetectionConfidenceThreshold and processedModelOuputDict["eyeTrigger"] != "None":
			position = processedModelOuputDict["leftEyePosition"]
			cv.putText(image,processedModelOuputDict["eyeTrigger"],(position[0]+30,position[1]),cv.FONT_HERSHEY_SIMPLEX,1,(0,0,255))

	return image
	
def addOffsetAndCircleToImage(image,lipPosition):
	cv.circle(image,lipPosition, 2,(255,255,255),2)
	cv.circle(image,lipPosition, lipCircleRadius,(255,255,255),2)
	return image	
	
def placeOpenCVImageInTK(image,label_image):
	image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
	tkimg[0] = ImageTk.PhotoImage(Image.fromarray(image))
	if not stopCurent:
		label_image.config(image=tkimg[0])

def getFrame(outputW,outputH):
	ret, img = capture.read()
	colorIMG = cv.resize(img,(outputW,outputH))
	mfunc.setGridSize(outputW,outputH)
	sample = torch.from_numpy(colorIMG).float().unsqueeze(0)
	sample = sample.permute((0,3,1,2))
	if torch.cuda.is_available():
		sample = sample.to(device)
	return sample,img
		
def processModelOuput(modelOuput):
	detectionDict = mfunc.decodeLabel(modelOuput)
	xPosition, yPosition = projectToSquareInCircle(detectionDict["tonguePosition"],detectionDict["lipPosition"])
	detectionDict["xPosition"] = xPosition
	detectionDict["yPosition"] = yPosition
	return detectionDict		
	
def streamModelOutput(modelOutput,streamClient):
	mouthTopic = None
	eyeTopic = None
	if modelOutput["mouthIntensity"] >= mouthIntensityThreshold and modelOutput["mouthTriggerConf"] >= mouthDetectionConfidenceThreshold:
		if modelOutput["mouthTrigger"] == "In Cheek" and modelOutput["tongueConf"] >= tongueDetectionConfidenceThreshold:
			streamClient.send_message(bytes(streamCheekIntensityTopic, encoding="ascii"),[modelOutput["mouthIntensity"]])
			streamClient.send_message(bytes(streamHorizontalTopic, encoding="ascii"),[modelOutput["xPosition"]])
			streamClient.send_message(bytes(streamVerticalTopic, encoding="ascii"),[modelOutput["yPosition"]])
			mouthTopic = streamCheekIntensityTopic
		elif modelOutput["mouthTrigger"] == "Pucker Lips":
			streamClient.send_message(bytes(streamPuckerTopic, encoding="ascii"),[modelOutput["mouthIntensity"]])
			mouthTopic = streamPuckerTopic
		elif modelOutput["mouthTrigger"] == "Tongue Out":
			streamClient.send_message(bytes(streamTongueOutTopic, encoding="ascii"),[modelOutput["mouthIntensity"]])
			mouthTopic = streamTongueOutTopic


	if modelOutput["eyeIntensity"] >= eyeIntensityThreshold and modelOutput["eyeTriggerConf"] >= eyeDetectionConfidenceThreshold:
		if modelOutput["eyeTrigger"] == "Left Wink":
			streamClient.send_message(bytes(streamLeftEyeTopic, encoding="ascii"),[modelOutput["eyeIntensity"]])
			eyeTopic = streamLeftEyeTopic
		elif modelOutput["eyeTrigger"] == "Right Wink":
			streamClient.send_message(bytes(streamRightEyeTopic, encoding="ascii"),[modelOutput["eyeIntensity"]])
			eyeTopic = streamRightEyeTopic
		elif modelOutput["eyeTrigger"] == "Left Brow":
			streamClient.send_message(bytes(streamLeftBrowTopic, encoding="ascii"),[modelOutput["eyeIntensity"]])
			eyeTopic = streamLeftBrowTopic

	if isPriorEyeTopicOver(eyeTopic):
		streamClient.send_message(bytes(streamEyeTopicEndControl[0],encoding="ascii"),[0])
	if isPriorMouthTopicOver(mouthTopic):
		streamClient.send_message(bytes(streamMouthTopicEndControl[0],encoding="ascii"),[0])

def isPriorEyeTopicOver(eyeTopic):
	global streamEyeTopicEndControl
	streamEyeTopicEndControl.append(eyeTopic)
	streamEyeTopicEndControl.pop(0)
	return streamEyeTopicEndControl[0] != streamEyeTopicEndControl[1] and streamEyeTopicEndControl[1] != None


def isPriorMouthTopicOver(mouthTopic):
	global streamMouthTopicEndControl
	streamMouthTopicEndControl.append(mouthTopic)
	streamMouthTopicEndControl.pop(0)
	return streamMouthTopicEndControl[0] != streamMouthTopicEndControl[1] and streamMouthTopicEndControl[1] != None
	
def recordFrame(recordWriter,image,processedModelOuputDict):
	if captureShowBoxOnRecord:
		image = addDetectionsToImage(image,processedModelOuputDict)
	recordWriter.write(image)
	
def getWHscales(outputW,outputH):
	return outputW/float(captureWidth),outputH/float(captureHeight)
	
def projectToSquareInCircle(tonguePosition,lipPosition):
	mouthCenterPose = lipPosition[0]+lipOffset[0],lipPosition[1] + lipOffset[1]
	tongueVector = np.array(tonguePosition) - np.array(mouthCenterPose)
	degrees = np.arctan2(tongueVector[1]*(-1),tongueVector[0])+np.pi/4 # -1 for image to non-image reference
	degreesMod90 = (np.abs(degrees/(np.pi/2))%1)*np.pi/2
	enscribedSquareDistance = lipCircleRadius*np.sin(np.pi/4)/np.sin(np.pi*3/4 - degreesMod90)
	if np.linalg.norm(tongueVector) > enscribedSquareDistance:
		ratio = enscribedSquareDistance/np.linalg.norm(tongueVector)
		tongueVector = tongueVector*ratio
	horizontalDiffScaled = int(streamNumberOfPositions*(tongueVector[0] + lipCircleRadius)/(2*lipCircleRadius))
	verticalDiffScaled = int(streamNumberOfPositions*(tongueVector[1] + lipCircleRadius)/(2*lipCircleRadius))
	return horizontalDiffScaled,verticalDiffScaled

if __name__ == '__main__':
	main()