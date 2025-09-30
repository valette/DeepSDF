import argparse
import generate_distance_data
import os
import reconstruct_single
import torch
from mesh_viewer import read_mesh, can_read_mesh

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
	dir = args.mesh
	for file in sorted( os.listdir( dir ) ):
		full_path = os.path.join( args.mesh, file )
		if not can_read_mesh( full_path ) : continue
		files.append( [ full_path, os.path.join( args.outputDir, os.path.splitext( os.path.basename( file ) )[0] ) ] )
else:
	files.append( [ args.mesh, "mesh" ] )

for mesh, output in files:
	print( "******** Mesh :", mesh )
	mesh = read_mesh( mesh )
	pos, neg, scale, offset = generate_distance_data.generate( args, mesh )
	print( scale )
	print( offset )
	data_sdf = [ torch.Tensor(pos), torch.Tensor(neg), scale, offset ]
	specs, decoder = reconstruct_single.init(args)
	reconstruct_single.reconstruct_mesh( output, args, specs, decoder, data_sdf )
	print( "Saved to", output + ".ply" );
