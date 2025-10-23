import argparse

from blueness import module
from blueness.argparse.generic import sys_exit
from bluer_options.logger.config import log_list

from bluer_objects import NAME
from bluer_objects import storage
from bluer_objects.storage.policies import DownloadPolicy
from bluer_objects.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="clear | download | ls | ls_objects | upload",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--filename",
    type=str,
    default="",
)
parser.add_argument(
    "--public",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--zip",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--where",
    type=str,
    default="local",
    help="local | cloud",
)
parser.add_argument(
    "--log",
    type=int,
    default=1,
    help="0|1",
)
parser.add_argument(
    "--delim",
    type=str,
    default=",",
)
parser.add_argument(
    "--do_dryrun",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--policy",
    type=str,
    default="none",
    help=" | ".join(sorted([policy.name.lower() for policy in DownloadPolicy])),
)
parser.add_argument(
    "--prefix",
    type=str,
    default="",
)
args = parser.parse_args()

delim = " " if args.delim == "space" else args.delim

success = False
if args.task == "clear":
    success = storage.clear(
        do_dryrun=args.do_dryrun == 1,
    )
elif args.task == "download":
    success = storage.download(
        object_name=args.object_name,
        filename=args.filename,
        policy=DownloadPolicy[args.policy.upper()],
    )
elif args.task == "ls":
    success, list_of_files = storage.ls(
        object_name=args.object_name,
        where=args.where,
    )

    if args.log:
        log_list(logger, "", list_of_files, "file(s)", 999)
    else:
        print(delim.join(list_of_files))
elif args.task == "ls_objects":
    success, list_of_objects = storage.ls_objects(
        prefix=args.prefix,
        where=args.where,
    )

    if args.log:
        log_list(logger, "", list_of_objects, "objects(s)", 999)
    else:
        print(delim.join(list_of_objects))
elif args.task == "upload":
    success = storage.upload(
        object_name=args.object_name,
        filename=args.filename,
        zip=args.zip == 1,
        public=args.public == 1,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
