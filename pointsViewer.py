#!/usr/bin/env python

import argparse
import math
import numpy as np
import random
import time
import vtk

def main( args ):
    print( "Reading : ", args.pointsFile )
    data = np.load( args.pointsFile )
    print( data[ "scale" ])
    if args.sign:
        pts = data[ args.sign ]
    else:
        pts = np.concatenate( ( data[ "pos" ], data[ "neg" ] ) )

    scale = 1
    if "scale" in data :
        scale = data[ "scale" ]
        print( "Scale : ", scale )
        pts = pts / scale
    if "offset" in data :
        offset = data[ "offset" ]
        print( "Offset : ", offset )
        offset = np.append( offset, 0 )
        pts = pts - offset

    points = vtk.vtkPoints()
    signedDistances = vtk.vtkFloatArray()
    for pt in pts:
        points.InsertNextPoint( pt[  : 3 ] )
        signedDistances.InsertNextValue( pt[ 3 ] * scale )

    print( points.GetNumberOfPoints(), "samples" )

    mesh = None

    if args.mesh :
        print( "Loading mesh : ", args.mesh )
        reader = vtk.vtkSTLReader()
        reader.SetFileName( args.mesh )
        reader.Update()
        mesh = reader.GetOutput()

    display( points, signedDistances, mesh, args.meshColor, args.meshOpacity, scale = args.scale )

def display( points, signedDistances, mesh = None, color = [ 1, 0, 0 ], opacity = 0.3, scale = 1 ):

    renderer = vtk.vtkRenderer()

    if mesh:
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData( mesh )
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity( opacity )
        actor.GetProperty().SetColor( color )
        renderer.AddViewProp(actor)

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    for i in range( signedDistances.GetNumberOfValues() ):
        signedDistances.SetValue( i, signedDistances.GetValue( i ) * scale )
    polyData.GetPointData().SetScalars(signedDistances)

    vertexGlyphFilter = vtk.vtkVertexGlyphFilter()
    vertexGlyphFilter.SetInputData(polyData)
    vertexGlyphFilter.Update()

    signedDistanceMapper = vtk.vtkPolyDataMapper()
    signedDistanceMapper.SetInputConnection(vertexGlyphFilter.GetOutputPort())
    signedDistanceMapper.ScalarVisibilityOn()

    signedDistanceActor = vtk.vtkActor()
    signedDistanceActor.SetMapper(signedDistanceMapper)

    renderer.AddViewProp(signedDistanceActor)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer( renderer )
    renderWindow.SetWindowName( 'Distance cloud' )

    renWinInteractor = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    renWinInteractor.SetInteractorStyle( style )
    renWinInteractor.SetRenderWindow( renderWindow )

    renderWindow.Render()
    renWinInteractor.Start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'NPZ Points viewer', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "-d", dest= "display", help="display result", action="store_true" )
    parser.add_argument( dest = 'pointsFile', help = 'input points' )
    parser.add_argument( "-m", "--mesh", help = 'input mesh' )
    parser.add_argument( "-c", "--meshColor", type = float, nargs = 3, default = [ 1, 0, 0 ], help = 'mesh color' )
    parser.add_argument( "-o", "--meshOpacity", type = float, default = 0.3, help = 'mesh opacity' )
    parser.add_argument( "-s", "--scale", dest= "scale", help="distance scale", default = 1, type = float )
    parser.add_argument( "--sign", help="display only positive or negative distance samples", choices={"pos", "neg"} )
    args = parser.parse_args()
    main( args )
