#!/usr/bin/env python

import argparse
import math
import numpy as np
import os
from pointsViewer import display
import random
import time
import vtk

def addRandomPoints( mesh, points, numberOfPoints ):

    for n in range( numberOfPoints ):
        x = random.random() - 0.5
        y = random.random() - 0.5
        z = random.random() - 0.5
        points.InsertNextPoint( x, y , z )

def addSurfacePoints( mesh, points, nCells, numberOfPoints, variance, secondVariance, useNormals ):
    meshPoints = mesh.GetPoints()
    sigma1 = math.sqrt( variance )
    sigma2 = math.sqrt( secondVariance )
    print( "Sigma1 :", sigma1, "Sigma2 :", sigma2 )

    items = list( range( nCells ) )
    weights = list( map( lambda i : mesh.GetCell( i ).ComputeArea(), items ) )
    samples = random.choices( items, weights=weights, k = math.floor( numberOfPoints / 2 ) )

    n = [ 0, 0, 0 ]
    v = [ 0, 0, 0 ]
    v2 = [ 0, 0, 0 ]
    v3 = [ 0, 0, 0 ]

    for item in samples:
        cell = mesh.GetCell( item )
        ids = cell.GetPointIds()
        area = cell.ComputeArea()
        p1 = meshPoints.GetPoint( ids.GetId( 0 ) )
        p2 = meshPoints.GetPoint( ids.GetId( 1 ) )
        p3 = meshPoints.GetPoint( ids.GetId( 2 ) )
        cell.ComputeNormal( p1, p2, p3, n )

        rnd1 = math.sqrt( random.random() )
        rnd2 = random.random()

        x1  = 1 - rnd1
        x2 = rnd1 * ( 1 - rnd2 )
        x3 = rnd2 * rnd1;

        r1 = random.gauss( 0.0, sigma1 )
        r2 = random.gauss( 0.0, sigma2 )

        for k in range( 3 ):
            v[k] = p1[k] * x1 + p2[k] * x2 + p3[k] * x3;
            if useNormals:
                v2[k] = v[ k ] + r1 * n[ k ]
                v3[k] = v[ k ] + r2 * n[ k ]
            else:
                v2[k] = v[ k ] + random.gauss( 0.0, sigma1 )
                v3[k] = v[ k ] + random.gauss( 0.0, sigma2 )

#            points.InsertNextPoint( v[ 0 ], v[ 1 ], v[ 2 ] )
        points.InsertNextPoint( v2[ 0 ], v2[ 1 ], v2[ 2 ] )
        points.InsertNextPoint( v3[ 0 ], v3[ 1 ], v3[ 2 ] )

def generate( args, mesh ):
    start = time.time()
    random.seed( args.seed )

    print( mesh.GetNumberOfCells(), "triangles before processing" )
    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetExtractionModeToLargestRegion()
    connectivity.SetInputData( mesh )
    holesFilling = vtk.vtkFillHolesFilter()
    holesFilling.SetInputConnection( connectivity.GetOutputPort() )
    holesFilling.SetHoleSize( 10 )
    normals = vtk.vtkPolyDataNormals()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.SetInputConnection( holesFilling.GetOutputPort() )
    normals.Update()
    nCells = connectivity.GetOutput().GetNumberOfCells()

    print( connectivity.GetNumberOfExtractedRegions(), "connected components" )
    print( nCells, "triangles after removing small connected components" )
    mesh = normals.GetOutput()
    print( mesh.GetNumberOfCells(), "triangles after hole filling" )

    variance = args.variance
    if args.test : variance = variance / 10
    secondVariance = variance / 10
    bounds = mesh.GetBounds()
    print( "Initial mesh bounds: ", bounds )

    if args.boxMesh:
        reader2 = vtk.vtkSTLReader()
        reader2.SetFileName( args.boxMesh )
        reader2.Update()
        bounds = reader2.GetOutput().GetBounds()
        print( "Box mesh bounds:", bounds )

    if args.box_extension:
        box_extension = args.box_extension
        bounds = list( bounds )
        extended = False
        for index in range( 3 ):
            i_max = 1 + index * 2
            i_min = index * 2
            diff = bounds[ i_max ] - bounds[ i_min ]

            if box_extension[ i_min ] > diff :
                bounds[ i_min ] -= box_extension[ i_min ] - diff
                diff = bounds[ i_max ] - bounds[ i_min ]
                extended = True

            if box_extension[ i_max ] > diff :
                bounds[ i_max ] += box_extension[ i_max ] - diff
                extended = True

        if extended : print( "Extended bounds:", bounds )


    box = vtk.vtkBoundingBox()
    box.SetBounds( bounds )
    offset = [ 0, 0, 0 ]
    box.GetCenter( offset )
    for i in range( 3 ) : offset[ i ] = - offset[ i ]
    print ( "Offset : ", offset )
    length = box.GetMaxLength()
    print( "Max length: ", length )
    scale = 1 / ( length * 1.1 )
    meshPoints = mesh.GetPoints()
    for i in range( meshPoints.GetNumberOfPoints() ):
        pt = list( meshPoints.GetPoint( i ) )
        for j in range( 3 ) : pt[ j ] = scale * ( pt[ j ] + offset[ j ] )
        meshPoints.SetPoint( i, pt )

    meshPoints.Modified()
    print( "Final mesh bounds: ", mesh.GetBounds() )

    points = vtk.vtkPoints()
    numberOfSamples = args.numberOfSamples
    numberOfNearSurfacePoints = round( args.nearRatio * numberOfSamples )
    addSurfacePoints( mesh, points, nCells, numberOfNearSurfacePoints, variance, secondVariance, args.normals )
    print( points.GetNumberOfPoints(), "near surface samples" )
    addRandomPoints( mesh, points, numberOfSamples - points.GetNumberOfPoints() )

    print( points.GetNumberOfPoints(), "samples in total " )
    box = vtk.vtkBoundingBox()
    for i in range( points.GetNumberOfPoints() ):
        box.AddPoint( points.GetPoint( i ) )

    bounds = [ 0, 0, 0, 0, 0, 0 ]
    box.GetBounds(bounds)
    print( "Sample bounds : ", bounds )
    implicitPolyDataDistance = vtk.vtkImplicitPolyDataDistance()
    implicitPolyDataDistance.SetInput( mesh )
    signedDistances = vtk.vtkFloatArray()

    pos = []
    neg = []

    for pointId in range(points.GetNumberOfPoints()):
        p = points.GetPoint(pointId)
        signedDistance = implicitPolyDataDistance.EvaluateFunction(p) * args.scale
        signedDistances.InsertNextValue(signedDistance)
        if p[ 1 ] < args.yMin : continue
        sample = []
        for j in range( 3 ): sample.append( p[ j ] );
        sample.append(signedDistance);
        arr = pos if signedDistance > 0 else neg
        arr.append( sample )

    print( "Distance range : ", signedDistances.GetRange() )
    pos = np.array( pos, dtype=np.float32 )
    neg = np.array( neg, dtype=np.float32 )
    end = time.time()
    print( "SDF values computed in", int( end - start) , "seconds" )
    if args.display : display( points, signedDistances, mesh )
    return pos, neg, scale, offset

def add_args( parser ):
    parser.add_argument( "-d", "--display", help="display result", action="store_true" )
    parser.add_argument( "-n", "--numberOfSamples", help="number of samples", type= int, default = 500000 )
    parser.add_argument( "--near", dest= "nearRatio", help="near surface sampling ratio", type = float, default = 47.0 / 50.0 )
    parser.add_argument( "--dilation", help="dilation ratio unit box", type= float, default = 0.05 )
    parser.add_argument( "-v", "--variance", dest= "variance", help="variance", type= float, default = 0.0025 )
    parser.add_argument( "-seed", help="random seed", type= int, default = 666 )
    parser.add_argument( "-s", "--scale", help="distance scale", default = 1, type = float )
    parser.add_argument( "-normals", dest= "normals", help="add noise with normals", action="store_true" )
    parser.add_argument( "-m", '--mesh', help = 'input mesh', required = True )
    parser.add_argument( "-b", '--boxMesh', help = 'input box mesh which will be used to compute bounding box' )
    parser.add_argument( "-be", '--box_extension', help = 'input box mesh will be extended to reach expected dimensions', nargs='+', type = float )
    parser.add_argument( "-t", '--test', help = 'use tighter sampling for test', action="store_true"  )
    parser.add_argument( "--ymin", dest = 'yMin', help = 'remove points with y lower than threshold', type = float, default = -1000000 )

if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Distances computation', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    add_args( parser )
    parser.add_argument( "-o", dest = 'output', help = 'output distance file name' )
    args = parser.parse_args()
    reader = vtk.vtkSTLReader()
    files = []

    if os.path.isdir( args.mesh ):
        for file in sorted( os.listdir( args.mesh ) ):
            if not file.endswith( ".stl" ) : continue
            mesh_file = os.path.join( args.mesh, file )
            output_npz = mesh_file.split( "/" ).pop()[ : -4 ] + ".npz"
            files.append( [ mesh_file , output_npz ] )
    else:
        files.append( [ args.mesh, args.output ] )

    for mesh, output in files:
        print( "Mesh :", mesh )
        reader.SetFileName( mesh )
        reader.Update()
        mesh = reader.GetOutput()
        pos, neg, scale, offset = generate( args, mesh )
        if output :
            scale = np.array( scale, dtype = np.float32 )
            offset = np.array( offset, dtype = np.float32 )
            np.savez( output, pos = pos, neg = neg, scale = scale, offset = offset )
