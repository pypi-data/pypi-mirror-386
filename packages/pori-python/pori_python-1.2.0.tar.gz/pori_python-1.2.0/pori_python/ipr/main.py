from __future__ import annotations

import argparse
import datetime
import json
import jsonschema.exceptions
import logging
import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Callable, Dict, List, Sequence, Set

from pori_python.graphkb import GraphKBConnection
from pori_python.graphkb.genes import get_gene_information
from pori_python.types import (
    Hashabledict,
    IprCopyVariant,
    IprExprVariant,
    IprSignatureVariant,
    IprSmallMutationVariant,
    IprStructuralVariant,
    IprVariant,
)

from .annotate import annotate_variants
from .connection import IprConnection
from .constants import DEFAULT_URL, TMB_SIGNATURE_HIGH_THRESHOLD
from .inputs import (
    check_comparators,
    check_variant_links,
    preprocess_copy_variants,
    preprocess_cosmic,
    preprocess_expression_variants,
    preprocess_hla,
    preprocess_msi,
    preprocess_signature_variants,
    preprocess_small_mutations,
    preprocess_structural_variants,
    preprocess_tmb,
    validate_report_content,
)
from .ipr import (
    create_key_alterations,
    filter_structural_variants,
    germline_kb_matches,
    get_kb_disease_matches,
    get_kb_matches_sections,
    select_expression_plots,
)
from .summary import auto_analyst_comments, get_ipr_analyst_comments
from .therapeutic_options import create_therapeutic_options
from .util import LOG_LEVELS, logger, trim_empty_values

CACHE_GENE_MINIMUM = 5000
RENAMED_GENE_PROPERTIES = {
    # old_name: new_name
    "cancerRelated": "kbStatementRelated",
    "cancerGene": "cancerGeneListMatch",
}


def file_path(path: str) -> str:
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"{repr(path)} is not a valid filename. does not exist")
    return path


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def command_interface() -> None:
    """Parse the ipr command from user input based on usage pattern.
    Parsed arguments are used to call the ipr_report() function.
    """
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    req = parser.add_argument_group("required arguments")
    (req if not os.environ.get("USER") else parser).add_argument(
        "--username",
        required=not os.environ.get("USER"),
        default=os.environ.get("USER"),
        help="username to use connecting to graphkb/ipr",
    )
    req.add_argument("--password", required=True, help="password to use connecting to graphkb/ipr")
    req.add_argument(
        "-c", "--content", required=True, type=file_path, help="Report Content as JSON"
    )

    parser.add_argument("--ipr_url", default=os.environ.get("IPR_URL", DEFAULT_URL))
    parser.add_argument(
        "--graphkb_username",
        help="username to use connecting to graphkb if different from ipr",
    )
    parser.add_argument(
        "--graphkb_password",
        help="password to use connecting to graphkb if different from ipr",
    )
    parser.add_argument("--graphkb_url", default=os.environ.get("GRAPHKB_URL", None))
    parser.add_argument("--log_level", default="info", choices=LOG_LEVELS.keys())
    parser.add_argument(
        "--therapeutics",
        default=False,
        help="Generate therapeutic options",
        action="store_true",
    )
    parser.add_argument(
        "--skip_comments",
        default=False,
        action="store_true",
        help="Turn off generating the analyst comments section of the report",
    )
    parser.add_argument(
        "-o",
        "--output_json_path",
        default=f"pori_python_report_{timestamp()}.json",
        help="path to a JSON to output the report upload body",
    )
    parser.add_argument(
        "-w",
        "--always_write_output_json",
        action="store_true",
        help="Write to output_json_path on successful IPR uploads instead of just when the upload fails",
    )
    parser.add_argument(
        "--async_upload",
        default=False,
        action="store_true",
        help="True if reports-async ipr endpoint should be used instead of basic reports",
    )
    parser.add_argument(
        "--mins_to_wait",
        default=5,
        action="store",
        help="is using reports-async, number of minutes to wait before throwing error",
    )
    parser.add_argument(
        "--allow_partial_matches",
        default=False,
        action="store_true",
        help="True to include matches to multivariant statements where not all variants are present",
    )
    parser.add_argument(
        "--upload_json",
        default=False,
        action="store_true",
        help="True to skip all the preprocessing and just submit a json to ipr",
    )
    parser.add_argument(
        "--validate_json",
        default=False,
        action="store_true",
        help="True if only need to validate the json",
    )
    parser.add_argument(
        "--ignore_extra_fields",
        default=False,
        action="store_true",
        help="True if ignore extra fields in json",
    )
    args = parser.parse_args()

    with open(args.content, "r") as fh:
        content = json.load(fh)

    ipr_report(
        username=args.username,
        password=args.password,
        content=content,
        ipr_url=args.ipr_url,
        graphkb_username=args.graphkb_username,
        graphkb_password=args.graphkb_password,
        graphkb_url=args.graphkb_url,
        log_level=args.log_level,
        output_json_path=args.output_json_path,
        always_write_output_json=args.always_write_output_json,
        generate_therapeutics=args.therapeutics,
        generate_comments=not args.skip_comments,
        async_upload=args.async_upload,
        mins_to_wait=args.mins_to_wait,
        allow_partial_matches=args.allow_partial_matches,
        upload_json=args.upload_json,
        validate_json=args.validate_json,
        ignore_extra_fields=args.ignore_extra_fields,
    )


def clean_unsupported_content(upload_content: Dict, ipr_spec: Dict = {}) -> Dict:
    """Remove unsupported content.
    This content is either added to facilitate creation
    or to support upcoming and soon to be supported content that we would like
    to implement but is not yet supported by the upload
    """
    if (
        ipr_spec
        and "components" in ipr_spec.keys()
        and "schemas" in ipr_spec["components"].keys()
        and "genesCreate" in ipr_spec["components"]["schemas"].keys()
        and "properties" in ipr_spec["components"]["schemas"]["genesCreate"].keys()
    ):
        genes_spec = ipr_spec["components"]["schemas"]["genesCreate"]["properties"].keys()

        # check what ipr report upload expects and adjust contents to match
        for old_name, new_name in RENAMED_GENE_PROPERTIES.items():
            if old_name in genes_spec:
                logger.warning(
                    f"Legacy IPR - Renaming property {new_name} to {old_name} for compatibility to ipr_spec"
                )
                for gene in upload_content["genes"]:
                    if new_name in gene:
                        gene[old_name] = gene[new_name]
                        gene.pop(new_name)
            else:
                outdate_properties = 0
                for gene in upload_content["genes"]:
                    if old_name in gene:
                        gene[new_name] = gene[old_name]
                        gene.pop(old_name)
                        outdate_properties += 1
                if outdate_properties:
                    logger.warning(
                        f"Renamed property {old_name} to {new_name} on {outdate_properties} genes for ipr_spec"
                    )

        # remove any unhandled incompatible keys
        removed_keys: Dict[str, int] = {}
        for gene in upload_content["genes"]:
            unsupported_keys = [key for key in gene.keys() if key not in genes_spec]
            for key in unsupported_keys:
                if key in removed_keys:
                    removed_keys[key] += 1
                else:
                    removed_keys[key] = 1
                gene.pop(key)
        for key, count in removed_keys.items():
            logger.warning(f"IPR unsupported property '{key}' removed from {count} genes.")

    drop_columns = ["variant", "variantType", "histogramImage"]
    # DEVSU-2034 - use a 'displayName'
    VARIANT_LIST_KEYS = [
        "expressionVariants",
        "smallMutations",
        "copyVariants",
        "structuralVariants",
        "probeResults",
        "signatureVariants",
    ]
    for variant_list_section in VARIANT_LIST_KEYS:
        for variant in upload_content.get(variant_list_section, []):
            if not variant.get("displayName"):
                variant["displayName"] = (
                    variant.get("variant") or variant.get("kbCategory") or variant.get("key", "")
                )
            if variant_list_section == "probeResults":
                # currently probeResults will error if they do NOT have a 'variant' column.
                # smallMutations will error if they DO have a 'variant' column.
                continue
            for col in drop_columns:
                if col in variant:
                    del variant[col]
    # tmburMutationBurden is a single value, not list
    if upload_content.get("tmburMutationBurden"):
        if not upload_content["tmburMutationBurden"].get("displayName"):
            upload_content["tmburMutationBurden"]["displayName"] = upload_content[
                "tmburMutationBurden"
            ].get("kbCategory", "")

    # TODO: check this is still necessary
    for row in upload_content["kbMatches"]:
        if "kbContextId" in row:
            del row["kbContextId"]
        if "kbRelevanceId" in row:
            del row["kbRelevanceId"]
        if "requiredKbMatches" in row:
            del row["requiredKbMatches"]

    for row in upload_content["kbMatchedStatements"]:
        if "kbContextId" in row:
            del row["kbContextId"]
        if "kbRelevanceId" in row:
            del row["kbRelevanceId"]

    # Removing cosmicSignatures. Temporary
    upload_content.pop("cosmicSignatures", None)

    return upload_content


def create_report(**kwargs) -> Dict:
    logger.warning("Deprecated function 'create_report' called - use ipr_report instead")
    return ipr_report(**kwargs)


def ipr_report(
    username: str,
    password: str,
    content: Dict,
    ipr_url: str = DEFAULT_URL,
    log_level: str = "info",
    output_json_path: str = "",
    always_write_output_json: bool = False,
    ipr_upload: bool = True,
    interactive: bool = False,
    graphkb_username: str = "",
    graphkb_password: str = "",
    graphkb_url: str = "",
    generate_therapeutics: bool = False,
    generate_comments: bool = True,
    match_germline: bool = False,
    custom_kb_match_filter: Callable = None,
    async_upload: bool = False,
    mins_to_wait: int = 5,
    include_ipr_variant_text: bool = True,
    include_nonspecific_disease: bool = False,
    include_nonspecific_project: bool = False,
    include_nonspecific_template: bool = False,
    allow_partial_matches: bool = False,
    upload_json: bool = False,
    validate_json: bool = False,
    ignore_extra_fields: bool = False,
    tmb_high: float = TMB_SIGNATURE_HIGH_THRESHOLD,
) -> Dict:
    """Run the matching and create the report JSON for upload to IPR.

    Args:
        username: the username for connecting to GraphKB and IPR
        password: the password for connecting to GraphKB and IPR
        ipr_url: base URL to use in connecting to IPR
        log_level: the logging level
        content: report content
        output_json_path: path to a JSON file to output the report upload body.
        always_write_output_json: with successful IPR upload
        ipr_upload: upload report to ipr
        interactive: progressbars for interactive users
        cache_gene_minimum: minimum number of genes required for gene name caching optimization
        graphkb_username: the username for connecting to GraphKB if diff from IPR
        graphkb_password: the password for connecting to GraphKB if diff from IPR
        graphkb_url: the graphkb url to use if not default
        generate_therapeutics: create therapeutic options for upload with the report
        generate_comments: create the analyst comments section for upload with the report
        match_germline: match only germline statements to germline events and non-germline statements to non-germline events.
        custom_kb_match_filter: function(List[kbMatch]) -> List[kbMatch]
        async_upload: use report_async endpoint to upload reports
        mins_to_wait: if using report_async, number of minutes to wait for success before exception raised
        include_ipr_variant_text: if True, include output from the ipr variant-texts endpoint in analysis comments
        include_nonspecific_disease: if include_ipr_variant_text is True, if no disease match is found use disease-nonspecific variant comment
        include_nonspecific_project: if include_ipr_variant_text is True, if no project match is found use project-nonspecific variant comment
        include_nonspecific_template: if include_ipr_variant_text is True, if no template match is found use template-nonspecific variant comment
        allow_partial_matches: allow matches to statements where not all conditions are satisfied
        tmb_high: mutation burden threshold/cutoff to qualify as 'high'
    Returns:
        ipr_conn.upload_report return dictionary
    """
    # set the default logging configuration
    logging.basicConfig(
        level=LOG_LEVELS[log_level],
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%m-%d-%y %H:%M:%S",
    )

    # IPR CONNECTION
    ipr_conn = IprConnection(username, password, ipr_url)

    if validate_json:
        ipr_result = ipr_conn.validate_json(content)
        return ipr_result

    if upload_json:
        ipr_result = ipr_conn.upload_report(
            content, mins_to_wait, async_upload, ignore_extra_fields
        )
        return ipr_result

    # validate the JSON content follows the specification
    try:
        validate_report_content(content)
    except jsonschema.exceptions.ValidationError as err:
        logger.error("Failed schema check - report variants may be corrupted or unmatched.")
        logger.error(f"Failed schema check: {err}")

    # INPUT VARIANTS VALIDATION & PREPROCESSING (OBSERVED BIOMARKERS)
    signature_variants: List[IprSignatureVariant] = preprocess_signature_variants(
        [
            *preprocess_cosmic(content.get("cosmicSignatures", [])),  # includes dMMR
            *preprocess_hla(content.get("hlaTypes", [])),
            *preprocess_tmb(
                tmb_high,
                content.get("tmburMutationBurden", None),  # old tmb pipeline
                content.get("genomeTmb", None),  # newer tmb pipeline
            ),
            *preprocess_msi(content.get("msi", None)),
        ]
    )
    small_mutations: List[IprSmallMutationVariant] = preprocess_small_mutations(
        content.get("smallMutations", [])
    )
    structural_variants: List[IprStructuralVariant] = preprocess_structural_variants(
        content.get("structuralVariants", [])
    )
    copy_variants: List[IprCopyVariant] = preprocess_copy_variants(content.get("copyVariants", []))
    expression_variants: List[IprExprVariant] = preprocess_expression_variants(
        content.get("expressionVariants", [])
    )
    # Additional checks
    if expression_variants:
        check_comparators(content, expression_variants)

    genes_with_variants: Set[str] = check_variant_links(
        small_mutations, expression_variants, copy_variants, structural_variants
    )

    # GKB CONNECTION
    if graphkb_url:
        logger.info(f"connecting to graphkb: {graphkb_url}")
        graphkb_conn = GraphKBConnection(graphkb_url)
    else:
        graphkb_conn = GraphKBConnection()

    gkb_user = graphkb_username if graphkb_username else username
    gkb_pass = graphkb_password if graphkb_password else password

    graphkb_conn.login(gkb_user, gkb_pass)

    # DISEASE
    # Disease term from bioapps; expected OncoTree term
    kb_disease_match: str = content["kbDiseaseMatch"]

    # Matching disease RIDs from GraphKB using term tree
    # (Will raise uncatched error if no match)
    disease_matches: list[str] = get_kb_disease_matches(graphkb_conn, kb_disease_match)

    # GKB MATCHING (AKA ANNOTATION)
    gkb_matches: List[Hashabledict] = annotate_variants(
        graphkb_conn=graphkb_conn,
        interactive=interactive,
        disease_matches=disease_matches,
        # Variants, per type:
        signature_variants=signature_variants,
        small_mutations=small_mutations,
        structural_variants=structural_variants,
        copy_variants=copy_variants,
        expression_variants=expression_variants,
    )

    # GROUPING ALL VARIANTS TOGETHER
    all_variants: Sequence[IprVariant] = [
        *copy_variants,
        *expression_variants,
        *signature_variants,
        *small_mutations,
        *structural_variants,
    ]  # type: ignore

    # GKB_MATCHES FILTERING
    if match_germline:
        # verify germline kb statements matched germline observed variants, not somatic variants
        org_len = len(gkb_matches)
        gkb_matches = [
            Hashabledict(match) for match in germline_kb_matches(gkb_matches, all_variants)
        ]
        num_removed = org_len - len(gkb_matches)
        if num_removed:
            logger.info(f"Removing {num_removed} germline events without medical matches.")

    if custom_kb_match_filter:
        logger.info(f"custom_kb_match_filter on {len(gkb_matches)} variants")
        gkb_matches = [Hashabledict(match) for match in custom_kb_match_filter(gkb_matches)]
        logger.info(f"\t custom_kb_match_filter left {len(gkb_matches)} variants")

    # KEY ALTERATIONS
    key_alterations, variant_counts = create_key_alterations(gkb_matches, all_variants)

    # GENE INFORMATION
    logger.info("fetching gene annotations")
    gene_information = get_gene_information(graphkb_conn, sorted(genes_with_variants))

    # THERAPEUTIC OPTIONS
    if generate_therapeutics:
        logger.info("generating therapeutic options")
        targets = create_therapeutic_options(graphkb_conn, gkb_matches, all_variants)
    else:
        targets = []

    # ANALYST COMMENTS
    logger.info("generating analyst comments")

    comments_list = []
    if generate_comments:
        graphkb_comments = auto_analyst_comments(
            graphkb_conn,
            gkb_matches,
            disease_matches=set(disease_matches),
            variants=all_variants,
        )
        comments_list.append(graphkb_comments)

    if include_ipr_variant_text:
        ipr_comments = get_ipr_analyst_comments(
            ipr_conn,
            gkb_matches,
            disease_name=kb_disease_match,
            project_name=content["project"],
            report_type=content["template"],
            include_nonspecific_disease=include_nonspecific_disease,
            include_nonspecific_project=include_nonspecific_project,
            include_nonspecific_template=include_nonspecific_template,
        )
        comments_list.append(ipr_comments)
    comments = {'comments': "\n".join(comments_list)}

    # REFORMATTING KBMATCHES
    # kbMatches -> kbMatches, kbMatchedStatements & kbStatementMatchedConditions
    kb_matched_sections = get_kb_matches_sections(
        gkb_matches, allow_partial_matches=allow_partial_matches
    )

    # OUTPUT CONTENT
    # thread safe deep-copy the original content
    output = json.loads(json.dumps(content))

    output.update(kb_matched_sections)
    output.update(
        {
            "copyVariants": [
                trim_empty_values(c) for c in copy_variants if c["gene"] in genes_with_variants
            ],
            "smallMutations": [trim_empty_values(s) for s in small_mutations],
            "expressionVariants": [
                trim_empty_values(e)
                for e in expression_variants
                if e["gene"] in genes_with_variants
            ],
            "kbDiseaseMatch": kb_disease_match,
            "kbUrl": graphkb_conn.url,
            "kbVersion": timestamp(),
            "structuralVariants": [
                trim_empty_values(s)
                for s in filter_structural_variants(
                    structural_variants, gkb_matches, gene_information
                )
            ],
            "signatureVariants": [trim_empty_values(s) for s in signature_variants],
            "genes": gene_information,
            "genomicAlterationsIdentified": key_alterations,
            "variantCounts": variant_counts,
            "analystComments": comments,
            "therapeuticTarget": targets,
        }
    )
    output.setdefault("images", []).extend(select_expression_plots(gkb_matches, all_variants))

    ipr_spec = ipr_conn.get_spec()
    output = clean_unsupported_content(output, ipr_spec)
    ipr_result = None
    upload_error = None

    # UPLOAD TO IPR
    if ipr_upload:
        try:
            logger.info(f"Uploading to IPR {ipr_conn.url}")
            ipr_result = ipr_conn.upload_report(
                output, mins_to_wait, async_upload, ignore_extra_fields
            )
            logger.info(ipr_result)
            output.update(ipr_result)
        except Exception as err:
            upload_error = err
            logger.error(f"ipr_conn.upload_report failed: {err}", exc_info=True)

    # SAVE TO JSON FILE
    if always_write_output_json:
        logger.info(f"Writing IPR upload json to: {output_json_path}")
        with open(output_json_path, "w") as fh:
            fh.write(json.dumps(output))

    logger.info(f"made {graphkb_conn.request_count} requests to graphkb")
    logger.info(f"average load {int(graphkb_conn.load or 0)} req/s")
    if upload_error:
        raise upload_error
    return output
