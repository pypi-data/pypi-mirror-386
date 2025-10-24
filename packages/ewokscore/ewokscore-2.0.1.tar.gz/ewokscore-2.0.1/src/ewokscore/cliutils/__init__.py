from . import cliconvertutils
from . import cliexecuteutils
from . import clilogutils


def add_execute_parameters(parser, shell=False):
    if shell:
        clilogutils.add_log_parameters(parser)
    cliexecuteutils.add_execute_parameters(parser)


def apply_execute_parameters(args, shell=False):
    if shell:
        clilogutils.apply_log_parameters(args)
    cliexecuteutils.apply_execute_parameters(args)


def add_convert_parameters(parser, shell=False):
    if shell:
        clilogutils.add_log_parameters(parser)
    cliconvertutils.add_convert_parameters(parser)


def apply_convert_parameters(args, shell=False):
    if shell:
        clilogutils.apply_log_parameters(args)
    cliconvertutils.apply_convert_parameters(args)
