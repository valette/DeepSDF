#!/usr/bin/env python
import argparse
import json
import math
import os
import random
import time

start = time.time()
parser = argparse.ArgumentParser( description = 'Generate split files', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "directory", help="directory containing meshes" )
parser.add_argument( "-r", dest= "trainRatio", help="ratio of training data", type= float, default = 0.9 )
# parser.add_argument( "-ns", dest= "numberOfSurfacePoints", help="number of surface points", type= float, default = 1000 )
# parser.add_argument( "-r", dest= "dilation", help="dilation around box", type= float, default = 1 )
# parser.add_argument( "-sigma", dest= "sigma", help="noise amplitude around surface", type= float, default = 0.5 )
# parser.add_argument( "-seed", dest= "seed", help="random seed", type= int, default = 666 )
# parser.add_argument( "-normals", dest= "normals", help="add noise with normals", action="store_true" )
# parser.add_argument( dest = 'mesh', help = 'input mesh' )
args = parser.parse_args()


path = os.path.normpath( args.directory )
arr = path.split( "/" )
name = arr[ 0 ]
name2 = arr[ 1 ]

names = []

for f in os.listdir( path ) :
    meshFile = os.path.join( path, f, f + ".stl" )
    if not os.path.isfile( meshFile ) : continue
#    print( meshFile )
    names.append( f )

random.shuffle( names )
print( "Total : ", len( names ), "items" )

trainSize = math.floor( args.trainRatio * len( names ) )
s = [ "train", "test" ]
arrays = [ names[ :trainSize ], names[ trainSize: ] ]

for i in range( 2 ):
    print( s[ i ] )
    obj = {}
    obj[ name ] = {}
    obj[ name ][ name2 ] = arrays[ i ]
#    print( obj )
    fileName = name + "_" + name2 + "_" + s[ i ] + ".json"
    print( fileName )
    print( len( arrays[ i ] ), "items" )
    txt = json.dumps(obj, indent=4)
    with open( fileName, "w") as outfile : outfile.write( txt )



end = time.time()
print( "Done in ", int( end - start) , "seconts" )
