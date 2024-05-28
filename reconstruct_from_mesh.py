import argparse
import generate_distance_data
import logging
import reconstruct_single
import torch
import vtk

parser = argparse.ArgumentParser( description = 'DeepSDF reconstruction from meshes', formatter_class=argparse.ArgumentDefaultsHelpFormatter )

sdf_parser = parser.add_argument_group('SDF generation options')
generate_distance_data.add_args( sdf_parser )

reconstruction_parser = parser.add_argument_group('Reconstruction options')
reconstruct_single.add_args( reconstruction_parser )

args = parser.parse_args()

reader = vtk.vtkSTLReader()
reader.SetFileName( args.mesh )
reader.Update()
mesh = reader.GetOutput()
pos, neg, scale, offset = generate_distance_data.generate( args, mesh )
print( scale )
print( offset )
data_sdf = [ torch.Tensor(pos), torch.Tensor(neg), scale, offset ]
specs, decoder = reconstruct_single.init(args)
reconstruct_single.reconstruct_mesh( "mesh", args, specs, decoder, data_sdf )
