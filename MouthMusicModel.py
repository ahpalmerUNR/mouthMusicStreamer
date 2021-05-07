# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2020-12-21 14:38:59
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-05-06 23:10:20
import torch

class MouthMusicMouthModel(torch.nn.Module):
	def __init__(self):
		super(MouthMusicMouthModel,self).__init__()
		self.conv1 = torch.nn.Conv2d(3,62,7,stride=2,padding=3,bias=False)
		self.batch1 = torch.nn.BatchNorm2d(62)
		self.relu = torch.nn.ReLU(inplace=True)
		self.maxPool1 = torch.nn.MaxPool2d(3,2,1,1)
		self.conv2 = torch.nn.Conv2d(62,120,7,stride=2,padding=3,bias=False)
		self.batch2 = torch.nn.BatchNorm2d(120)
		self.conv3 = torch.nn.Conv2d(120,120,7,stride=2,padding=3,bias=False)
		self.batch3 = torch.nn.BatchNorm2d(120)
		self.maxPool2 = torch.nn.MaxPool2d(3,1,1,1)
		self.conv4 = torch.nn.Conv2d(120,120,7,stride=1,padding=3,bias=False)
		self.batch4 = torch.nn.BatchNorm2d(120)
		self.conv5 = torch.nn.Conv2d(120,120,7,stride=1,padding=3,bias=False)
		self.batch5 = torch.nn.BatchNorm2d(120)
		self.conv6 = torch.nn.Conv2d(120,30,7,stride=2,padding=3,bias=False)
		self.conv7 = torch.nn.Conv2d(30,12,1)
		self.sigmoid = torch.nn.Sigmoid()

	def forward(self,x):
		out = self.relu(self.batch1(self.conv1(x)))
		out = self.maxPool1(out)
		out = self.relu(self.batch2(self.conv2(out)))
		out = self.batch3(self.conv3(out))
		out = self.maxPool2(out)
		out = self.relu(self.batch4(self.conv4(out)))
		out = self.relu(self.batch5(self.conv5(out)))
		out = self.relu(self.conv6(out))
		out = self.sigmoid(self.conv7(out))
		return out
		
class MouthMusicEyeModel(torch.nn.Module):
	def __init__(self):
		super(MouthMusicEyeModel,self).__init__()
		self.conv1 = torch.nn.Conv2d(3,64,7,stride=2,padding=3,bias=False)
		self.batch1 = torch.nn.BatchNorm2d(64)
		self.relu = torch.nn.ReLU(inplace=True)
		self.maxPool1 = torch.nn.MaxPool2d(3,2,1,1)
		self.conv2 = torch.nn.Conv2d(64,120,7,stride=2,padding=3,bias=False)
		self.batch2 = torch.nn.BatchNorm2d(120)
		self.conv3 = torch.nn.Conv2d(120,120,7,stride=2,padding=3,bias=False)
		self.batch3 = torch.nn.BatchNorm2d(120)
		self.maxPool2 = torch.nn.MaxPool2d(3,1,1,1)
		self.conv7 = torch.nn.Conv2d(120,16,1)
		self.sigmoid = torch.nn.Sigmoid()

	def forward(self,x):
		out = self.relu(self.batch1(self.conv1(x)))
		out = self.maxPool1(out)
		out = self.relu(self.batch2(self.conv2(out)))
		out = self.batch3(self.conv3(out))
		out = self.maxPool2(out)
		out = self.sigmoid(self.conv7(out))
		return out
	
def loadModelMouth(directory,nameRoot):
	modelMouth = MouthMusicMouthModel()
	modelMouth.load_state_dict(torch.load(directory+"mouth_"+nameRoot, map_location="cpu"))
	return modelMouth

def loadModelEyes(directory,nameRoot):
	modelEyes = MouthMusicEyeModel()
	modelEyes.load_state_dict(torch.load(directory+"eye_"+nameRoot, map_location="cpu"))
	return modelEyes

def loadModel(directory,nameRoot):
	eyeModel = loadModelEyes(directory,nameRoot)
	mouthModel = loadModelMouth(directory,nameRoot)
	return mouthModel,eyeModel