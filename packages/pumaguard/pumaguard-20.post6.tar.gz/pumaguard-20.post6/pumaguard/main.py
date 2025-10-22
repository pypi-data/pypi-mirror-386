"""
PumaGuard
"""

import argparse
import logging
import os
import sys

from pumaguard import (
    __VERSION__,
    analyze,
    classify,
    model_cli,
    server,
    train,
    verify,
)
from pumaguard.models import (
    __MODELS__,
)
from pumaguard.presets import (
    Preset,
)
from pumaguard.utils import (
    print_bash_completion,
)


def create_global_parser() -> argparse.ArgumentParser:
    """
    Shared arguments.
    """
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        "--settings",
        help="Load presets from file",
        type=str,
    )
    global_parser.add_argument(
        "--debug",
        help="Debug the application",
        action="store_true",
    )
    global_parser.add_argument(
        "--version",
        action="version",
        version=__VERSION__,
    )
    global_parser.add_argument(
        "--completion",
        choices=["bash"],
        help="Print out bash completion script",
    )
    global_parser.add_argument(
        "--model-path",
        help="Where the models are stored (default = %(default)s)",
        type=str,
        default=os.getenv(
            "PUMAGUARD_MODEL_PATH",
            default=os.path.join(
                os.path.dirname(__file__), "../pumaguard-models"
            ),
        ),
    )
    global_parser.add_argument(
        "--model",
        help="The model to load",
        type=str,
        default="",
    )
    global_parser.add_argument(
        "--notebook",
        help="The notebook to use",
        type=int,
    )
    global_parser.add_argument(
        "--list-models",
        help="List the available models",
        action="store_true",
    )
    return global_parser


def configure_presets(args: argparse.Namespace, presets: Preset):
    """
    Configure the settings based on commandline arguments.
    """
    logger = logging.getLogger("PumaGuard")

    model_path = (
        args.model_path
        if hasattr(args, "model_path") and args.model_path
        else os.getenv("PUMAGUARD_MODEL_PATH", default=None)
    )

    logger.debug("model path is %s", presets.base_output_directory)

    if args.settings is None:
        logger.info("loading default settings")
        settings = os.path.join(model_path, "settings.yaml")
    else:
        settings = args.settings
    presets.load(settings)

    presets.image_dimensions = (299, 299)
    logger.warning("hardcoding image dimension: %s", presets.image_dimensions)

    logger.debug("model path is %s", presets.base_output_directory)

    if model_path is not None:
        logger.debug("setting model path to %s", model_path)
        presets.base_output_directory = model_path

    if args.list_models:
        logger.info("available models:")
        for name, model in __MODELS__.items():
            logger.info("  %s: %s", name, model.model_description())
        sys.exit(0)

    if args.notebook is not None:
        presets.notebook_number = args.notebook

    verification_path = (
        args.verification_path if hasattr(args, "verification_path") else None
    )
    if verification_path is not None:
        logger.debug("setting verification path to %s", verification_path)
        presets.verification_path = verification_path

    if args.model != "":
        presets.model_file = args.model


def configure_subparsers(
    parser: argparse.ArgumentParser,
    global_args_parser: argparse.ArgumentParser,
):
    """
    Configure the subparsers.
    """

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available sub-commands",
    )
    train.configure_subparser(
        subparsers.add_parser(
            "train",
            help="Train a model",
            description="Train a model and get the model weights.",
            parents=[global_args_parser],
        )
    )
    classify.configure_subparser(
        subparsers.add_parser(
            "classify",
            help="Classify images",
            description="Classify images using a particular model.",
            parents=[global_args_parser],
        )
    )
    server.configure_subparser(
        subparsers.add_parser(
            "server",
            help="Run the classification server",
            description=(
                "Run the classification server. The server "
                "will monitor folders and classify any new image "
                "added to those folders."
            ),
            parents=[global_args_parser],
        )
    )
    verify.configure_subparser(
        subparsers.add_parser(
            "verify",
            help="Verify a model",
            description="Verifies a model using a standard set of images.",
            parents=[global_args_parser],
        )
    )
    analyze.configure_subparser(
        subparsers.add_parser(
            "analyze",
            help="Analyze a model",
            description="Analyze a model.",
            parents=[global_args_parser],
        )
    )
    model_cli.configure_subparser(
        subparsers.add_parser(
            "models",
            help="Manage downloaded models",
            description=(
                "Manage downloaded models. "
                "This includes deleting or verifying them."
            ),
            parents=[global_args_parser],
        )
    )


def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("PumaGuard")

    file_handler = logging.FileHandler("pumaguard.log")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    global_args_parser = create_global_parser()
    parser = argparse.ArgumentParser(
        description="""The goal of this project is to accurately classify
                    images based on the presence of mountain lions. This can
                    have applications in wildlife monitoring, research, and
                    conservation efforts. The model is trained on a labeled
                    dataset and validated using a separate set of images.""",
        parents=[global_args_parser],
    )

    configure_subparsers(parser, global_args_parser)

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.debug("command line arguments: %s", args)

    if args.completion:
        print_bash_completion(command=args.command, shell=args.completion)
        sys.exit(0)

    presets = Preset()

    configure_presets(args, presets)

    logger.debug("presets: %s", str(presets).rstrip())

    if args.command == "train":
        train.main(args, presets)
    elif args.command == "server":
        server.main(args, presets)
    elif args.command == "classify":
        classify.main(args, presets)
    elif args.command == "verify":
        verify.main(args, presets)
    elif args.command == "analyze":
        analyze.main(args, presets)
    elif args.command == "models":
        model_cli.main(args, presets)
    else:
        parser.print_help()
