#!/usr/bin/env python
import argparse
import csv
import getpass
import json
import os
from tabulate import tabulate
from tqdm import tqdm

def find_parameter_holder( cfg, parameter ):
    if type( cfg ) is not dict : return None

    holder = current_config = cfg
    found=True
    for parameter in parameter.split( "." ):
        if parameter in current_config:
            holder = current_config
            current_config = current_config[ parameter ]
        else:
            found=False
            break

    if found: return holder

    for entry in cfg:
        target = find_parameter_holder( cfg[ entry ], parameter )
        if target: return target

    return None

def get_parameter( cfg, parameter ):
    holder = find_parameter_holder( cfg, parameter )
    if holder == None : return None
    else : return holder[ parameter.split( "." ).pop() ]

jean_zay = 'WORK' in os.environ
join = os.path.join
home_dir = os.environ[ 'WORK' if jean_zay else 'HOME' ]
print( home_dir )
gitDir = os.path.dirname( os.path.realpath(__file__) )

to_hide= [ "-g" ]

possible_values = [  ]

parser = argparse.ArgumentParser( description = 'leaderboard', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "-f", "--filter", help = "Filter jobs" )
parser.add_argument( "-fv", "--filter_value",  metavar=('parameter', 'value'), nargs=2, help = "Filter jobs by parameter value. Example :  grid_resolution 64" )
parser.add_argument( "-s", "--sort", help = "sorting field" )
parser.add_argument( "-csv", help = "write results to leaderboard.csv file", action = "store_true" )
parser.add_argument( "-l", "--job_args_length", help = "maximum display length for job args", type = int, default = 30 )
parser.add_argument( "-lgpu", "--list_gpus", help = "list available machines and their respective gpu", action = "store_true" )
parser.add_argument( "-lv", "--list_values", help = "list available values", action = "store_true" )
parser.add_argument( "-r", "--root_dir", default = "DeepSDF" )
parser.add_argument( "-v", "--value", action='append', help = "Show extra values, e.g. " + ", ".join( possible_values ), default = [] )
parser.add_argument( "-hp", "--hide_parameters", action='append', help = "Hide job parameters", default = to_hide )
parser.add_argument( "-aj", "--all_job_parameters", action='store_true', help = "Show all job parameters" )

args = parser.parse_args()
job_root = join( home_dir, args.root_dir )
jobs = []
join = os.path.join

headers = [ "id", "job_args" ]

# get gpus architectures
gpus = {}

try:
    for line in os.popen('pbsnodes').read().split( "\n" ) :
        if "linux" in line : exec_host = line.split( "." )[ 0 ]
        if "properties" in line and "gpu" in line:
            gpus[ exec_host ] = line.split( "," ).pop()

    if args.list_gpus:
        for exec_host in sorted( gpus ):
            print( exec_host, gpus[ exec_host ] )
        exit( 0 )

except Exception as e:
    print( str( e ))



for dir in tqdm( sorted( os.listdir( job_root ) ) ):
    full_dir = join( job_root, dir )
    try:
        entry = {};
        entry[ "id" ] = int( dir )

        for extension in [ "pbs", "slurm" ]:
            if os.path.exists( join( full_dir, "job." + extension ) ):
                job_file = join( full_dir, "job." + extension )
                break

        with open( job_file ) as f:
            lines = f.read().split( "\n" )
            job_args = lines[ 1 ].split( "qsub.py " ).pop().split( "submit.py" ).pop()
            entry[ "full_job_args" ] = job_args
            if not args.all_job_parameters :
                for p in args.hide_parameters :
                    job_args = job_args.replace( p, "" )
            if len( job_args ) > args.job_args_length:
                job_args = job_args[:args.job_args_length - 3] + "..."
            entry[ "job_args" ] = job_args

        with open( join( full_dir, "specs.json"), 'r') as file:
            entry[ "config" ] = cfg = json.load(file)

        with open( join( full_dir, "log.out" ) ) as f:
            for line in f.read().split( "\n" ) :
                if "linux" in line :
                    exec_host = entry[ "exec_host" ] = line.split( "." )[ 0 ]
                    if exec_host in gpus:
                        entry[ "gpu" ] = gpus[ exec_host ]
                    else : entry[ "gpu" ] = "none"
                    break

        jobs.append( entry )

    except Exception as e:
        print( "Error for : " + full_dir )
        print( str( e ))
        print( entry )

def getField( job, field, notFoundValue = 0 ):
    if field in job : return job[ field ]
    else:
        value = get_parameter( job[ "config" ], field )
        if value == None : return notFoundValue
        return value

if args.list_values :
    values = {}
    for job in jobs:
        for field in job:
            if not isinstance( field, dict ) : values[ field ] = True

    print( "Available values" )
    print( sorted( values ) )
    exit( 0 )

if args.filter:
    jobs = list( filter( lambda j : args.filter in json.dumps( j ), jobs ) )

if args.filter_value:
    param, value = args.filter_value
    jobs = list( filter( lambda j : value in str( getField( j, param ) ), jobs ) )

if args.sort:
    jobs.sort( key = lambda j : getField( j, args.sort ) )
else:
    jobs.sort( key = lambda j : int( j[ "id" ] ) )


headers.extend( args.value )
tab = list( map( lambda j : list( map( lambda f : getField( j, f, "NA" ), headers ) ), jobs ) )
print( "Jobs : " )
print ( tabulate( tab, headers ) )

if args.csv :
    with open('leaderboard.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(tab)
