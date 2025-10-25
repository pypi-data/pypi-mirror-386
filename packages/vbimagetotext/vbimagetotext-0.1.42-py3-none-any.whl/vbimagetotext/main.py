import re
import click
import os
from .gptvision import gptvision
from .geminivision import geminivision
# from .copyprompt import copyprompt
from .scan import scan
from .imgtopost import imgtopost
from .resolve import resolve
from .crop import crop
from .imagestolatex import imagestolatex
# from .varient import varient
from .sketchtotex import sketchtotex
from .extractsolution import extractsolution
from .extractanswer import extractanswer
from .check import check
from .deepvariant import deepvariant
from .agentic import agent
from .extractitem import extractitem
from .simulate import simulate
from .ocr import ocr
from .generatehint import generatehint
from .deepresearch import deepresearch
from .tikz_cache import tikzcache

CONTEXT_SETTINGS = dict(
    help_option_names=[
        '-h',
        '--help'
    ],
    auto_envvar_prefix='VBIMAGETOTEXT',
)


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


main.add_command(gptvision)
main.add_command(geminivision)
# main.add_command(gptloop)
main.add_command(scan)
main.add_command(imgtopost)
main.add_command(resolve)
main.add_command(crop)
main.add_command(imagestolatex)
# main.add_command(varient)
main.add_command(sketchtotex)
main.add_command(extractsolution)
main.add_command(extractanswer)
main.add_command(check)
main.add_command(deepvariant)
main.add_command(extractitem)
main.add_command(agent)
main.add_command(simulate)
main.add_command(ocr)
main.add_command(generatehint)
main.add_command(deepresearch)
main.add_command(tikzcache)
