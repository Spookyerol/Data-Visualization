# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 18:02:26 2021

@author: PC
"""

import vtk
import numpy as np
import sys

from vtk.util.numpy_support import vtk_to_numpy
from vtk.util.numpy_support import numpy_to_vtk

def main(argv):
    reader = vtk.vtkTIFFReader()
    reader.SetFileName(argv[1]) #"elevationData.tif"
    reader.Update()
    
    textRead = vtk.vtkJPEGReader()
    textRead.SetFileName(argv[2]) #"marsTexture.jpg"
    textRead.Update()
    
    """ program settings """
    heightMapping = True
    writeFile = False
    
    """ crop out the colourmap displayed on the image """
    resize = vtk.vtkImageResize()
    resize.SetCroppingRegion(12, 3989, 150, 2211, -1, -1)
    resize.CroppingOn()
    resize.SetOutputDimensions(4000, 2211, -1)
    resize.SetInputData(reader.GetOutput())
    
    west = vtk.vtkImageResize()
    west.SetCroppingRegion(14, 1973, 151, 2110, -1, -1)
    west.CroppingOn()
    west.SetOutputDimensions(1959, 1959, -1)
    west.SetInputData(reader.GetOutput())
    
    east = vtk.vtkImageResize()
    east.SetCroppingRegion(2028, 3987, 151, 2110, -1, -1)
    east.CroppingOn()
    east.SetOutputDimensions(1959, 1959, -1)
    east.SetInputData(reader.GetOutput())
    
    normal = vtk.vtkImageNormalize()
    normal.SetInputConnection(resize.GetOutputPort())
    normalWest = vtk.vtkImageNormalize()
    normalWest.SetInputConnection(west.GetOutputPort())
    normalEast = vtk.vtkImageNormalize()
    normalEast.SetInputConnection(east.GetOutputPort())
    
    imageHSV = vtk.vtkImageRGBToHSV()
    imageHSV.SetInputConnection(normal.GetOutputPort())
    imageHSV.Update()
    westHSV = vtk.vtkImageRGBToHSV()
    westHSV.SetInputConnection(normalWest.GetOutputPort())
    westHSV.Update()
    eastHSV = vtk.vtkImageRGBToHSV()
    eastHSV.SetInputConnection(normalEast.GetOutputPort())
    eastHSV.Update()
    
    westFlipped = vtk.vtkImageFlip()
    westFlipped.SetInputConnection(westHSV.GetOutputPort())
    westFlipped.SetFilteredAxis(0)
    westFlipped.Update()
    
    eastFlipped = vtk.vtkImageFlip()
    eastFlipped.SetInputConnection(eastHSV.GetOutputPort())
    eastFlipped.SetFilteredAxis(0)
    eastFlipped.Update()
    
    rowsH, colsH, _ = eastHSV.GetOutput().GetDimensions()
    
    #print(pixels[1633119]) the index == XY
    #print(scalars)
    
    """ set up LUT in order to help visualise better """
    if (heightMapping):
        lookupTable = vtk.vtkLookupTable()
        lookupTable.SetNumberOfTableValues(22)
        lookupTable.SetTableRange (0, 255)
        lookupTable.SetRamp (0)
        lookupTable.Build()
        
        lookupTable.SetTableValue(0, 41/255, 35/255, 43/255, 1.0)
        lookupTable.SetTableValue(1, 122/255, 116/255, 144/255, 1.0)
        lookupTable.SetTableValue(2, 117/255, 133/255, 179/255, 1.0)
        lookupTable.SetTableValue(3, 119/255, 167/255, 204/255, 1.0)
        lookupTable.SetTableValue(4, 118/255, 200/255, 225/255, 1.0)
        lookupTable.SetTableValue(5, 132/255, 220/255, 180/255, 1.0)
        lookupTable.SetTableValue(6, 133/255, 214/255, 131/255, 1.0)
        lookupTable.SetTableValue(7, 170/255, 214/255, 122/255, 1.0)
        lookupTable.SetTableValue(8, 234/255, 215/255, 102/255, 1.0)
        lookupTable.SetTableValue(9, 229/255, 185/255, 99/255, 1.0)
        lookupTable.SetTableValue(10, 233/255, 164/255, 115/255, 1.0)
        lookupTable.SetTableValue(11, 228/255, 121/255, 95/255, 1.0)
        lookupTable.SetTableValue(12, 229/255, 139/255, 145/255, 1.0)
        lookupTable.SetTableValue(13, 212/255, 150/255, 158/255, 1.0)
        lookupTable.SetTableValue(14, 201/255, 139/255, 137/255, 1.0)
        lookupTable.SetTableValue(15, 181/255, 143/255, 124/255, 1.0)
        lookupTable.SetTableValue(16, 172/255, 150/255, 126/255, 1.0)
        lookupTable.SetTableValue(17, 172/255, 150/255, 133/255, 1.0)
        lookupTable.SetTableValue(18, 177/255, 162/255, 157/255, 1.0)
        lookupTable.SetTableValue(19, 196/255, 189/255, 188/255, 1.0)
        lookupTable.SetTableValue(20, 213/255, 213/255, 213/255, 1.0)
        lookupTable.SetTableValue(21, 233/255, 233/255, 233/255, 1.0)   
    else: 
        contourTable = vtk.vtkColorTransferFunction()
        contourTable.BuildFunctionFromTable(-8, 14, 3, [0,0,1,1,0,0,1,1,0])
        
    """ set up a lookupTable to provide the water table """
    waterTable = vtk.vtkColorTransferFunction()
    waterTable.BuildFunctionFromTable(0, 0, 2, [0,0,1,1,1,1])
    
    """ prepare the sphere """
    sphere = vtk.vtkSphereSource()
    sphere.SetThetaResolution(4000)
    sphere.SetPhiResolution(4000)
    sphere.SetRadius(0.9994)
    sphere.SetCenter(0, 0, 0)
    sphere.Update()
    
    sphereCoords = vtk_to_numpy(sphere.GetOutput().GetPoints().GetData())
    
    scalarsWest = vtk_to_numpy(westFlipped.GetOutput().GetPointData().GetScalars())
    scalarsEast = vtk_to_numpy(eastHSV.GetOutput().GetPointData().GetScalars())
    
    scalarsSphere = np.zeros((sphereCoords.shape[0], 3))
    
    """ line up the sphere coordinates with the scalars of the image """
    
    for i in range(sphereCoords.shape[0]):
        x = round(int((sphereCoords[i][0] + 1) * (rowsH / 2)))
        y = round(int((sphereCoords[i][1] + 1) * (colsH / 2)))
        
        if (sphereCoords[i][2] > 0):
            scalarsSphere[i] = scalarsWest[x+y*1959]
        elif (sphereCoords[i][2] < 0):
            scalarsSphere[i] = scalarsEast[x+y*1959]
        
    sphereScalars = numpy_to_vtk(np.asarray(scalarsSphere))
    sphere.GetOutput().GetPointData().SetScalars(sphereScalars)
    
    """ HSV and RGB do not perfectly map 1-1 in the red channel so we shift the HSV scale """
    
    pixelsSphere = vtk_to_numpy(sphere.GetOutput().GetPointData().GetScalars())
    
    for i in range(pixelsSphere.shape[0]):
        if(pixelsSphere[i][1] < 20):
            pixelsSphere[i][0] = pixelsSphere[i][1]
            
        pixelsSphere[i][0] = pixelsSphere[i][0] - 205
        pixelsSphere[i][0] = pixelsSphere[i][0] * -1
        
        if(pixelsSphere[i][0] < 0):
            pixelsSphere[i][0] = pixelsSphere[i][0] + 255
            pixelsSphere[i][2] = 1
            
        pixelsSphere[i][0] = ((pixelsSphere[i][0] / 255) * 22) - 8
    
    shiftedScalarsSphere = numpy_to_vtk(np.asarray(pixelsSphere))
    
    sphere.GetOutput().GetPointData().GetScalars().DeepCopy(shiftedScalarsSphere)
    
    """ write the sphere dataset into a .vtk file """
    if (writeFile):
        writer = vtk.vtkPolyDataWriter()
        writer.SetInputData(sphere.GetOutput())
        writer.SetFileName('mars.vtk')
        writer.Update()
    
    """ load in the texture for the sphere and map it to its coordinates """    
    texture = vtk.vtkTexture()
    texture.SetInputData(textRead.GetOutput())
    
    textMapper = vtk.vtkTextureMapToCylinder()
    textMapper.SetInputConnection(sphere.GetOutputPort())
    textMapper.SetPoint1(0, 1, 0)
    textMapper.SetPoint2(0, -1, 0)
    textMapper.AutomaticCylinderGenerationOff()
    textMapper.PreventSeamOff()
        
    if (heightMapping):   
        warp = vtk.vtkWarpScalar()
        warp.SetInputConnection(textMapper.GetOutputPort())
        warp.SetScaleFactor(0) #0.004
        
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(warp.GetOutputPort())
        mapper.SetLookupTable(waterTable)
        mapper.SetScalarRange(-8, 14)
    else:
        contours = vtk.vtkContourFilter()
        contours.GenerateValues(22, -8, 14)
        contours.SetInputConnection(sphere.GetOutputPort())
        
        tubes = vtk.vtkTubeFilter()
        tubes.SetRadius(0.001)
        tubes.SetVaryRadiusToVaryRadiusOff()
        tubes.SetNumberOfSides(22)
        tubes.SetInputConnection(contours.GetOutputPort())
        
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(tubes.GetOutputPort())
        mapper.SetLookupTable(contourTable)
        mapper.SetScalarRange(-8, 14)
        
        planet = vtk.vtkDataSetMapper()
        planet.SetInputConnection(textMapper.GetOutputPort())
        planet.SetLookupTable(waterTable)
        planet.SetScalarRange(-8, 14)
        
    
    if (heightMapping):
        actorSphere = vtk.vtkActor()
        actorSphere.SetMapper(mapper)
        actorSphere.SetTexture(texture)
    else:
        actorMapping = vtk.vtkActor()
        actorMapping.SetMapper(mapper)
        
        actorSphere = vtk.vtkActor()
        actorSphere.SetMapper(planet)
        actorSphere.SetTexture(texture)
    
    """ create the stuff to visualise """
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(750,750)
    interact = vtk.vtkRenderWindowInteractor()
    interact.SetRenderWindow(renWin)
    
    ren.AddActor(actorSphere)
    if(not heightMapping):
        ren.AddActor(actorMapping)
    
    ren.ResetCamera()
    ren.ResetCameraClippingRange()
    cam1 = ren.GetActiveCamera()
    cam1.Zoom(0.5)
    
    ren.SetBackground(0.5,0.6,0.7)
    interact.Initialize()
    renWin.Render()
    
    """ set up the sliders """
    if (heightMapping):
        # set up the height slider
        sliderHeightConfig = vtk.vtkSliderRepresentation2D()
        sliderHeightConfig.SetMinimumValue(0)
        sliderHeightConfig.SetMaximumValue(0.03)
        sliderHeightConfig.SetValue(warp.GetScaleFactor())
        sliderHeightConfig.SetTitleText("Height Scale")
        sliderHeightConfig.SetTitleHeight(0.02)
        sliderHeightConfig.SetLabelHeight(0.025)
        
        sliderHeightConfig.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
        sliderHeightConfig.GetPoint1Coordinate().SetValue(40, 50)
        sliderHeightConfig.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
        sliderHeightConfig.GetPoint2Coordinate().SetValue(240, 50)
        
        def vtkSliderCallbackHeight(obj, event):
            sliderRep = obj.GetRepresentation()
            pos = sliderRep.GetValue()
            warp.SetScaleFactor(pos)
        
        sliderHeight = vtk.vtkSliderWidget()
        sliderHeight.SetRepresentation(sliderHeightConfig)
        sliderHeight.SetInteractor(interact)
        sliderHeight.SetAnimationModeToAnimate()
        sliderHeight.EnabledOn()
        
        sliderHeight.AddObserver("InteractionEvent", vtkSliderCallbackHeight)
        sliderHeight.AddObserver("EndInteractionEvent", vtkSliderCallbackHeight)
    else:
        # set up the tube slider
        sliderTubeConfig = vtk.vtkSliderRepresentation2D()
        sliderTubeConfig.SetMinimumValue(0)
        sliderTubeConfig.SetMaximumValue(0.02)
        sliderTubeConfig.SetValue(0)
        sliderTubeConfig.SetTitleText("Tube Radius")
        sliderTubeConfig.SetTitleHeight(0.02)
        sliderTubeConfig.SetLabelHeight(0.025)
        
        sliderTubeConfig.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
        sliderTubeConfig.GetPoint1Coordinate().SetValue(40, 50)
        sliderTubeConfig.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
        sliderTubeConfig.GetPoint2Coordinate().SetValue(240, 50)
        
        def vtkSliderCallbackTube(obj, event):
            sliderRep = obj.GetRepresentation()
            pos = sliderRep.GetValue()
            tubes.SetRadius(pos)
        
        sliderTube = vtk.vtkSliderWidget()
        sliderTube.SetRepresentation(sliderTubeConfig)
        sliderTube.SetInteractor(interact)
        sliderTube.SetAnimationModeToAnimate()
        sliderTube.EnabledOn()
        
        sliderTube.AddObserver("InteractionEvent", vtkSliderCallbackTube)
        sliderTube.AddObserver("EndInteractionEvent", vtkSliderCallbackTube)
        
    """ Set up the water slider """
    sliderWaterConfig = vtk.vtkSliderRepresentation2D()
    sliderWaterConfig.SetMinimumValue(-8)
    sliderWaterConfig.SetMaximumValue(14)
    sliderWaterConfig.SetValue(0)
    sliderWaterConfig.SetTitleText("Water Level")
    sliderWaterConfig.SetTitleHeight(0.02)
    sliderWaterConfig.SetLabelHeight(0.025)
    
    sliderWaterConfig.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
    sliderWaterConfig.GetPoint1Coordinate().SetValue(280, 50)
    sliderWaterConfig.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
    sliderWaterConfig.GetPoint2Coordinate().SetValue(480, 50)
    
    def vtkSliderCallbackWater(obj, event):
        sliderRep = obj.GetRepresentation()
        pos = sliderRep.GetValue()
        waterTable.BuildFunctionFromTable(pos, pos, 2, [0,0,1,1,1,1])
    
    sliderWater = vtk.vtkSliderWidget()
    sliderWater.SetRepresentation(sliderWaterConfig)
    sliderWater.SetInteractor(interact)
    sliderWater.SetAnimationModeToAnimate()
    sliderWater.SetNumberOfAnimationSteps(22)
    sliderWater.EnabledOn()
    
    sliderWater.AddObserver("InteractionEvent", vtkSliderCallbackWater)
    sliderWater.AddObserver("EndInteractionEvent", vtkSliderCallbackWater)
        
    interact.Start()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
