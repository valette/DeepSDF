#!/usr/bin/env python
import argparse
import os
import shutil
import tempfile
import time

start = time.time()
parser = argparse.ArgumentParser( description = 'Generate data dirs', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "directory", help="directory containing meshes" )
parser.add_argument( dest= "output_dir", help="output directory" )
parser.add_argument( "--mesh2STL", dest= "mesh2STL", help="path to mesh2STl converter" )
args = parser.parse_args()

output_dir = os.path.abspath( args.output_dir )
if not os.path.exists( output_dir ) : os.makedirs( output_dir )

for root, dirs, files in os.walk( args.directory ):
    for f in files:
        inputFile = os.path.abspath( os.path.join( root, f ) )
        for ext in [ ".ply", ".obj", ".vtk" ] :
            if not f.endswith( ext ) : continue
            if not args.mesh2STL:
                print( "Warning : no mesh2STL path provided, cannot convert", inputFile )
                continue
            temp_dir = tempfile.TemporaryDirectory()
            print( "Converting ", inputFile )
            os.chdir( temp_dir.name )
            os.system( args.mesh2STL + " " + '"' + inputFile + '"')
            inputFile = os.path.abspath( os.path.join( temp_dir.name, "mesh.stl" ) )

        extension_OK = False
        for ext in [ "stl", "vtp" ] :
            if inputFile.endswith( "." + ext ) :
                extension_OK = True
                extension = ext
        if not extension_OK : continue
        arr = f.split( "." )
        arr.pop()
        arr.append( extension )
        newDir = os.path.join( output_dir, "_".join( ".".join( arr[ :-1 ] ).split( " " ) ) )
        if not os.path.exists( newDir ) : os.makedirs( newDir )
        outputFile = "_".join( os.path.join( newDir, ".".join( arr ) ).split( " " ) )
        shutil.copyfile( inputFile, outputFile )
        print( inputFile )
        print( newDir )

end = time.time()
print( "Done in ", int( end - start) , "seconds" )
