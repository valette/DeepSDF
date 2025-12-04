#!/usr/bin/env python
import argparse
import os
import shutil
import tempfile
import time
from mesh_viewer import can_read_mesh, convert_to_ply

start = time.time()
parser = argparse.ArgumentParser( description = 'Generate data dirs', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "directory", help="directory containing meshes" )
parser.add_argument( dest= "output_dir", help="output directory" )
parser.add_argument( "--allowed", help="allowed extensions", action = 'append', default = [] )
parser.add_argument( "--depth", help="recursion depth", type = int, default = -1 )
parser.add_argument( "--to_ply", help="if used, .stl files are converted to .ply", action='store_true' )
args = parser.parse_args()
print( args )

output_dir = os.path.abspath( args.output_dir )
if not os.path.exists( output_dir ) : os.makedirs( output_dir )

for root, dirs, files in os.walk( args.directory ):
    if args.depth >= 0:
        relative = os.path.relpath( root, args.directory )
        if relative == "." : depth = 0
        else : depth = len( relative.split( os.sep ) )
        if depth > args.depth :
            print( root, "directory skipped, depth=", depth )
            continue

    for f in files:
        inputFile = os.path.abspath( os.path.join( root, f ) )
        if not can_read_mesh( inputFile ) : continue
        if len( args.allowed ) > 0 :
            allowed = False
            for ext in args.allowed :
                if inputFile.endswith( ext ) :
                    allowed = True
                    break
            if not allowed : continue
        print( "Processing", inputFile )

        arr = f.split( "." )
        newDir = os.path.join( output_dir, "_".join( ".".join( arr[ :-1 ] ).split( " " ) ) )
        if not os.path.exists( newDir ) : os.makedirs( newDir )
        if  args.to_ply and arr[1] != 'ply':
            outputFile = "_".join( os.path.join( newDir, ".".join( arr[ :-1 ] ) + ".ply" ).split( " " ) )
            convert_to_ply(inputFile, outputFile)
        else:
            outputFile = "_".join( os.path.join( newDir, ".".join( arr ) ).split( " " ) )
            shutil.copyfile( inputFile, outputFile )
        print( inputFile )
        print( newDir )

end = time.time()
print( "Done in ", int( end - start) , "seconds" )
