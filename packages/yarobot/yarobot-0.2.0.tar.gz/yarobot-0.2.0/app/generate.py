#!/usr/bin/env python


"""
yarGen - Yara Rule Generator, Copyright (c) 2015, Florian Roth
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Florian Roth BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import sys
import logging

import time
from collections import Counter
from lxml import etree

from app.common import get_abs_path, load, load_db
from app.config import DB_PATH, PE_STRINGS_FILE

import pstats

import cProfile
from app.rule_generator import RuleGenerator, generate_rules

# from app.scoring import extract_stats_by_file, sample_string_evaluation
from app.config import RELEVANT_EXTENSIONS

import yarobot_rs

import click
import os
import sys

from app import database


def getPrefix(prefix, identifier):
    """
    Get a prefix string for the rule description based on the identifier
    :param prefix:
    :param identifier:
    :return:
    """
    if prefix == "Auto-generated rule":
        return identifier
    else:
        return prefix


def getIdentifier(id, path):
    """
    Get a identifier string - if the provided string is the path to a text file, then read the contents and return it as
    reference, otherwise use the last element of the full path
    :param ref:
    :return:
    """
    # Identifier
    if id == "not set" or not os.path.exists(id):
        # Identifier is the highest folder name
        return os.path.basename(path.rstrip("/"))
    else:
        # Read identifier from file
        identifier = open(id).read()
        print("[+] Read identifier from file %s > %s" % (id, identifier))
        return identifier


def getReference(ref):
    """
    Get a reference string - if the provided string is the path to a text file, then read the contents and return it as
    reference
    :param ref:
    :return:
    """
    if os.path.exists(ref):
        reference = open(ref).read()
        print("[+] Read reference from file %s > %s" % (ref, reference))
        return reference
    else:
        return ref


def emptyFolder(dir):
    """
    Removes all files from a given folder
    :return:
    """
    for file in os.listdir(dir):
        filePath = os.path.join(dir, file)
        try:
            if os.path.isfile(filePath):
                print("[!] Removing %s ..." % filePath)
                os.unlink(filePath)
        except Exception as e:
            print(e)


def initialize_pestudio_strings():
    # if not os.path.isfile(get_abs_path(PE_STRINGS_FILE)):
    #    return None
    print("[+] Processing PEStudio strings ...")

    pestudio_strings = {}

    tree = etree.parse(get_abs_path(PE_STRINGS_FILE))
    processed_strings = {}
    pestudio_strings["strings"] = tree.findall(".//string")
    pestudio_strings["av"] = tree.findall(".//av")
    pestudio_strings["folder"] = tree.findall(".//folder")
    pestudio_strings["os"] = tree.findall(".//os")
    pestudio_strings["reg"] = tree.findall(".//reg")
    pestudio_strings["guid"] = tree.findall(".//guid")
    pestudio_strings["ssdl"] = tree.findall(".//ssdl")
    pestudio_strings["ext"] = tree.findall(".//ext")
    pestudio_strings["agent"] = tree.findall(".//agent")
    pestudio_strings["oid"] = tree.findall(".//oid")
    pestudio_strings["priv"] = tree.findall(".//priv")
    for category, elements in pestudio_strings.items():
        for elem in elements:
            processed_strings[elem.text] = (5, category)
    return processed_strings


def load_databases():
    good_strings_db = Counter()
    good_opcodes_db = Counter()
    good_imphashes_db = Counter()
    good_exports_db = Counter()

    # Initialize all databases
    for file in os.listdir(get_abs_path(DB_PATH)):
        if file.endswith(".db") or file.endswith(".json"):
            if file.startswith("good-strings"):
                load_db(
                    file, good_strings_db, True if file.endswith(".json") else False
                )
            if file.startswith("good-opcodes"):
                load_db(
                    file, good_opcodes_db, True if file.endswith(".json") else False
                )
            if file.startswith("good-imphashes"):
                pass  # load_db(file, good_imphashes_db, True if file.endswith(".json") else False) TODO
            if file.startswith("good-exports"):
                pass  # load_db(file, good_exports_db, True if file.endswith(".json") else False) TODO
    return good_strings_db, good_opcodes_db, good_imphashes_db, good_exports_db


def process_folder(
    args,
    folder,
    good_strings_db={},
    good_opcodes_db={},
    good_imphashes_db={},
    good_exports_db={},
    pestudio_strings={},
):
    if args.opcodes and len(good_opcodes_db) < 1:
        logging.getLogger("yarobot").warning(
            "Missing goodware opcode databases.    Please run 'yarobot update' to retrieve the newest database set."
        )
        args.opcodes = False

    if len(good_exports_db) < 1 and len(good_imphashes_db) < 1:
        logging.getLogger("yarobot").warning(
            "Missing goodware imphash/export databases.     Please run 'yarobot update' to retrieve the newest database set."
        )

    if len(good_strings_db) < 1:
        logging.getLogger("yarobot").warning(
            "no goodware databases found.     Please run 'yarobot update' to retrieve the newest database set."
        )
        # sys.exit(1)

    # Scan malware files
    logging.getLogger("yarobot").info(f"[+] Generating YARA rules from {folder}")
    (
        combinations,
        super_rules,
        utf16_combinations,
        utf16_super_rules,
        opcode_combinations,
        opcode_super_rules,
        file_strings,
        file_opcodes,
        file_utf16strings,
        file_info,
        scoring_engine,
    ) = yarobot_rs.process_malware(
        folder,
        args.recursive,
        RELEVANT_EXTENSIONS,
        args.min_size,
        args.max_size,
        args.max_file_size,
        args.opcodes,
        args.debug,
        args.excludegood,
        args.min_score,
        args.superrule_overlap,
        good_strings_db,
        good_opcodes_db,
        good_imphashes_db,
        good_exports_db,
        pestudio_strings,
    )
    # Apply intelligent filters
    logging.getLogger("yarobot").info(
        "[-] Applying intelligent filters to string findings ..."
    )
    file_strings = {
        fpath: scoring_engine.filter_string_set(strings)
        for fpath, strings in file_strings.items()
    }

    file_opcodes = {
        fpath: scoring_engine.filter_opcode_set(opcodes)
        for fpath, opcodes in file_opcodes.items()
    }

    file_utf16strings = {
        fpath: scoring_engine.filter_string_set(utf16strings)
        for fpath, utf16strings in file_utf16strings.items()
    }

    # Create Rule Files
    rg = RuleGenerator(args)
    (rule_count, super_rule_count, rules) = generate_rules(
        rg,
        scoring_engine,
        args,
        file_strings,
        file_opcodes,
        file_utf16strings,
        super_rules,
        opcode_super_rules,
        utf16_super_rules,
        file_info,
    )

    print("[=] Generated %s SIMPLE rules." % str(rule_count))
    if not args.nosuper:
        print("[=] Generated %s SUPER rules." % str(super_rule_count))
    print("[=] All rules written to %s" % args.output_rule_file)
    return rules


@click.command()
@click.argument("malware_path", type=click.Path(exists=True))
@click.option(
    "-y",
    "--min-size",
    help="Minimum string length to consider (default=8)",
    type=int,
    default=8,
)
@click.option(
    "-z",
    "--min-score",
    help="Minimum score to consider (default=5)",
    type=int,
    default=5,
)
@click.option(
    "-x",
    "--high-scoring",
    help='Score required to set string as "highly specific string" (default: 30)',
    type=int,
    default=30,
)
@click.option(
    "-w",
    "--superrule-overlap",
    help="Minimum number of strings that overlap to create a super rule (default: 5)",
    type=int,
    default=5,
)
@click.option(
    "-s",
    "--max-size",
    help="Maximum length to consider (default=128)",
    type=int,
    default=128,
)
@click.option(
    "-rc",
    "--strings-per-rule",
    help="Maximum number of strings per rule (default=15, intelligent filtering will be applied)",
    type=int,
    default=15,
)
@click.option(
    "--excludegood",
    help="Force the exclude all goodware strings",
    is_flag=True,
    default=False,
)
@click.option(
    "-o", "--output-rule-file", help="Output rule file", default="yarobot_rules.yar"
)
@click.option(
    "-e", "--output-dir-strings", help="Output directory for string exports", default=""
)
@click.option("-a", "--author", help="Author Name", default="yarobot Rule Generator")
@click.option(
    "--ref",
    help="Reference (can be string or text file)",
    default="https://github.com/ogre2007/yarobot",
)
@click.option("-l", "--license", help="License", default="")
@click.option(
    "-p",
    "--prefix",
    help="Prefix for the rule description",
    default="Auto-generated rule",
)
@click.option(
    "-b",
    "--identifier",
    help="Text file from which the identifier is read (default: last folder name in the full path)",
    default="not set",
)
@click.option(
    "--score",
    help="Show the string scores as comments in the rules",
    is_flag=True,
    default=False,
)
@click.option(
    "--nosimple",
    help="Skip simple rule creation for files included in super rules",
    is_flag=True,
    default=False,
)
@click.option(
    "--nomagic",
    help="Don't include the magic header condition statement",
    is_flag=True,
    default=False,
)
@click.option(
    "--nofilesize",
    help="Don't include the filesize condition statement",
    is_flag=True,
    default=False,
)
@click.option(
    "-fm",
    "--filesize-multiplier",
    help="Multiplier for the maximum 'filesize' condition value (default: 2)",
    type=int,
    default=2,
)
@click.option(
    "--globalrule",
    help="Create global rules (improved rule set speed)",
    is_flag=True,
    default=False,
)
@click.option(
    "--nosuper",
    help="Don't try to create super rules that match against various files",
    is_flag=True,
    default=False,
)
@click.option(
    "-R",
    "--recursive",
    help="Recursively scan directories",
    is_flag=True,
    default=False,
)
@click.option(
    "--oe",
    "--only-executable",
    help="Only scan executable extensions EXE, DLL, ASP, JSP, PHP, BIN, INFECTED",
    is_flag=True,
    default=False,
)
@click.option(
    "-fs",
    "--max-file-size",
    help="Max file size in MB to analyze (default=2)",
    type=int,
    default=2,
)
@click.option(
    "--noextras",
    help="Don't use extras like Imphash or PE header specifics",
    is_flag=True,
    default=False,
)
@click.option("--debug", help="Debug output", is_flag=True, default=False)
@click.option("--trace", help="Trace output", is_flag=True, default=False)
@click.option(
    "--opcodes",
    help="Do use the OpCode feature (use this if not enough high scoring strings can be found)",
    is_flag=True,
    default=False,
)
@click.option(
    "-n",
    "--opcode-num",
    help="Number of opcodes to add if not enough high scoring string could be found (default=3)",
    type=int,
    default=3,
)
def generate(malware_path, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    """Generate YARA rules from malware samples"""
    args = type("Args", (), kwargs)()

    # Validate input
    if malware_path and os.path.isfile(malware_path):
        click.echo("[E] Input is a file, please use a directory instead (-m path)")
        sys.exit(0)
    sourcepath = malware_path
    args.identifier = getIdentifier(args.identifier, sourcepath)
    print("[+] Using identifier '%s'" % args.identifier)

    # Reference
    args.ref = getReference(args.ref)
    print("[+] Using reference '%s'" % args.ref)

    # Prefix
    args.prefix = getPrefix(args.prefix, args.identifier)
    print("[+] Using prefix '%s'" % args.prefix)

    pestudio_strings = initialize_pestudio_strings()
    print("[+] Reading goodware strings from database 'good-strings.db' ...")
    print(
        "    (This could take some time and uses several Gigabytes of RAM depending on your db size)"
    )

    good_strings_db, good_opcodes_db, good_imphashes_db, good_exports_db = (
        load_databases()
    )
    # exit()
    process_folder(
        args,
        malware_path,
        good_strings_db,
        good_opcodes_db,
        good_imphashes_db,
        good_exports_db,
        pestudio_strings,
    )
    pr.disable()

    stats = pstats.Stats(pr)
    stats.sort_stats("cumulative").print_stats(
        10
    )  # Sort by cumulative time and print top 10


@click.command()
@click.argument("malware_path", type=click.Path(exists=True))
@click.option(
    "-y",
    "--min-size",
    help="Minimum string length to consider (default=8)",
    type=int,
    default=8,
)
@click.option(
    "-z",
    "--min-score",
    help="Minimum score to consider (default=5)",
    type=int,
    default=5,
)
@click.option(
    "-o", "--output-rule-file", help="Output rule file", default="yarobot_rules.yar"
)
@click.option("-a", "--author", help="Author Name", default="yarobot Rule Generator")
@click.option("--opcodes", help="Use the OpCode feature", is_flag=True, default=False)
@click.option("--debug", help="Debug output", is_flag=True, default=False)
def dropzone(malware_path, **kwargs):
    """Dropzone mode - monitor directory for new samples and generate rules automatically"""
    args = type("Args", (), kwargs)()

    click.echo(f"[+] Starting dropzone mode, monitoring {malware_path}")
    click.echo("[!] WARNING: Processed files will be deleted!")

    while True:
        if len(os.listdir(malware_path)) > 0:
            # Deactivate super rule generation if there's only a single file in the folder
            if len(os.listdir(malware_path)) < 2:
                args.nosuper = True
            else:
                args.nosuper = False
            # Read a new identifier
            identifier = getIdentifier(args.b, malware_path)
            # Read a new reference
            reference = getReference(args.ref)
            # Generate a new description prefix
            prefix = getPrefix(args.p, identifier)
            # Process the samples
            processSampleDir(malware_path)
            # Delete all samples from the dropzone folder
            emptyFolder(malware_path)
        time.sleep(1)


# MAIN ################################################################
if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("YAROBOT_LOG_LEVEL", "INFO"))
    logging.getLogger().setLevel(logging.DEBUG)
    generate()
    # Identifier
