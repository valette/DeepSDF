#!/usr/bin/env python

import argparse
import vtk

mesh_formats = {
    'stl' : vtk.vtkSTLReader,
    'ply' : vtk.vtkPLYReader,
    'obj' : vtk.vtkOBJReader,
    'vtp' : vtk.vtkXMLPolyDataReader,
    'vtk' : vtk.vtkPolyDataReader
}

def get_readable_mesh_formats():
    return mesh_formats.keys()

def get_mesh_reader( file ):
    return mesh_formats.get( file.split( '.' )[ -1 ], None )

def read_mesh( file ):
    reader_class = get_mesh_reader( file )
    if reader_class is None : raise ValueError("Unsupported mesh format", file )
    reader = reader_class()
    reader.SetFileName( file )
    reader.Update()
    return reader.GetOutput()

def can_read_mesh( file ):
    reader_class = get_mesh_reader( file )
    return reader_class is not None

def convert_to_ply( inputFile , outputFile ):
    mesh = read_mesh( inputFile )
    writer = vtk.vtkPLYWriter()
    writer.SetInputData( mesh )
    writer.SetFileName( outputFile )
    writer.Update()

def render_mesh( mesh ) :
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData( mesh )
    actor = vtk.vtkActor()
    actor.SetMapper( mapper )
    window = vtk.vtkRenderWindow()
    renderer = vtk.vtkRenderer()
    window.AddRenderer( renderer )
    interactor = vtk.vtkRenderWindowInteractor()
    # set trackball style
    style = vtk.vtkInteractorStyleTrackballCamera()
    interactor.SetInteractorStyle( style )
    interactor.SetRenderWindow( window )
    renderer.AddViewProp( actor )

    renderer.Render()
    interactor.Start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Mesh viewer', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "mesh", help = 'input mesh' )
    args = parser.parse_args()
    mesh = read_mesh( args.mesh )
    render_mesh( mesh )




