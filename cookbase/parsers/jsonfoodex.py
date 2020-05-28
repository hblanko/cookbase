"""Parsing suite for the Cookbase platform from `FoodEx2`_  data into JSON documents.

The main command, :option:`parsexml`, allows for lossless translation from `FoodEx2`_
XML data into a collection of JSON documents. Nonetheless, it also permits to filter out
and discard the desired hierarchies together with the ingredients that belong only to
those hierarchies. Field contents are parsed into Python built-in types (:keyword:`str`,
:keyword:`int` and :keyword:`bool`). The original ordering and format are respected,
however there are a number of particularities when mapping into JSON to be considered:

    - The JSON output represents the content of the root :const:`<catalogue>` tag.
    - The :const:`<hierarchyGroups>` tag is mapped into JSON object that holds an array
      with the text from each contained :const:`<hierarchyGroup>` tag.
    - The :const:`<hierarchyAssignment>` tag is mapped into a JSON object whose key is
      the :const:`<hierarchyCode>` tag content, and the value is a JSON document
      including all its data.
    - The :const:`<implicitAttribute>` tag is mapped into a JSON object whose key is the
      :const:`<attributeCode>` tag content, and the value is an array with the text from
      each contained :const:`<attributeValue>` tag.

The :option:`-d`/:option:`--discardedhierarchies` option lets the user choose whether or
not to discard any desired hierarchy (including the terms that are only related to them)
by providing a list of hierarchy codes. By default, if not used, all hierarchies not
directly related to food preparation are discarded: :const:`botanic`, :const:`pest`,
:const:`biomo`, :const:`legis`, :const:`feed`, :const:`partcon`, :const:`place`,
:const:`vetdrug`, :const:`report`, :const:`fpurpose`, :const:`replev`, :const:`targcon`
and :const:`feedAddExpo`. In case of wanting not to discard any hierarchy, the
:option:`-d`/:option:`--discardedhierarchies` flag should be used providing no
hierarchies to discard.

The :option:`-cb`/:option:`--cookbase` flag argument indicates to generate identifiers
(:code:`_id`) for each catalogue term suitable for the Cookbase platform.

The :option:`hierarchize` command permits to build a JSON document describing a
hierarchy tree.

"""
import argparse
import json
import os
from collections import OrderedDict
from math import ceil
from time import time
from typing import Any, Dict, Optional, Tuple
from xml.dom import minidom

from cookbase.utils import _HelpAction

# from cookbase.parsers import termcode # this import is performed in-place
vprint = None


def parsexml(args: argparse.Namespace) -> None:
    """Method implementing the parsing logic.

    :param args: Command-line arguments
    :type args: argparse.Namespace
    """
    if args.cookbase:
        try:
            from cookbase.parsers import termcode
        except ImportError:
            print(
                "   WARNING: cookbase.parsers.termcode is not included under"
                + "PYTHONPATH. The parser will not generate '_id' fields."
            )
            args.cookbase = False

    start_time = time()
    generic_term_counter = 0
    expo_term_counter = 0

    vprint("loading and parsing the FoodEx2 Matrix...")

    foodex_xml = minidom.parse(args.inputfile)
    catalogue = OrderedDict()

    # including information about the parser configuration
    vprint("including information about the parser configuration...")

    catalogue["parserInfo"] = {"discardedHierarchies": args.discardedhierarchies}

    # parsing the <catalogueDesc> node
    vprint("parsing the <catalogueDesc> node...")

    node = foodex_xml.getElementsByTagName("catalogueDesc")[0]
    catalogue["catalogueDesc"] = OrderedDict()

    for i in node.childNodes:
        if i.nodeType != i.TEXT_NODE:
            if i.nodeName == "termCodeLength":
                catalogue["catalogueDesc"][i.nodeName] = int(i.firstChild.nodeValue)
            elif i.nodeName in ["acceptNonStandardCodes", "generateMissingCodes"]:
                if i.firstChild.nodeValue == "true":
                    catalogue["catalogueDesc"][i.nodeName] = True
                else:
                    catalogue["catalogueDesc"][i.nodeName] = False
            else:
                catalogue["catalogueDesc"][i.nodeName] = i.firstChild.nodeValue

    # parsing the <catalogueVersion> node
    vprint("parsing the <catalogueVersion> node...")

    node = foodex_xml.getElementsByTagName("catalogueVersion")[0]
    catalogue["catalogueVersion"] = OrderedDict()

    for i in node.childNodes:
        if i.nodeType != i.TEXT_NODE:
            catalogue["catalogueVersion"][i.nodeName] = i.firstChild.nodeValue

    # parsing the <catalogueGroups> node
    vprint("parsing the <catalogueGroups> node...")

    node = foodex_xml.getElementsByTagName("catalogueGroups")[0]
    catalogue["catalogueGroups"] = OrderedDict()
    catalogue["catalogueGroups"][node.childNodes[1].nodeName] = node.childNodes[
        1
    ].firstChild.nodeValue

    del node

    # parsing the <catalogueHierarchies> node
    vprint("parsing the <catalogueHierarchies> node...")

    hierarchy_nodes = foodex_xml.getElementsByTagName("hierarchy")

    # checking whether or not the hierarchies to discard exist
    for i in args.discardedhierarchies:
        f = False

        for j in hierarchy_nodes:
            if i == j.getElementsByTagName("code")[0].firstChild.nodeValue:
                f = True
                break

        if not f:
            print(
                '   WARNING: the hierarchy "'
                + i
                + '" listed to discard does not exist in this catalogue'
            )

    catalogue["catalogueHierarchies"] = OrderedDict()

    for hierarchy_node in hierarchy_nodes:
        code = hierarchy_node.getElementsByTagName("code")[0].firstChild.nodeValue

        if code not in args.discardedhierarchies:
            hierarchy_dict = OrderedDict()

            for i in hierarchy_node.childNodes:
                if i.nodeType != i.TEXT_NODE:
                    if i.nodeName == "hierarchyGroups":
                        hierarchyGroups_list = []

                        for j in i.childNodes:
                            if j.nodeType != j.TEXT_NODE:
                                hierarchyGroups_list.append(j.firstChild.nodeValue)
                        hierarchy_dict[i.nodeName] = hierarchyGroups_list
                    else:
                        hierarchy_dict[i.nodeName] = OrderedDict()

                        for j in i.childNodes:
                            if j.nodeType != j.TEXT_NODE:
                                if j.nodeName == "hierarchyOrder":
                                    hierarchy_dict[i.nodeName][j.nodeName] = int(
                                        j.firstChild.nodeValue
                                    )
                                elif j.nodeType != j.TEXT_NODE:
                                    hierarchy_dict[i.nodeName][
                                        j.nodeName
                                    ] = j.firstChild.nodeValue

            catalogue["catalogueHierarchies"][code] = hierarchy_dict

    del hierarchy_nodes, hierarchy_dict

    # parsing the <catalogueAttributes> node
    vprint("parsing the <catalogueAttributes> node")

    attribute_nodes = foodex_xml.getElementsByTagName("attribute")
    catalogue["catalogueAttributes"] = OrderedDict()

    for attribute_node in attribute_nodes:
        code = attribute_node.getElementsByTagName("code")[0].firstChild.nodeValue

        attribute_dict = OrderedDict()

        for i in attribute_node.childNodes:
            if i.nodeType != i.TEXT_NODE:
                attribute_dict[i.nodeName] = OrderedDict()

                for j in i.childNodes:
                    if j.nodeType != j.TEXT_NODE:
                        if j.nodeName in ["attributeOrder", "attributeMaxLength"]:
                            attribute_dict[i.nodeName][j.nodeName] = int(
                                j.firstChild.nodeValue
                            )
                        elif j.nodeName in [
                            "attributeVisible",
                            "attributeSearchable",
                            "attributeUniqueness",
                            "attributeTermCodeAlias",
                        ]:
                            if j.firstChild.nodeValue == "true":
                                attribute_dict[i.nodeName][j.nodeName] = True
                            else:
                                attribute_dict[i.nodeName][j.nodeName] = False
                        else:
                            attribute_dict[i.nodeName][
                                j.nodeName
                            ] = j.firstChild.nodeValue

        catalogue["catalogueAttributes"][code] = attribute_dict

    del attribute_nodes, attribute_dict

    # parsing the <catalogueTerms> node
    vprint("parsing the <catalogueTerms> node...")

    term_nodes = foodex_xml.getElementsByTagName("term")

    if args.termsfile:
        catalogue_terms = []
    else:
        catalogue["catalogueTerms"] = OrderedDict()

    for term_node in term_nodes:
        # checking whether the term should be filtered out
        hierarchy_codes = set()

        for i in term_node.getElementsByTagName("hierarchyCode"):
            hierarchy_codes.add(i.firstChild.nodeValue)

        # MTX hierarchy is by default always present
        if len(hierarchy_codes.difference(args.discardedhierarchies)) <= 1:
            continue
        else:
            generic_term_counter += 1

        termCode = term_node.getElementsByTagName("termCode")[0].firstChild.nodeValue

        term_dict = OrderedDict()

        if args.cookbase:
            term_dict["_id"] = termcode.to_int(termCode)

        for i in term_node.childNodes:
            if i.nodeType != i.TEXT_NODE:
                term_dict[i.nodeName] = OrderedDict()

                if i.nodeName == "hierarchyAssignments":
                    for j in i.childNodes:
                        if j.nodeType != j.TEXT_NODE:
                            hierarchy_code = j.getElementsByTagName("hierarchyCode")[
                                0
                            ].firstChild.nodeValue

                            # updating counter
                            if hierarchy_code == "expo":
                                expo_term_counter += 1

                            # checking discarded hierarchy
                            if hierarchy_code in args.discardedhierarchies:
                                continue

                            term_dict[i.nodeName][hierarchy_code] = OrderedDict()

                            for k in j.childNodes:
                                if k.nodeType != k.TEXT_NODE:
                                    if k.nodeName == "order":
                                        term_dict[i.nodeName][hierarchy_code][
                                            k.nodeName
                                        ] = int(k.firstChild.nodeValue)
                                    elif k.nodeName == "reportable":
                                        if k.firstChild.nodeValue == "true":
                                            term_dict[i.nodeName][hierarchy_code][
                                                k.nodeName
                                            ] = True
                                        else:
                                            term_dict[i.nodeName][hierarchy_code][
                                                k.nodeName
                                            ] = False
                                    else:
                                        term_dict[i.nodeName][hierarchy_code][
                                            k.nodeName
                                        ] = k.firstChild.nodeValue
                elif i.nodeName == "implicitAttributes":
                    for j in i.childNodes:
                        if j.nodeType != j.TEXT_NODE:
                            for k in j.childNodes:
                                if k.nodeName == "attributeCode":
                                    attributeCode = k.firstChild.nodeValue
                                    break

                            attributeValues_list = []

                            for k in j.childNodes:
                                if k.nodeName == "attributeValues":
                                    for q in k.childNodes:
                                        if q.nodeType != q.TEXT_NODE:
                                            attributeValues_list.append(
                                                q.firstChild.nodeValue
                                            )

                                    term_dict[i.nodeName][
                                        attributeCode
                                    ] = attributeValues_list
                else:
                    for j in i.childNodes:
                        if j.nodeType != j.TEXT_NODE:
                            term_dict[i.nodeName][j.nodeName] = j.firstChild.nodeValue

        if args.termsfile:
            catalogue_terms.append(term_dict)
        else:
            catalogue["catalogueTerms"][termCode] = term_dict

    del term_node, term_dict

    vprint("writing output...")

    with open(args.outputfile, "w") as f:
        json.dump(catalogue, f, indent=2)

    if args.termsfile:
        if args.single:
            for i in catalogue_terms:
                with open(
                    args.termsfile + "/" + i["termDesc"]["termCode"] + ".json", "w"
                ) as f:
                    json.dump(i, f, indent=2)
        elif args.nchunks:
            split_index = ceil(len(catalogue_terms) / args.nchunks)
            for i in range(1, args.nchunks + 1):
                start = split_index * (i - 1)
                end = split_index * i
                with open(args.termsfile + "." + str(i), "w") as f:
                    json.dump(catalogue_terms[start:end], f, indent=2)
        else:
            with open(args.termsfile, "w") as f:
                json.dump(catalogue_terms, f, indent=2)

    vprint("Time elapsed: " + str(ceil(time() - start_time)) + " seconds")
    vprint("Total number of terms: " + str(generic_term_counter))
    vprint("Number of terms in the Exposure Hierarchy: " + str(expo_term_counter))


def _traverse_hierarchy(
    hierarchy_siblings: Dict[str, Any],
    term_to_attach: Optional[Tuple[str, str, Dict[str, Any]]] = None,
) -> bool:
    """Generates a JSON document describing a hierarchy tree.

    :param hierarchy_siblings: A dictionary describing all (already scanned) hierarchy
      terms sharing the same parent
    :type hierarchy_siblings: dict[str, Any]
    :param term_to_attach: Data describing a term to be attached to hierarchy
    :type term_to_attach: tuple[str, str, dict[str, Any]], optional
    :return: :const:`True` if a term was attached to hierarchy, :const:`False` otherwise
    :rtype: bool
    """
    for i in hierarchy_siblings.values():
        if term_to_attach and i["termCode"] == term_to_attach[0]:
            try:
                i["children"][term_to_attach[1]] = term_to_attach[2]
            except KeyError:
                i["children"] = {}
                i["children"][term_to_attach[1]] = term_to_attach[2]
            return True
        elif "children" in i and _traverse_hierarchy(i["children"], term_to_attach):
            return True

    return False


def hierarchize(args: argparse.Namespace) -> None:
    """Generates a JSON document describing a hierarchy tree.

    :param args: Command-line arguments
    :type args: argparse.Namespace
    """
    hierarchy = {}
    buffer = []
    start_time = time()
    hierarchy_term_counter = 0

    vprint("loading terms and including them selectively by hierarchy...")

    for e in os.scandir(args.inputfolder):
        if e.path.endswith(".json"):
            with open(e.path) as f:
                term = json.load(f)
            try:
                parent_code = term["hierarchyAssignments"][args.hierarchycode][
                    "parentCode"
                ]
            except KeyError:
                continue

            tta = (
                parent_code,
                term["termDesc"]["termExtendedName"],
                {
                    "termCode": term["termDesc"]["termCode"],
                    "reportable": term["hierarchyAssignments"][args.hierarchycode][
                        "reportable"
                    ],
                    "order": term["hierarchyAssignments"][args.hierarchycode]["order"],
                },
            )

            if parent_code == "root":
                hierarchy[term["termDesc"]["termExtendedName"]] = tta[2]
            elif not _traverse_hierarchy(hierarchy, tta):
                buffer.append(tta)

            hierarchy_term_counter += 1

    vprint("clearing pool of unattached hierarchy terms...")

    while len(buffer) > 0:
        for i in buffer:
            if _traverse_hierarchy(hierarchy, i):
                buffer.remove(i)

    vprint("writing output...")

    with open(args.outputfile, "w") as f:
        json.dump(hierarchy, f, indent=2)

    vprint("Time elapsed: " + str(ceil(time() - start_time)) + " seconds")
    vprint("Total number of terms in hierarchy: " + str(hierarchy_term_counter))


def _main() -> None:
    """Command-line parser."""
    ap = argparse.ArgumentParser(
        description="jsonfoodex - A parsing suite"
        + " for the Cookbase platform which"
        + " transforms from the standard FoodEx2"
        + " XML-formatted file into JSON files.",
        add_help=False,
    )
    ap.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help message and exit"
    )
    subparsers = ap.add_subparsers(dest="command")
    subparsers.required = True
    parsexml_parser = subparsers.add_parser(
        "parsexml", help="parse a FoodEx2 XML file into JSON files"
    )
    parsexml_parser.add_argument("inputfile", help="path to the XML input file")
    parsexml_parser.add_argument("outputfile", help="path to the JSON output file")
    parsexml_parser.add_argument(
        "-t",
        "--termsfile",
        help="path to the JSON separated output file for "
        + "FoodEx2 terms, or folder if flag -s is used",
    )
    pg = parsexml_parser.add_mutually_exclusive_group()
    pg.add_argument(
        "-n",
        "--nchunks",
        type=int,
        help="number of chunks to split the terms output file",
    )
    pg.add_argument(
        "-s",
        "--single",
        action="store_true",
        help="indicate output terms in single files",
    )
    parsexml_parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase output verbosity"
    )
    parsexml_parser.add_argument(
        "-d",
        "--discardedhierarchies",
        nargs="*",
        default=[
            "botanic",
            "pest",
            "biomo",
            "legis",
            "feed",
            "partcon",
            "place",
            "vetdrug",
            "report",
            "fpurpose",
            "replev",
            "targcon",
            "feedAddExpo",
        ],
        help="List of hierarchies to be discarded by the "
        + "parser. Not indicating this assigns the default "
        + "discarded hierarchies, and using it without any "
        + "elements means no hierarchy will be discarded.",
    )
    parsexml_parser.add_argument(
        "-cb",
        "--cookbase",
        action="store_true",
        help="activate identifier generation ('_id') for " + "Cookbase platform",
    )
    parsexml_parser.set_defaults(func=parsexml)

    hierarchize_parser = subparsers.add_parser(
        "hierarchize", help="build JSON document describing a hierarchy"
    )
    hierarchize_parser.add_argument(
        "inputfolder", help="path to the directory including single term" + " files"
    )
    hierarchize_parser.add_argument("outputfile", help="path to the JSON output file")
    hierarchize_parser.add_argument(
        "hierarchycode", help="code of the hierarchy to build"
    )
    hierarchize_parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase output verbosity"
    )
    hierarchize_parser.set_defaults(func=hierarchize)
    args = ap.parse_args()

    # checking command-line arguments correctness
    if args.command == "parsexml":
        if (args.nchunks is not None or args.single == True) and args.termsfile == None:
            ap.error(
                "-n/--nchunks and -s/--single can only be used if -t/--termsfile"
                + " is declared"
            )

    global vprint
    vprint = print if args.verbose > 0 else lambda _: None
    args.func(args)


if __name__ == "__main__":
    _main()
