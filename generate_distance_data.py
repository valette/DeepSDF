#!/usr/bin/env python

import argparse
import math
import random
import numpy as np
# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import (
    vtkFloatArray,
    vtkPoints
)
from vtkmodules.vtkCommonDataModel import ( 
vtkPolyData,
vtkBoundingBox
)
from vtkmodules.vtkFiltersCore import (
vtkImplicitPolyDataDistance

)
from vtkmodules.vtkFiltersGeneral import(
 vtkVertexGlyphFilter,
 vtkDistancePolyDataFilter
)
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtkmodules.vtkIOGeometry import vtkSTLReader
import time

def addRandomPoints( mesh, points, numberOfPoints, dilation ):
    bounds = mesh.GetBounds()
    box = vtkBoundingBox()
    box.SetBounds( bounds )
    box.Inflate( dilation )
    max = box.GetMaxPoint();
    min = box.GetMinPoint();

    for n in range( numberOfPoints ):
        x = random.uniform( min[ 0 ], max[ 0 ] )
        y = random.uniform( min[ 1 ], max[ 1 ] )
        z = random.uniform( min[ 2 ], max[ 2 ] )
        points.InsertNextPoint( x, y , z )

def addSurfacePoints( mesh, points, numberOfPoints, sigma, useNormals ):
    nCells = mesh.GetNumberOfCells();
    meshPoints = mesh.GetPoints()
    sArea = 0
    for i in range( nCells ): sArea += mesh.GetCell( i ).ComputeArea()

    for i in range( nCells ):
        cell = mesh.GetCell( i )
        ids = cell.GetPointIds()
        area = cell.ComputeArea()
        nPoints = math.floor( 0.5 + numberOfPoints * area / sArea );
        p1 = meshPoints.GetPoint( ids.GetId( 0 ) )
        p2 = meshPoints.GetPoint( ids.GetId( 1 ) )
        p3 = meshPoints.GetPoint( ids.GetId( 2 ) )
        n = [ 0, 0, 0 ]
        v = [ 0, 0, 0 ]
        v2 = [ 0, 0, 0 ]
        v3 = [ 0, 0, 0 ]
        sigma2 = sigma / 2
        cell.ComputeNormal( p1, p2, p3, n )

        for j in range( nPoints ) :
            ok =  False
            while not ok:
                x1 = random.random()
                x2 = random.random()
                if x1 + x2 <= 1.0 : ok = True

            x3 = 1 - x1 - x2;
            r1 = random.uniform( -sigma, sigma )
            r2 = random.uniform( -sigma2, sigma2 )

            for k in range( 3 ):
                v[k] = p1[k] * x1 + p2[k] * x2 + p3[k] * x3;
                if useNormals:
                    v2[k] = v[ k ] + r1 * n[ k ]
                    v3[k] = v[ k ] + r2 * n[ k ]
                else:
                    v2[k] = v[ k ] + random.uniform( -sigma, sigma )
                    v3[k] = v[ k ] + random.uniform( -sigma2, sigma2 )

            points.InsertNextPoint( v[ 0 ], v[ 1 ], v[ 2 ] )
            points.InsertNextPoint( v2[ 0 ], v2[ 1 ], v2[ 2 ] )
            points.InsertNextPoint( v2[ 0 ], v2[ 1 ], v2[ 2 ] )

def main( args ):
    random.seed( args.seed )
    reader = vtkSTLReader()
    reader.SetFileName( args.mesh )
    reader.Update()

    mesh = reader.GetOutput()
    points = vtkPoints()
    addRandomPoints( mesh, points, args.numberOfRandomPoints, args.dilation )
    addSurfacePoints( mesh, points, args.numberOfSurfacePoints, args.sigma, args.normals )

    print( str( points.GetNumberOfPoints() ) + " points " )

    implicitPolyDataDistance = vtkImplicitPolyDataDistance()
    implicitPolyDataDistance.SetInput( mesh )
    signedDistances = vtkFloatArray()

    for pointId in range(points.GetNumberOfPoints()):
        p = points.GetPoint(pointId)
        signedDistance = implicitPolyDataDistance.EvaluateFunction(p)
        signedDistances.InsertNextValue(signedDistance)

    if args.output : writeSDFToNPZ( points, signedDistances, args.output )


    if args.display : display( mesh, points, signedDistances )

def writeSDFToNPZ( points, sdf, filename ):

    box = vtkBoundingBox()
    for i in range( points.GetNumberOfPoints() ):
        box.AddPoint( points.GetPoint( i ) )

    length = box.GetDiagonalLength();
    center = [ 0, 0, 0 ]
    box.GetCenter( center )
    pos = []
    neg = []

    for i in range( points.GetNumberOfPoints() ):
        p = points.GetPoint( i )
        s = sdf.GetValue( i )
        sample = []
        for j in range( 3 ):
            coord = ( p[ j ] - center[ j ] ) / length
            sample.append( coord );
        sample.append(s);
        arr = pos if s > 0 else neg
        arr.append( sample )

    pos = np.array( pos, dtype=np.float32 )
    neg = np.array( neg, dtype=np.float32 )
    np.savez( filename, pos = pos, neg = neg)

def display( mesh, points, signedDistances ):

    mapper = vtkPolyDataMapper()
    mapper.SetInputData( mesh )
    mapper.ScalarVisibilityOff()

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.3)
    actor.GetProperty().SetColor(1, 0, 0)

    polyData = vtkPolyData()
    polyData.SetPoints(points)
    polyData.GetPointData().SetScalars(signedDistances)

    vertexGlyphFilter = vtkVertexGlyphFilter()
    vertexGlyphFilter.SetInputData(polyData)
    vertexGlyphFilter.Update()

    signedDistanceMapper = vtkPolyDataMapper()
    signedDistanceMapper.SetInputConnection(vertexGlyphFilter.GetOutputPort())
    signedDistanceMapper.ScalarVisibilityOn()

    signedDistanceActor = vtkActor()
    signedDistanceActor.SetMapper(signedDistanceMapper)

    renderer = vtkRenderer()
    renderer.AddViewProp(actor)
    renderer.AddViewProp(signedDistanceActor)
    colors = vtkNamedColors()
    renderer.SetBackground(colors.GetColor3d('SlateGray'))

    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetWindowName('Distance cloud')

    renWinInteractor = vtkRenderWindowInteractor()
    renWinInteractor.SetRenderWindow(renderWindow)

    renderWindow.Render()
    renWinInteractor.Start()


if __name__ == '__main__':
    start = time.time()
    parser = argparse.ArgumentParser( description = 'Distances computation', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "-d", dest= "display", help="display result", action="store_true" )
    parser.add_argument( "-nr", dest= "numberOfRandomPoints", help="number of random points", type= int, default = 50000 )
    parser.add_argument( "-ns", dest= "numberOfSurfacePoints", help="number of surface points", type= float, default = 150000 )
    parser.add_argument( "-r", dest= "dilation", help="dilation around box", type= float, default = 1 )
    parser.add_argument( "-sigma", dest= "sigma", help="noise amplitude around surface", type= float, default = 0.5 )
    parser.add_argument( "-seed", dest= "seed", help="random seed", type= int, default = 666 )
    parser.add_argument( "-normals", dest= "normals", help="add noise with normals", action="store_true" )
    parser.add_argument( "-m", dest = 'mesh', help = 'input mesh', required = True )
    parser.add_argument( "-o", dest = 'output', help = 'output distance file name' )
    args = parser.parse_args()
    main( args )
    end = time.time()
    print( "Done in ", int( end - start) , "seconts" )
