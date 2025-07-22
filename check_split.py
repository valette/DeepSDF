#!/usr/bin/env python
import argparse
import json
import math
import os
import random
import time

start = time.time()
parser = argparse.ArgumentParser( description = 'Check split file', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "split", help="JSON file containing split" )
parser.add_argument( "-f", "--fix", help="remove missing items", action="store_true" )
args = parser.parse_args()


if not os.path.exists( args.split ):
    print( "Split file does not exist: %s" % args.split )
    exit( 1 )

with open( args.split, 'r' ) as f:
    try:
        split = json.load( f )
    except json.JSONDecodeError as e:
        print( "Error decoding JSON: %s" % e )
        exit( 1 )

    directory = os.path.dirname( os.path.normpath( args.split ) )
    name = list( split.keys()) [0]
    print( "Dataset name :", name)

    items = split[ name ][ 'all' ]
    present_items = 0;
    missing_items = 0;

    new_items = []

    for item in items:
        if not os.path.exists( os.path.join( directory, "SdfSamples", name, "all", item + ".npz") ):
            print( "File does not exist: %s" % item )
            missing_items += 1
        else:
            present_items += 1
            new_items.append( item )

    print( "Present items: %d" % present_items )
    print( "Missing items: %d" % missing_items )

    if missing_items > 0:
        if args.fix:
            print( "Fixing split file..." )
            split[ name ][ 'all' ] = new_items
            with open( args.split, 'w' ) as f:
                json.dump( split, f, indent=4 )
            print( "Split file fixed." )
        else:
            print( "Use -f to fix the split file." )