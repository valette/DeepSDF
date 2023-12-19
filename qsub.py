#!/usr/bin/env python
import argparse
import getpass
import json
import os
import sys

join = os.path.join
user = getpass.getuser()
homeDir = os.environ['HOME']
gitDir = os.path.dirname( os.path.realpath(__file__) )
name = "DeepSDF"

parser = argparse.ArgumentParser( description = 'train DeepSDF via qsub', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "-d", "--dry", dest = 'dryRun', help = "dry run", default = False, action="store_true" )
parser.add_argument( "-s", "--specs",  dest = 'specs', help = "specs file", required = True )
parser.add_argument( "-c", "--config", metavar=('parameter', 'value'), action='append', nargs=2, help = "specs parameters", default = [] )

args = parser.parse_args()
trainExec = os.path.join( gitDir, "train_deep_sdf.py" )
reconstructExec = os.path.join( gitDir, "reconstruct.py" )
job = ""
jobRoot = join( homeDir, name )
maxJobId = 0

for dir in os.listdir( jobRoot ) :
    if not os.path.isdir( join( jobRoot, dir) ) : continue
    try:
        maxJobId = max( maxJobId, int( dir ) )
    except:
        continue

jobId = str( maxJobId + 1 )
jobPath = join( jobRoot, jobId )

with open( args.specs, 'r' ) as openfile: 
	specs = json.load( openfile )

for key, value in args.config:
	if not key in specs:
		print( "Error! : " + key + " is not a spec config key" )
		exit( 1 )
	if not isinstance( specs[ key ], str ) :
		value = json.loads( value )
	specs[ key ] = value

print( "specs.json:" )
specsTxt = json.dumps( specs, indent = 4 )
print( specsTxt )

def add( line ) :
    global job
    job += line + "\n"

add( "#!/bin/sh" )
add( "#Command to reproduce this job: " + " ".join( sys.argv ) )
add( "#PBS -l walltime=5000:00:00" )
add( "#PBS -N " + name + "-" + jobId)
add( "#PBS -q gpu" )
add( "#PBS -l nodes=1:ppn=6:gpus=1:gpu24" )
add( "#PBS -l mem=30gb" )
add( "#PBS -o " + join( jobPath, "log.out" ) )
add( "#PBS -e " + join( jobPath, "log.err" ) )
add( "#PBS -m ae" )
add( "#PBS -M " + user + "@creatis.insa-lyon.fr" )
add( "hostname" )
add( "source /home/valette/anaconda3/etc/profile.d/conda.sh" )
add( "conda activate DeepSDF" )
add( "cd " + jobPath )
add( "python " + trainExec + " -e ./" )
add( "python " + reconstructExec + " -e ./ --data " + specs[ "DataSource" ] + " --split " + specs[ "TestSplit" ] )

print( "job.pbs : " )
print( job )

if args.dryRun :
    print( "Dry run : job not submitted" )
    exit( 0 )

os.mkdir( jobPath )

def writeFile( filePath, content ) :
    File = open( filePath, "w" )
    File.write( content )
    File.close()

jobPBSFile = join ( jobPath, "job.pbs" )
writeFile( jobPBSFile, job )

specsFile = join ( jobPath, "specs.json" )
with open( specsFile, "w") as outFile : outFile.write( specsTxt )

os.system( "qsub " + jobPBSFile )
print( "job file " + jobPBSFile + " submitted" )
