#!/usr/bin/env python
import argparse
import numpy as np
import os
import pandas as pd
import time
import torch

start = time.time()
parser = argparse.ArgumentParser( description = 'Convert pth codes to csv', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( dest= "directory", help="directory containing codes" )
parser.add_argument( dest= "outputDir", default = "./", help="output directory" )
args = parser.parse_args()

if not os.path.exists( args.outputDir ) : os.makedirs( args.outputDir )

for root, dirs, files in os.walk( args.directory ):
    for f in files:
        if not f.endswith( ".pth" ) : continue
        inputFile = os.path.join( root, f )
        print( inputFile )
        outputFile = os.path.join(  args.outputDir, f )
        outputFile = os.path.splitext( outputFile )[0]+".csv"
        print( outputFile )
        code = torch.load( inputFile, map_location='cpu' ).squeeze().detach().numpy()
        print( code )
        np.savetxt( outputFile, code, fmt="%f", newline=',' )
#        pd.DataFrame( code ).to_csv( outputFile, index = False )


end = time.time()
print( "Done in ", int( end - start) , "seconds" )
