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
args = parser.parse_args()


path = os.path.normpath( args.directory )
arr = path.split( "/" )
name = arr[ -2 ]
name2 = arr[ -1 ]

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
