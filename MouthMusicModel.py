# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2020-12-21 14:38:59
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-01-28 21:49:58
import torch

class MouthMusicModel(torch.nn.Module):
	def __init__(self):
		super(MouthMusicModel,self).__init__()
		self.conv1 = torch.nn.Conv2d(3,30,7,stride=2,padding=3,bias=False)
		self.batch1 = torch.nn.BatchNorm2d(30)
		self.relu = torch.nn.ReLU(inplace=True)
		self.maxPool1 = torch.nn.MaxPool2d(3,2,1,1)
		self.conv2 = torch.nn.Conv2d(30,60,7,stride=2,padding=3,bias=False)
		self.batch2 = torch.nn.BatchNorm2d(60)
		self.conv3 = torch.nn.Conv2d(60,60,7,stride=2,padding=3,bias=False)
		self.batch3 = torch.nn.BatchNorm2d(60)
		self.conv4 = torch.nn.Conv2d(60,30,7,stride=2,padding=3,bias=False)
		self.conv5 = torch.nn.Conv2d(30,10,1)
		self.sigmoid = torch.nn.Sigmoid()

	def forward(self,x):
		x = self.relu(self.batch1(self.conv1(x[0])))
		x = self.maxPool1(x)
		x = self.relu(self.batch2(self.conv2(x)))
		x = self.batch3(self.conv3(x))
		x = self.relu(self.conv4(x))
		x = self.sigmoid(self.conv5(x))
		return x
	
def loadModel(directory,name):
	model = MouthMusicModel()
	model.load_state_dict(torch.load(directory+name, map_location="cpu",),strict=False)
	return model