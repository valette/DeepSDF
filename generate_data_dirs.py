#!/usr/bin/env python
import argparse
import os
import shutil
import time

start = time.time()
parser = argparse.ArgumentParser( description = 'Generate data dirs', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "directory", help="directory containing meshes" )
parser.add_argument( dest= "outputDir", help="output directory" )
# parser.add_argument( "-ns", dest= "numberOfSurfacePoints", help="number of surface points", type= float, default = 1000 )
# parser.add_argument( "-r", dest= "dilation", help="dilation around box", type= float, default = 1 )
# parser.add_argument( "-sigma", dest= "sigma", help="noise amplitude around surface", type= float, default = 0.5 )
# parser.add_argument( "-seed", dest= "seed", help="random seed", type= int, default = 666 )
# parser.add_argument( "-normals", dest= "normals", help="add noise with normals", action="store_true" )
# parser.add_argument( dest = 'mesh', help = 'input mesh' )
args = parser.parse_args()

if not os.path.exists( args.outputDir ) : os.makedirs( args.outputDir )

for root, dirs, files in os.walk( args.directory ):
    for f in files:
        if not f.endswith( ".stl" ) : continue
        arr = f.split( "." )
        #print(os.path.join(root, f))
        newDir = os.path.join( args.outputDir, "_".join( ".".join( arr[ :-1 ] ).split( " " ) ) )
        if not os.path.exists( newDir ) : os.makedirs( newDir )
        inputFile = os.path.join( root, f )
        outputFile = "_".join( os.path.join( newDir, f ).split( " " ) )
        shutil.copyfile( inputFile, outputFile )
        print( inputFile )
        print( newDir )

end = time.time()
print( "Done in ", int( end - start) , "seconds" )
