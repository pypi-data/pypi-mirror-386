from collections import Counter
import datetime
from typing import Any, List

from typing import Tuple

from app.config import KNOWN_IMPHASHES

import yarobot_rs
import os
import re
import logging


from yarobot_rs import ScoringEngine, TokenInfo, TokenType


def get_uint_string(magic):
    print(magic)
    return f"uint16(0) == 0x{hex(magic[1])[2:]}{hex(magic[0])[2:]}"


def sanitize_rule_name(path: str, file: str) -> str:
    """Generate a valid YARA rule name from path and filename.

    - Prefix with folder name if too short
    - Ensure it doesn't start with a number
    - Replace invalid chars with underscore
    - De-duplicate underscores
    """
    file_base = os.path.splitext(file)[0]
    cleaned = file_base
    if len(file_base) < 8:
        cleaned = path.split("\\")[-1:][0] + "_" + cleaned
    if re.search(r"^[0-9]", cleaned):
        cleaned = "sig_" + cleaned
    cleaned = re.sub(r"[^\w]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned


def get_timestamp_basic(date_obj=None):
    return (
        date_obj.strftime("%Y-%m-%d")
        if date_obj
        else datetime.datetime.now().strftime("%Y-%m-%d")
    )


def get_file_range(size, fm_size):
    size_string = ""
    # max sample size - args.filesize_multiplier times the original size
    max_size_b = size * fm_size
    # Minimum size
    if max_size_b < 1024:
        max_size_b = 1024
    # in KB
    max_size = int(max_size_b / 1024)
    max_size_kb = max_size
    # Round
    if len(str(max_size)) == 2:
        max_size = int(round(max_size, -1))
    elif len(str(max_size)) == 3:
        max_size = int(round(max_size, -2))
    elif len(str(max_size)) == 4:
        max_size = int(round(max_size, -3))
    elif len(str(max_size)) >= 5:
        max_size = int(round(max_size, -3))
    size_string = f"filesize < {max_size}KB"
    logging.getLogger("yarobot").debug(
        "File Size Eval: SampleSize (b): %s SizeWithMultiplier (b/Kb): %s / %s RoundedSize: %s",
        str(size),
        str(max_size_b),
        str(max_size_kb),
        str(max_size),
    )
    return size_string


def generate_general_condition(file_info, nofilesize, filesize_multiplier, args):
    """
    Generates a general condition for a set of files
    :param file_info:
    :return:
    """
    conditions = []
    pe_module_neccessary = False

    # Different Magic Headers and File Sizes
    magic_headers = []
    file_sizes = []
    imphashes = []

    for filePath in file_info:
        if not file_info[filePath].magic:
            continue
        magic = file_info[filePath].magic
        size = file_info[filePath].size
        imphash = file_info[filePath].imphash

        # Add them to the lists
        if magic not in magic_headers and magic != "":
            magic_headers.append(magic)
        if size not in file_sizes:
            file_sizes.append(size)
        if imphash not in imphashes and imphash != "":
            imphashes.append(imphash)

    # If different magic headers are less than 5
    if len(magic_headers) <= 5:
        magic_string = " or ".join(get_uint_string(h) for h in magic_headers)
        if " or " in magic_string:
            conditions.append("( {0} )".format(magic_string))
        else:
            conditions.append("{0}".format(magic_string))

    # Biggest size multiplied with maxsize_multiplier
    if not nofilesize and len(file_sizes) > 0:
        conditions.append(get_file_range(max(file_sizes), filesize_multiplier))

    # If different magic headers are less than 5
    if len(imphashes) == 1 and not args.noextras:
        conditions.append('pe.imphash() == "{0}"'.format(imphashes[0]))
        pe_module_neccessary = True

    # If enough attributes were special
    condition_string = " and ".join(conditions)

    return condition_string, pe_module_neccessary


class RuleGenerator:
    def __init__(self, args):
        self.prefix = args.prefix
        self.author = args.author
        self.ref = args.ref

    def generate_rule(
        self, rule_name, file, hashes, rule_strings, rule_opcodes, conditions
    ):
        # Print rule title
        rule = (
            f"rule {rule_name} {{\n"
            f"\tmeta:\n"
            f'\t\tdescription = "{self.prefix} - file {file}"\n'
            f'\t\tauthor = "{self.author}"\n'
            f'\t\treference = "{self.ref}"\n'
            f'\t\tdate = "{get_timestamp_basic()}"\n'
        )
        for i, hash in enumerate(hashes):
            rule += f'\t\thash{i + 1} = "{hash}"\n'
        rule += "\tstrings:\n"
        rule += "\n".join(rule_strings)
        rule += "\n"
        rule += "\n".join(rule_opcodes)
        rule += "\n\tcondition:\n"
        rule += "\t\t%s\n" % conditions
        rule += "}\n\n"
        return rule


def add_conditions(
    conditions,
    subconditions,
    rule_strings,
    rule_opcodes,
    high_scoring_strings,
    pe_conditions_add,
):
    # String combinations
    cond_op = ""  # opcodes condition
    cond_hs = ""  # high scoring strings condition
    cond_ls = ""  # low scoring strings condition

    low_scoring_strings = len(rule_strings) - high_scoring_strings
    if high_scoring_strings > 0:
        cond_hs = "1 of ($x*)"
    if low_scoring_strings > 0:
        if low_scoring_strings > 10:
            if high_scoring_strings > 0:
                cond_ls = "4 of them"
            else:
                cond_ls = "8 of them"
        else:
            cond_ls = "all of them"

    # If low scoring and high scoring
    cond_combined = "all of them"
    needs_brackets = False
    if low_scoring_strings > 0 and high_scoring_strings > 0:
        # If PE conditions have been added, don't be so strict with the strings
        if pe_conditions_add:
            cond_combined = "{0} or {1}".format(cond_hs, cond_ls)
            needs_brackets = True
        else:
            cond_combined = "{0} and {1}".format(cond_hs, cond_ls)
    elif low_scoring_strings > 0 and not high_scoring_strings > 0:
        cond_combined = "{0}".format(cond_ls)
    elif not low_scoring_strings > 0 and high_scoring_strings > 0:
        cond_combined = "{0}".format(cond_hs)
    if rule_opcodes:
        cond_op = " and all of ($op*)"
        # Opcodes (if needed)
    if cond_op or needs_brackets:
        subconditions.append("( {0}{1} )".format(cond_combined, cond_op))
    else:
        subconditions.append(cond_combined)


def generate_rule_tokens(
    scoring_engine, args, strings, utf16strings, opcodes, opcode_num
) -> Tuple[List[str], int, List[str]]:
    # Rule String generation
    (
        rule_strings,
        high_scoring_strings,
    ) = scoring_engine.generate_rule_strings(
        args.score,
        args.high_scoring,
        args.strings_per_rule,
        (strings or []) + (utf16strings or []),
    )  # generate_rule_strings(args,(strings or []) + (utf16strings or []),)

    rule_opcodes = []
    if opcodes:
        rule_opcodes = generate_rule_opcodes(opcodes, opcode_num)
    return rule_strings, high_scoring_strings, rule_opcodes


def generate_simple_rule(
    rg: RuleGenerator,
    printed_rules,
    args,
    scoring_engine: ScoringEngine,
    strings: List[TokenInfo] | None,
    opcodes: List[TokenInfo] | None,
    utf16strings: List[TokenInfo] | None,
    info,
    fname,
) -> str:
    if not strings and not utf16strings:
        logging.getLogger("yarobot").warning(
            "[W] Not enough high scoring strings to create a rule. (Try -z 0 to reduce the min score or --opcodes to include opcodes) FILE: %s",
            fname,
        )
        return False
    # Skip if there is nothing to do
    logging.getLogger("yarobot").info(
        "[+] Generating rule for %s, %d strings, %d opcodes, %d utf16strs",
        fname,
        len(strings),
        len(opcodes),
        len(utf16strings),
    )

    # Print rule title ----------------------------------------

    (path, file) = os.path.split(fname)
    # Prepare name via helper
    cleanedName = sanitize_rule_name(path, file)
    # Check if already printed
    if cleanedName in printed_rules:
        printed_rules[cleanedName] += 1
        cleanedName = cleanedName + "_" + str(printed_rules[cleanedName])
    else:
        printed_rules[cleanedName] = 1

    # Condition -----------------------------------------------
    # Conditions list (will later be joined with 'or')
    conditions = []  # AND connected
    subconditions = []  # OR connected

    # Condition PE
    # Imphash and Exports - applicable to PE files only
    condition_pe = []
    condition_pe_part1 = []
    condition_pe_part2 = []

    def add_extras():
        # Add imphash - if certain conditions are met
        if info.imphash not in scoring_engine.good_imphashes_db and info.imphash != "":
            # Comment to imphash
            imphash = info.imphash
            comment = ""
            if imphash in KNOWN_IMPHASHES:
                comment = " /* {0} */".format(KNOWN_IMPHASHES[imphash])
            # Add imphash to condition
            condition_pe_part1.append(
                'pe.imphash() == "{0}"{1}'.format(imphash, comment)
            )
            pe_module_necessary = True
        if info.exports:
            e_count = 0
            for export in info.exports:
                if export not in scoring_engine.good_exports_db:
                    condition_pe_part2.append('pe.exports("{0}")'.format(export))
                    e_count += 1
                    pe_module_necessary = True
                if e_count > 5:
                    break

    if not args.noextras and info.magic.startswith(b"MZ"):
        add_extras()

    # 1st Part of Condition 1
    def add_basic_conditions(conditions, info, args):
        basic_conditions: List[Any] = []
        # Filesize
        if not args.nofilesize:
            basic_conditions.insert(
                0, get_file_range(info.size, args.filesize_multiplier)
            )
        # Magic
        if info.magic != b"":
            uint_string = get_uint_string(info.magic)
            basic_conditions.insert(0, uint_string)
        conditions.append(" and ".join(basic_conditions))

    add_basic_conditions(conditions, info, args)
    # Add extra PE conditions to condition 1
    pe_conditions_add = False
    if condition_pe_part1 or condition_pe_part2:
        if len(condition_pe_part1) == 1:
            condition_pe.append(condition_pe_part1[0])
        elif len(condition_pe_part1) > 1:
            condition_pe.append(f"( {' or '.join(condition_pe_part1)} )")
        if len(condition_pe_part2) == 1:
            condition_pe.append(condition_pe_part2[0])
        elif len(condition_pe_part2) > 1:
            condition_pe.append(f"({' and '.join(condition_pe_part2)} )")
        # Marker that PE conditions have been added
        pe_conditions_add = True
        # Add to sub condition
        subconditions.append(" and ".join(condition_pe))

    rule_strings, high_scoring_strings, rule_opcodes = generate_rule_tokens(
        scoring_engine, args, strings, utf16strings, opcodes, args.opcode_num
    )
    add_conditions(
        conditions,
        subconditions,
        rule_strings,
        rule_opcodes,
        high_scoring_strings,
        pe_conditions_add,
    )

    # Now add string condition to the conditions
    if len(subconditions) == 1:
        conditions.append(subconditions[0])
    elif len(subconditions) > 1:
        conditions.append("( %s )" % " or ".join(subconditions))

    # Create condition string
    condition_string = " and\n      ".join(conditions)

    return rg.generate_rule(
        cleanedName, file, [info.sha256], rule_strings, rule_opcodes, condition_string
    )


def generate_super_rule(
    rg: RuleGenerator,
    super_rule,
    infos,
    args,
    scoring_engine,
    printed_rules,
    super_rule_names,
    printed_combi,
    super_rule_count,
    opcodes,
):
    # Prepare Name
    rule_name = ""
    file_list = []
    hashes = []
    # Loop through files
    print("Generating super rule for %s" % super_rule)
    imphashes = Counter()
    for filePath in super_rule.files:
        (path, file) = os.path.split(filePath)
        file_list.append(file)
        # Prepare name via helper
        cleanedName = sanitize_rule_name(path, file)
        # Append it to the full name
        rule_name += "_" + cleanedName
        # Check if imphash of all files is equal
        imphash = infos[filePath].imphash
        hashes.append(infos[filePath].sha256)
        if imphash != "-" and imphash != "":
            imphashes.update([imphash])

    # Imphash usable
    if len(imphashes) == 1:
        unique_imphash = list(imphashes.items())[0][0]
        if unique_imphash in scoring_engine.good_imphashes_db:
            unique_imphash = ""

    # Shorten rule name
    rule_name = rule_name[:124]
    # Add count if rule name already taken
    if rule_name not in super_rule_names:
        rule_name = "%s_%s" % (rule_name, super_rule_count)
    super_rule_names.append(rule_name)

    # File name starts with a number
    if re.search(r"^[0-9]", rule_name):
        rule_name = "sig_" + rule_name
    # clean name from all characters that would cause errors
    rule_name = re.sub(r"[^\w]", "_", rule_name)
    # Check if already printed
    if rule_name in printed_rules:
        printed_combi[rule_name] += 1
        rule_name = rule_name + "_" + str(printed_combi[rule_name])
    else:
        printed_combi[rule_name] = 1

    rule_strings, high_scoring_strings, rule_opcodes = generate_rule_tokens(
        scoring_engine, args, super_rule.strings, [], opcodes, args.opcode_num
    )

    # Condition -----------------------------------------------
    # Conditions list (will later be joined with 'or')
    conditions = []
    subconditions = []
    # 1st condition
    # Evaluate the general characteristics
    file_info_super = {}
    pe_module_necessary = False
    for filePath in super_rule.files:
        file_info_super[filePath] = infos[filePath]
    condition_strings, pe_module_necessary_gen = generate_general_condition(
        infos, args.nofilesize, args.filesize_multiplier, args
    )
    if pe_module_necessary_gen:
        pe_module_necessary = True

    # 2nd condition
    # String combinations
    add_conditions(
        conditions,
        subconditions,
        rule_strings,
        rule_opcodes,
        high_scoring_strings,
        pe_module_necessary,
    )
    # Now add string condition to the conditions
    if len(subconditions) == 1:
        conditions.append(subconditions[0])
    elif len(subconditions) > 1:
        conditions.append("( %s )" % " or ".join(subconditions))
    # Create condition string
    condition_string = "\n      ) or ( ".join(conditions)

    return rg.generate_rule(
        rule_name,
        ", ".join(file_list),
        hashes,
        rule_strings,
        rule_opcodes,
        condition_string,
    )


def generate_top_info(author, identifier, ref, license):
    # General Info
    general_info = "/*\n"
    general_info += "   YARA Rule Set\n"
    general_info += f"   Author: {author}\n"
    general_info += f"   Date: {get_timestamp_basic()}\n"
    general_info += f"   Identifier: {identifier}\n"
    general_info += f"   Reference: {ref}\n"
    if license != "":
        general_info += f"   License: {license}\n"
    general_info += "*/\n\n"
    return general_info


def generate_rules(
    rg: RuleGenerator,
    scoring_engine,
    args,
    file_strings,
    file_opcodes,
    file_utf16strings,
    super_rules,
    opcode_super_rules,
    utf16_super_rules,
    file_info,
):
    fdata = ""
    with open(args.output_rule_file, "w") as fh:
        fdata = generate_top_info(args.author, args.identifier, args.ref, args.license)

        # GLOBAL RULES ----------------------------------------------------
        if args.globalrule:
            condition, pe_module_necessary = generate_general_condition(
                file_info, args.nofilesize, args.filesize_multiplier, args
            )

            # Global Rule
            if condition != "":
                global_rule = (
                    "/* Global Rule -------------------------------------------------------------- */\n"
                    "/* Will be evaluated first, speeds up scanning process, remove at will */\n\n"
                    "global private rule gen_characteristics {\n"
                    "\tcondition:\n"
                    f"\t\t{condition}\n}}\n\n"
                )

                fdata += global_rule

        # General vars
        rules = ""
        printed_rules = {}
        rule_count = 0
        super_rule_count = 0

        # PROCESS SIMPLE RULES ----------------------------------------------------
        logging.getLogger("yarobot").info("[+] Generating Simple Rules ...")

        # logging.getLogger("yarobot").info(file_strings)

        # GENERATE SIMPLE RULES -------------------------------------------
        fdata += "/* Rule Set ----------------------------------------------------------------- */\n\n"
        all_files_set = set(file_strings.keys())
        all_files_set.update(file_opcodes.keys())
        all_files_set.update(file_utf16strings.keys())

        for filePath in all_files_set:
            if rule := generate_simple_rule(
                rg,
                printed_rules,
                args,
                scoring_engine,
                file_strings[filePath] if filePath in file_strings.keys() else [],
                file_opcodes[filePath] if filePath in file_opcodes.keys() else [],
                file_utf16strings[filePath]
                if filePath in file_utf16strings.keys()
                else [],
                file_info[filePath],
                filePath,
            ):
                rules += rule
                rule_count += 1

        # GENERATE SUPER RULES --------------------------------------------
        if not args.nosuper:
            rules += "/* Super Rules ------------------------------------------------------------- */\n\n"
            super_rule_names = []

            print("[+] Generating Super Rules ...")
            printed_combi = {}
            for super_rule in super_rules + opcode_super_rules + utf16_super_rules:
                rules += generate_super_rule(
                    rg,
                    super_rule,
                    file_info,
                    args,
                    scoring_engine,
                    printed_rules,
                    super_rule_names,
                    printed_combi,
                    super_rule_count,
                    None,
                )
                super_rule_count += 1

        # WRITING RULES TO FILE
        # PE Module -------------------------------------------------------
        if not args.noextras:
            if "pe." in rules:
                fdata += 'import "pe"\n\n'
        # RULES ------------------------------
        fdata += rules
        fh.write(fdata)
        # Print rules to command line -------------------------------------
        logging.getLogger("yarobot").debug(rules)

    return (rule_count, super_rule_count, fdata)


def generate_string_repr(is_super_string, i, stringe):
    return f'\t\t${"x" if is_super_string else "s"}{i + 1} = "{stringe.reprz.replace("\\", "\\\\").replace('"', '\\"')}" {"wide" if stringe.typ == TokenType.UTF16LE else "ascii"}\
 {"fullword" if stringe.fullword else ""} /*{stringe.notes}*/'


def generate_opcode_repr(i, opcode):
    return f"\t\t$op{i} = {{{opcode.reprz}}}"


def generate_rule_opcodes(opcode_elements, opcodes_per_rule):
    # Adding the opcodes --------------------------------------
    rule_opcodes = []
    for i, opcode in enumerate(opcode_elements):
        rule_opcodes.append(generate_opcode_repr(i, opcode))
        if i >= opcodes_per_rule:
            break
    return rule_opcodes


def generate_rule_strings(
    scoring_engine, args, string_elements
) -> Tuple[List[str], int]:
    rule_strings = []
    # Adding the strings --------------------------------------

    # string_elements = list(set(string_elements))
    string_elements = sorted(string_elements, key=lambda x: x.score, reverse=True)
    high_scoring_strings = 0
    for i, stringe in enumerate(string_elements):
        # Collect the data
        string = stringe.reprz

        if string in scoring_engine.good_strings_db:
            stringe.add_note(
                f"goodware string - occured {scoring_engine.good_strings_db[string]} times"
            )

        if args.score:
            stringe.add_note(f" / score: {stringe.score} /")
        else:
            logging.getLogger("yarobot").debug("NO SCORE: %s", string)

        if stringe.b64:
            stringe.add_note(
                f" / base64 encoded string '{scoring_engine.base64strings[string]}' /"
            )
        if stringe.hexed:
            stringe.add_note(
                f" / hex encoded string '{yarobot_rs.remove_non_ascii_drop(scoring_engine.hex_enc_strings[string]).decode()}' /"
            )
        if stringe.from_pestudio and args.score:
            stringe.add_note(f" / PEStudio Blacklist: {args.pestudio_marker[string]} /")
        if stringe.reversed:
            stringe.add_note(
                f" / reversed goodware string '{scoring_engine.reversed_strings[string]}' /"
            )

        is_super_string = float(stringe.score) > args.high_scoring
        if is_super_string:
            high_scoring_strings += 1
        rule_strings.append(generate_string_repr(is_super_string, i, stringe))

        # If too many string definitions found - cut it at the
        # count defined via command line param -rc
        if (i + 1) >= args.strings_per_rule:
            break

    else:
        logging.getLogger("yarobot").info(
            "[-] Not enough unique opcodes found to include them"
        )

    return rule_strings, high_scoring_strings
