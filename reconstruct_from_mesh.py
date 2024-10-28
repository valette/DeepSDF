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
reconstruction_parser.add_argument( '--outputDir', help = 'Output directory', default = "./" )

args = parser.parse_args()

files = []
if not os.path.exists( args.outputDir ) : os.mkdir( args.outputDir )

if os.path.isdir( args.mesh ):
	for file in sorted( os.listdir( args.mesh ) ):
		if not file.endswith( ".stl" ) : continue
		files.append( [ os.path.join( args.mesh, file ), os.path.join( args.outputDir, file[ : -4 ] ) ] )
else:
	files.append( [ args.mesh, "mesh" ] )

for mesh, output in files:
	print( "******** Mesh :", mesh )
	reader = vtk.vtkSTLReader()
	reader.SetFileName( mesh )
	reader.Update()
	mesh = reader.GetOutput()
	pos, neg, scale, offset = generate_distance_data.generate( args, mesh )
	print( scale )
	print( offset )
	data_sdf = [ torch.Tensor(pos), torch.Tensor(neg), scale, offset ]
	specs, decoder = reconstruct_single.init(args)
	reconstruct_single.reconstruct_mesh( output, args, specs, decoder, data_sdf )
	print( "Saved to", output + ".ply" );
