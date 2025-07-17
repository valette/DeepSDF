#!/usr/bin/env python

import argparse
import json
import os


git_dir = os.path.dirname( os.path.realpath(__file__) )
join = os.path.join
cwd = os.getcwd()

parser = argparse.ArgumentParser( description = 'Generate full dataset', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "input_directory", help="input directory" )
parser.add_argument( "output_directory", help="output directory" )
parser.add_argument( "--SDF_options", help="SDF computation options" )
parser.add_argument( "--split_options", help="split generation options" )
parser.add_argument( "-s", "--step_start", help="start step in the process", choices = [ 0, 1, 2 ], default=0, type=int )
parser.add_argument( "-p", "--processes", help="number of processes for SDF computation", default
= os.cpu_count(), type = int )
args = parser.parse_args()

start = args.step_start

input_dir = os.path.realpath( args.input_directory )
output_dir = os.path.realpath( args.output_directory )
out_meshes_dir = join( output_dir, "all" )

if start <= 0:
    os.system( f"python {join( git_dir, "generate_data_dirs.py" )} {input_dir} {out_meshes_dir}" )

if start <= 1:
    os.chdir(output_dir)
    split_args = [ "python", join( git_dir, "generate_splits.py" ), out_meshes_dir ]
    if args.split_options : split_args.extend( args.split_options.split( " " ) )
    os.system( " ".join( split_args ) )
    os.chdir(cwd)

if start <= 2:
    data_name = output_dir.split( "/" ).pop()
    test_split = join( output_dir, data_name + "_all_test.json" )
    train_split = join( output_dir, data_name + "_all_train.json" )

    sdf_args = [ "python", join( git_dir, "preprocess_data.py" ), "-d", output_dir, "-s", output_dir, "--preprocessMeshPath", join( git_dir, "generate_distance_data.py" ), "--threads", str( args.processes ) ]
    if args.SDF_options : sdf_args.extend( [ "--SDF_options", "'" + args.SDF_options + "'" ] )
    sdf_args.extend( [ "--split", test_split ] )
    print( " ".join( sdf_args ) )
    os.system( " ".join( sdf_args ) )

    sdf_args[ -1 ] = train_split
    sdf_args.extend( [ "--test" ] )
    os.system( " ".join( sdf_args ) )

with open( join( output_dir, "generate_settings.json" ), 'w') as json_file:
    json.dump( vars(args), json_file, indent=4 )
