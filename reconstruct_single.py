#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import argparse
import json
import logging
import os
import random
import time
import torch
from reconstruct import reconstruct
import deep_sdf
import deep_sdf.workspace as ws

def add_args( arg_parser ):
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
        "--iters",
        dest="iterations",
        default=800,
        help="The number of iterations of latent code optimization to perform.",
    )
    arg_parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default="mesh",
        help="output mesh file name",
    )
    arg_parser.add_argument(
        "--cpu",
        action = "store_true",
        help="disable GPU",
    )
    return arg_parser

def init( args ):
    deep_sdf.configure_logging(args)

    device = torch.device('cuda' if not args.cpu and torch.cuda.is_available() else 'cpu')
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
    return specs, decoder

def reconstruct_mesh( args, specs, decoder, data_sdf ):
    data_sdf[0] = data_sdf[0][torch.randperm(data_sdf[0].shape[0])]
    data_sdf[1] = data_sdf[1][torch.randperm(data_sdf[1].shape[0])]

    start = time.time()
    err, latent = reconstruct(
        decoder,
        int(args.iterations),
        specs["CodeLength"],
        data_sdf,
        0.01,  # [emp_mean,emp_var],
        0.1,
        num_samples=8000,
        lr=5e-3,
        l2reg=True,
        args=args
    )
    logging.debug("reconstruct time: {}".format(time.time() - start))
    logging.debug("error : {}".format(err))
    logging.debug("latent: {}".format(latent.detach().cpu().numpy()))

    decoder.eval()

    scale = None
    if len(data_sdf) > 2 : scale=data_sdf[2]
    offset = None
    if len(data_sdf) > 3 : offset=data_sdf[3]
    start = time.time()
    with torch.no_grad():
        deep_sdf.mesh.create_mesh(
            decoder, latent, args.output, N=args.resolution, max_batch=int(2 ** 18), offset=offset, scale=scale, args=args
        )
    logging.debug("total time: {}".format(time.time() - start))
    torch.save(latent.unsqueeze(0), "code.pth")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Use a trained DeepSDF decoder to reconstruct a shape given SDF "
        + "samples."
    )
    add_args( arg_parser )
    arg_parser.add_argument(
        "--npz",
        "-z",
        dest="npz",
        help="The npz file to reconstruct",
        required=True
    )
    deep_sdf.add_common_args(arg_parser)
    args = arg_parser.parse_args()
    specs, decoder = init(args)
    logging.debug("loading {}".format(args.npz))
    data_sdf = deep_sdf.data.read_sdf_samples_into_ram(args.npz)
    reconstruct_mesh( args, specs, decoder, data_sdf )

