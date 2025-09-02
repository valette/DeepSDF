#!/usr/bin/env python
import argparse
import json
import os

git_dir = os.path.dirname( os.path.realpath(__file__) )
join = os.path.join
cwd = os.getcwd()

parser = argparse.ArgumentParser( description = 'Merge datasets', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "-i", "--input", action= "append", default = [], help="input dataset" )
parser.add_argument( "-o", "--output", help="output dataset" )
args = parser.parse_args()

output_dir = os.path.realpath( args.output )
#make output directory
output_dataset_name = output_dir.split( "/" ).pop()
print( "Output dataset name: " + output_dataset_name )
output_meshes_dir = join( output_dir, "all" )
if not os.path.exists( output_meshes_dir ): os.makedirs( output_meshes_dir )
sdf_dir = join( output_dir, "SdfSamples", output_dataset_name, "all" )
if not os.path.exists( sdf_dir ): os.makedirs( sdf_dir )

for set in [ "train", "test" ]:

    output_data = { output_dataset_name : { "all" : [] } }

    for dir in args.input:
        dir = os.path.realpath( dir )
        if not os.path.exists( dir ):
            print( "Error! : input directory does not exist: " + dir )
            exit( 1 )

        data_name = dir.split( "/" ).pop()
        split = join( dir, data_name + "_all_" + set + ".json" )
        if ( not os.path.exists( split ) ):
            print( "Error! : split does not exist: " + split )
            exit( 1 )

        if not os.path.exists( join( dir, "all" ) ):
            print( "Error! : meshes directory does not exist: " + join( dir, "all" ) )
            exit( 1 )

        print( "Merging dataset: " + dir )

        #read split
        with open( split, 'r' ) as f:
            data = json.load(f)
            print( data )
            for name in data[ data_name ][ "all" ]:
                print( "   processing: " + name )
                output_data[ output_dataset_name ][ "all" ].append( name )
                #copy mesh
                input_mesh_dir = join( dir, "all", name )
                if not os.path.exists( input_mesh_dir ):
                    print( "Error! : mesh directory does not exist: " + input_mesh_dir )
                    exit( 1 )

                # create symlink to mesh directory
                output_mesh_dir = join( output_meshes_dir, name )
                if os.path.exists( output_mesh_dir ):
                    print( "Error! : mesh directory already exists (name conflict?): " + output_mesh_dir )
                    exit( 1 )
                os.symlink( input_mesh_dir, output_mesh_dir )

                #symlink sdf samples
                input_sdf = join( dir, "SdfSamples", data_name, "all", name + ".npz" )
                if not os.path.exists( input_sdf ):
                    print( "Error! : sdf file does not exist: " + input_sdf )
                    exit( 1 )

                output_sdf = join( sdf_dir, name + ".npz" )
                if os.path.exists( output_sdf ):
                    print( "Error! : sdf file already exists (name conflict?): " + output_sdf )
                    exit( 1 )

                os.symlink( input_sdf, output_sdf )

    #write output split
    with open( join( output_dir, output_dataset_name + "_all_" + set + ".json" ), 'w') as json_file:
        json.dump( output_data, json_file, indent=4)

