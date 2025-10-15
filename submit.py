#!/usr/bin/env python
import argparse
import getpass
import json
import os
import sys

join = os.path.join
user = getpass.getuser()
name = "DeepSDF"
jean_zay = 'WORK' in os.environ
home_dir = os.environ[ 'WORK' if jean_zay else 'HOME' ]
git_dir = os.path.dirname( os.path.realpath(__file__) )


parser = argparse.ArgumentParser( description = 'train DeepSDF via qsub or slurm', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "-d", "--dataset", help = "shortcut to set Dataset directory, training set and test set" )
parser.add_argument( "-g", "--go", help = "really submit job", action="store_true" )
parser.add_argument( "--write", help = "only write job files without submitting", action="store_true" )
parser.add_argument( "-n", "--nodes", help = "qsub nodes", default = "1" )
parser.add_argument( "--gpu", help = "gpu type", default = "24" )
parser.add_argument( "-s", "--specs",  dest = 'specs', help = "specs file", required = True )
parser.add_argument( "-c", "--config", metavar=('parameter', 'value'), action='append', nargs=2, help = "specs parameters", default = [] )
parser.add_argument( "-r", "--job_root", help = "default root job dir", default = join( home_dir, name ) )
parser.add_argument( "--resolution", help = "reconstruction resolution", type = int, default = 256 )
parser.add_argument( "-l", "--supplementary_lines", action='append', help = "supplementary script lines", default = [] )
parser.add_argument( "-u", "--user"  )
parser.add_argument( "-w", "--walltime", help = "job wall time (hours)", type = int, default = 20 )
args = parser.parse_args()

if jean_zay and not args.user: raise TypeError ( "Jean Zay : add user name with --user option" )
if args.user : user = args.user

trainExec = os.path.join( git_dir, "train_deep_sdf.py" )
reconstructExec = os.path.join( git_dir, "reconstruct.py" )
pth2csvExec = os.path.join( git_dir, "pth2csv.py" )
job = ""
job_root = os.path.abspath( args.job_root )
if not os.path.exists( job_root ): os.mkdir( job_root )
max_job_id = 0

for dir in os.listdir( job_root ) :
    if not os.path.isdir( join( job_root, dir) ) : continue
    try:
        max_job_id = max( max_job_id, int( dir ) )
    except:
        continue

job_id = str( max_job_id + 1 )
job_path = join( job_root, job_id )
with open( args.specs, 'r' ) as openfile:
	specs = json.load( openfile )

if args.dataset:
    if not os.path.exists( args.dataset ):
          print( "Error! : dataset directory does not exist: " + args.dataset )
          exit( 1 )
    dataset_dir = args.dataset
    data_name = os.path.basename( os.path.normpath( dataset_dir ) )
    args.config.append( ( "DataSource", dataset_dir ) )
    train_split = os.path.join( dataset_dir, data_name + "_all_train.json" )
    if ( not os.path.exists( train_split ) ):
        print( "Error! : train split does not exist: " + train_split )
        exit( 1 )

    args.config.append( ( "TrainSplit", train_split ) )
    test_split = os.path.join( dataset_dir, data_name + "_all_test.json" )
    if ( not os.path.exists( test_split ) ):
        print( "Error! : test split does not exist: " + test_split )
        exit( 1 )
    args.config.append( ( "TestSplit", test_split ) )

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

if jean_zay:
	add( "#SBATCH --job-name=" + name + "-" + job_id )
	add( "#SBATCH --mail-type=ALL" )
	add( "#SBATCH --mail-user=" + user + "@creatis.insa-lyon.fr" )
	if args.walltime > 20 : queue = "t4"
	else : queue = "t3"
	add( "#SBATCH --qos=qos_gpu-" + queue + "             # t4 : 100h max, t3 : 20h max (default)" )
	add( "#SBATCH --nodes=1                    # Run all processes on a single node	" )
	add( "#SBATCH --ntasks=1                   # Run a single task" )
	add( "#SBATCH --gres=gpu:1                 # number of GPUs" )
	add( "#SBATCH --constraint v100-32g" )
	add( "#SBATCH --cpus-per-task=10           # Number of CPU cores per task" )
	add( "#SBATCH --hint=nomultithread         # hyperthreading is deactivated" )
	add( "#SBATCH --time=" + str( args.walltime ) + ":00:00              # maximum execution time requested (HH:MM:SS) " )
	add( "#SBATCH --output=" + join( job_path, "log.out") )
	add( "#SBATCH --error=" + join( job_path, "log.out") )
	add( "module purge" )
	add( "module load pytorch-gpu/py3/2.5.0" )
	add( "module load git" )

else:
	add( "#PBS -l walltime=5000:00:00" )
	add( "#PBS -N " + name + "-" + job_id)
	add( "#PBS -q gpu" )
	add( "#PBS -l nodes=" + args.nodes + ":ppn=10:gpus=1:gpu" + str( args.gpu )  )
	add( "#PBS -l mem=30gb" )
	add( "#PBS -o " + join( job_path, "log.out" ) )
	add( "#PBS -e " + join( job_path, "log.err" ) )
	add( "#PBS -m ae" )
	add( "#PBS -M " + user + "@creatis.insa-lyon.fr" )
	add( "hostname" )
	add( "source " + os.path.join( home_dir, "anaconda3/etc/profile.d/conda.sh" ) )
	add( "conda activate DeepSDF" )


add( "cd " + job_path )
for line in args.supplementary_lines: add( line )

print( "job.pbs : " )
print( job )

if not args.go and not args.write:
    print( "Job neither written nor submitted. Relaunch with option --write to only write or --go to write and submit" )
    exit( 0 )

os.mkdir( job_path )

def writeFile( filePath, content ) :
    File = open( filePath, "w" )
    File.write( content )
    File.close()

job_file = join ( job_path, "job." + ( "slurm" if jean_zay else "pbs" ) )
writeFile( job_file, job )

specsFile = join ( job_path, "specs.json" )
with open( specsFile, "w") as outFile : outFile.write( specsTxt )
print( "job file " + job_file + " written" )

if not args.go:
	print( "Job written but not submitted" )
	exit( 0 )

os.system( ( "sbatch" if jean_zay else "qsub" ) + " " + job_file )

print( "job file " + job_file + " submitted" )
