import argparse
import generate_distance_data
import logging
import os
import reconstruct_single
import torch
import vtk

parser = argparse.ArgumentParser( description = 'DeepSDF reconstruction from meshes', formatter_class=argparse.ArgumentDefaultsHelpFormatter )

sdf_parser = parser.add_argument_group('SDF generation options')
generate_distance_data.add_args( sdf_parser )

reconstruction_parser = parser.add_argument_group('Reconstruction options')
reconstruct_single.add_args( reconstruction_parser )

args = parser.parse_args()

files = []

if os.path.isdir( args.mesh ):
	for file in os.listdir( args.mesh ) :
		if not file.endswith( ".stl" ) : continue
		files.append( [ os.path.join( args.mesh, file ), file[ : -4 ] ] )
else:
	files.append( [ args.mesh, "mesh" ] )

for entry in files:
	print( "******** Mesh :", entry[ 0 ] )
	reader = vtk.vtkSTLReader()
	reader.SetFileName( entry[ 0 ] )
	reader.Update()
	mesh = reader.GetOutput()
	pos, neg, scale, offset = generate_distance_data.generate( args, mesh )
	print( scale )
	print( offset )
	data_sdf = [ torch.Tensor(pos), torch.Tensor(neg), scale, offset ]
	specs, decoder = reconstruct_single.init(args)
	reconstruct_single.reconstruct_mesh( entry[ 1 ], args, specs, decoder, data_sdf )
	print( "Saved to", entry[ 1 ] + ".ply" );
