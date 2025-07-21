#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import argparse
import csv
import json
import logging
import os
import random
import time
import torch
from reconstruct import reconstruct
import nibabel as nib
import numpy as np

import deep_sdf
import deep_sdf.workspace as ws

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(
        description="Use a trained DeepSDF decoder to reconstruct a shape given a latent representation."

    )
    arg_parser.add_argument(
        "--experiment",
        "-e",
        dest="experiment_directory",
        required=True,
        help="The experiment directory which includes specifications and saved model "
        + "files to use for reconstruction",
    )
    arg_parser.add_argument(
        "--checkpoint",
        "-c",
        dest="checkpoint",
        default="latest",
        help="The checkpoint weights to use. This can be a number indicated an epoch "
        + "or 'latest' for the latest weights (this is the default)",
    )
    arg_parser.add_argument(
        "--resolution",
        "-r",
        dest="resolution",
        type=int,
        default=256,
        help="The reconstruction resolution.",
    )
    arg_parser.add_argument(
        "--inputCSV",
        "-csv",
        help="The csv file to reconstruct",
        required=True
    )
    arg_parser.add_argument(
        "--saveSDF",
        help="save the SDF as a nifty image",
        action="store_true"
    )
    arg_parser.add_argument(
        "--npz",
        help="npz file to recover origin and scale from"
    )

    deep_sdf.add_common_args(arg_parser)

    args = arg_parser.parse_args()

    deep_sdf.configure_logging(args)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    specs_filename = os.path.join(args.experiment_directory, "specs.json")

    if not os.path.isfile(specs_filename):
        raise Exception(
            'The experiment directory does not include specifications file "specs.json"'
        )

    specs = json.load(open(specs_filename))

    arch = __import__("networks." + specs["NetworkArch"], fromlist=["Decoder"])

    latent_size = specs["CodeLength"]

    decoder = arch.Decoder(latent_size, **specs["NetworkSpecs"])

    decoder = torch.nn.DataParallel(decoder)

    saved_model_state = torch.load(
        os.path.join(
            args.experiment_directory, ws.model_params_subdir, args.checkpoint + ".pth"
        )
        , map_location=torch.device(device)
    )
    saved_model_epoch = saved_model_state["epoch"]

    decoder.load_state_dict(saved_model_state["model_state_dict"])

    decoder = decoder.module.to( device )

    logging.debug(decoder)

    err_sum = 0.0

    logging.debug("loading {}".format(args.inputCSV))
    with open(args.inputCSV) as csvfile:
        for row in csv.reader(csvfile):
            clean = filter( lambda c : len( c ) > 0, row)
            latent = list( map( lambda c : float( c ) , clean ) )

    if latent_size != len( latent ) :
        print( "Error : latent conde size must be", latent_size, ", not", len( latent ) )
        exit( 1 )
    latent = torch.tensor( latent ).to( device )
    decoder.eval()

    start = time.time()
    with torch.no_grad():
        values = deep_sdf.mesh.create_mesh(
            decoder, latent, "mesh", N=args.resolution, max_batch=int(2 ** 18) )

        if args.saveSDF:
            matrix = np.eye(4)
            if args.npz:
                npz = np.load(args.npz)
                offset = 2 * npz['offset']
                scale = npz['scale']
            else:
                offset = [-1, -1, -1]
                scale = 2.0 / (args.resolution - 1)

            matrix[:3, 3] = offset
            matrix[:3, :3] = scale

            # use nibabel to save the SDF as a nifty volume
            values = values.cpu().numpy()
            img = nib.Nifti1Image(values, matrix)
            nib.save(img, "sdf.nii.gz")

    logging.debug("total time: {}".format(time.time() - start))
