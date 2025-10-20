#!/usr/bin/env python

import argparse
import vtk

def get_readable_mesh_formats():
    return [ "stl", "ply", "obj", "vtp", "vtk" ]

def get_mesh_reader( file ):
    extension = file.split( '.' )[ -1 ]
    if extension == "stl" :
        return vtk.vtkSTLReader
    if extension == "ply" :
        return vtk.vtkPLYReader
    if extension == "obj" :
        return vtk.vtkOBJReader
    if extension == "vtp" :
        return vtk.vtkXMLPolyDataReader
    if extension == "vtk" :
        return vtk.vtkPolyDataReader
    return None

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
    parser = argparse.ArgumentParser( description = 'NPZ Points viewer', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "mesh", help = 'input mesh' )
    args = parser.parse_args()
    if not can_read_mesh( args.mesh ) :
        raise ValueError("Unsupported mesh format", args.mesh )
    mesh = read_mesh( args.mesh )
    render_mesh( mesh )




