# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from argparse import ArgumentParser, Namespace

# ---------------------
# third party libraries
# ---------------------

import decouple

from lica.cli import execute
from lica.validators import vfile


# --------------
# local imports
# -------------

from .. import __version__
from ..tdbalarm import one_pass
from ..dao import Session


# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS Database alarms tool"

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__.split(".")[-1])

sender = decouple.config("SMTP_SENDER")
receivers = decouple.config("SMTP_RECEIVERS")
host = decouple.config("SMTP_HOST")
port = decouple.config("SMTP_PORT", cast=int)
password = decouple.config("SMTP_PASSWORD")
cafile = decouple.config("SMTP_CACERT", default=None)
secure = decouple.config("SMTP_SECURE", cast=int, default=0)
admin_host = decouple.config("ADMIN_HTTP_ADDR")
admin_port = decouple.config("ADMIN_HTTP_PORT", cast=int)
wait_minutes = decouple.config("WAIT_MINUTES", cast=int)

# -------------------
# Auxiliary functions
# -------------------


def cli_main(args: Namespace) -> None:
    with Session() as session:
        with session.begin():
            one_pass(
                session=session,
                host=host,
                port=port,
                sender=sender,
                password=password,
                secure=bool(secure),
                cafile=cafile,
                receivers=receivers,
                admin_host=admin_host,
                admin_port=admin_port,
                wait_minutes=wait_minutes,
            )


def add_args(parser: ArgumentParser) -> None:
    pass


def main():
    """The main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
