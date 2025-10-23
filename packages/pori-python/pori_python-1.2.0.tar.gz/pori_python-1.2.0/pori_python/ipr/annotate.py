"""
handles annotating variants with annotation information from graphkb
"""

from __future__ import annotations

from requests.exceptions import HTTPError

from pandas import isnull
from tqdm import tqdm
from typing import Dict, List, Sequence

from pori_python.graphkb import GraphKBConnection
from pori_python.graphkb import match as gkb_match
from pori_python.graphkb.match import INPUT_COPY_CATEGORIES
from pori_python.graphkb.statement import get_statements_from_variants
from pori_python.graphkb.util import FeatureNotFoundError
from pori_python.types import (
    Hashabledict,
    IprCopyVariant,
    IprExprVariant,
    IprSignatureVariant,
    IprSmallMutationVariant,
    IprStructuralVariant,
    KbMatch,
    Statement,
    Variant,
)

from .constants import TMB_SIGNATURE
from .ipr import convert_statements_to_alterations
from .util import convert_to_rid_set, logger

REPORTED_COPY_VARIANTS = (INPUT_COPY_CATEGORIES.AMP, INPUT_COPY_CATEGORIES.DEEP)


def get_second_pass_variants(
    graphkb_conn: GraphKBConnection, statements: List[Statement]
) -> List[Variant]:
    """Given a list of statements that have been matched, convert these to
    new category variants to be used in a second-pass matching.
    """
    # second-pass matching
    all_inferred_matches: Dict[str, Variant] = {}
    inferred_variants = {
        (s["subject"]["@rid"], s["relevance"]["name"])
        for s in statements
        if s["subject"] and s["subject"]["@class"] in ("Feature", "Signature")
    }

    for reference1, variant_type in inferred_variants:
        variants = gkb_match.match_category_variant(graphkb_conn, reference1, variant_type)

        for variant in variants:
            all_inferred_matches[variant["@rid"]] = variant
    inferred_matches: List[Variant] = list(all_inferred_matches.values())
    return inferred_matches


def get_ipr_statements_from_variants(
    graphkb_conn: GraphKBConnection, matches: List[Variant], disease_matches: List[str]
) -> List[KbMatch]:
    """IPR upload formatted GraphKB statements from the list of variants.

    Matches to GraphKB statements from the list of input variants. From these results matches
    again with the inferred variants. Then returns the results formatted for upload to IPR
    """
    if not matches:
        return []
    rows = []

    statements = get_statements_from_variants(graphkb_conn, matches)
    existing_statements = {s["@rid"] for s in statements}

    for ipr_row in convert_statements_to_alterations(
        graphkb_conn, statements, disease_matches, convert_to_rid_set(matches)
    ):
        rows.append(ipr_row)

    # second-pass matching
    inferred_matches = get_second_pass_variants(graphkb_conn, statements)

    inferred_statements = [
        s
        for s in get_statements_from_variants(graphkb_conn, inferred_matches)
        if s["@rid"] not in existing_statements  # do not duplicate if non-inferred match
    ]

    for ipr_row in convert_statements_to_alterations(
        graphkb_conn,
        inferred_statements,
        disease_matches,
        convert_to_rid_set(inferred_matches),
    ):
        ipr_row["kbData"]["inferred"] = True
        rows.append(ipr_row)

    return rows


def annotate_expression_variants(
    graphkb_conn: GraphKBConnection,
    disease_matches: List[str],
    variants: List[IprExprVariant],
    show_progress: bool = False,
) -> List[KbMatch]:
    """Annotate expression variants with GraphKB in the IPR alterations format.

    Args:
        graphkb_conn (GraphKBConnection): the graphkb api connection object
        disease_matches (list.str): GraphKB disease RIDs
        variants (list.IprExprVariant): list of variants.
        show_progress (bool): Progressbar displayed for long runs.

    Returns:
        list of kbMatches records for IPR
    """
    skipped = 0
    alterations = []
    problem_genes = set()
    logger.info(f"Starting annotation of {len(variants)} expression category_variants")
    iterfunc = tqdm if show_progress else iter
    for row in iterfunc(variants):
        gene = row["gene"]
        variant = row["variant"]

        if not variant:
            skipped += 1
            logger.debug(f"Skipping malformed Expression {gene}: {row}")
            continue
        try:
            matches = gkb_match.match_expression_variant(graphkb_conn, gene, variant)
            for ipr_row in get_ipr_statements_from_variants(graphkb_conn, matches, disease_matches):
                ipr_row["variant"] = row["key"]
                ipr_row["variantType"] = row.get("variantType", "exp")
                alterations.append(ipr_row)
        except FeatureNotFoundError as err:
            problem_genes.add(gene)
            logger.debug(f"Unrecognized gene ({gene} {variant}): {err}")
        except ValueError as err:
            logger.error(f"failed to match variants ({gene} {variant}): {err}")

    if skipped:
        logger.info(f"skipped matching {skipped} expression information rows")
    if problem_genes:
        logger.error(f"gene finding failures for expression {sorted(problem_genes)}")
        logger.error(f"gene finding falure for {len(problem_genes)} expression genes")
    logger.info(
        f"matched {len(variants)} expression variants to {len(alterations)} graphkb annotations"
    )
    return alterations


def annotate_copy_variants(
    graphkb_conn: GraphKBConnection,
    disease_matches: List[str],
    variants: List[IprCopyVariant],
    show_progress: bool = False,
) -> List[KbMatch]:
    """Annotate allowed copy variants with GraphKB in the IPR alterations format.

    Args:
        graphkb_conn (GraphKBConnection): the graphkb api connection object
        disease_matches (list.str): GraphKB disease RIDs
        variants (list.IprCopyVariant): list of variants.
        show_progress (bool): Progressbar displayed for long runs.

    Returns:
        list of kbMatches records for IPR
    """
    skipped = 0
    alterations = []
    problem_genes = set()

    logger.info(f"Starting annotation of {len(variants)} copy category_variants")
    iterfunc = tqdm if show_progress else iter
    for row in iterfunc(variants):
        gene = row["gene"]
        variant = row["variant"]

        if variant not in REPORTED_COPY_VARIANTS:
            # https://www.bcgsc.ca/jira/browse/GERO-77
            skipped += 1
            logger.debug(f"Dropping {gene} copy change '{variant}' - not in REPORTED_COPY_VARIANTS")
            continue
        try:
            matches = gkb_match.match_copy_variant(graphkb_conn, gene, variant)
            for ipr_row in get_ipr_statements_from_variants(graphkb_conn, matches, disease_matches):
                ipr_row["variant"] = row["key"]
                ipr_row["variantType"] = row.get("variantType", "cnv")
                alterations.append(ipr_row)
        except FeatureNotFoundError as err:
            problem_genes.add(gene)
            logger.debug(f"Unrecognized gene ({gene} {variant}): {err}")
        except ValueError as err:
            logger.error(f"failed to match variants ({gene} {variant}): {err}")

    if skipped:
        logger.info(
            f"skipped matching {skipped} copy number variants not in {REPORTED_COPY_VARIANTS}"
        )
    if problem_genes:
        logger.error(f"gene finding failures for copy variants {sorted(problem_genes)}")
        logger.error(f"gene finding failure for {len(problem_genes)} copy variant genes")
    logger.info(
        f"matched {len(variants)} copy category variants to {len(alterations)} graphkb annotations"
    )
    return alterations


def annotate_positional_variants(
    graphkb_conn: GraphKBConnection,
    variants: Sequence[IprStructuralVariant] | Sequence[Hashabledict],
    disease_matches: List[str],
    show_progress: bool = False,
) -> List[Hashabledict]:
    """Annotate SNP, INDEL or fusion variant calls with GraphKB and return in IPR match format.

    Hashable type is required to turn lists into sets.
    Args:
        graphkb_conn (GraphKBConnection): the graphkb api connection object
        variants (Sequence): list of variants.
        disease_matches (list.str): GraphKB disease RIDs
        show_progress (bool): Progressbar displayed for long runs.

    Returns:
        Hashable list of kbMatches records for IPR
    """
    VARIANT_KEYS = ("variant", "hgvsProtein", "hgvsCds", "hgvsGenomic")
    errors = 0
    alterations: List[Hashabledict] = []
    problem_genes = set()

    iterfunc = tqdm if show_progress else iter
    for row in iterfunc(variants):
        if not row.get("gene") and (not row.get("gene1") or not row.get("gene2")):
            # https://www.bcgsc.ca/jira/browse/GERO-56?focusedCommentId=1234791&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-1234791
            # should not match single gene SVs
            continue

        for var_key in VARIANT_KEYS:
            variant = row.get(var_key)
            matches = []
            if not variant or isnull(variant):
                continue
            try:
                try:
                    matches = gkb_match.match_positional_variant(graphkb_conn, variant)
                except HTTPError as parse_err:
                    # DEVSU-1885 - fix malformed single deletion described as substitution of blank
                    # eg. deletion described as substitution with nothing: 'chr1:g.150951027T>'
                    if (
                        variant[-1] == ">"
                        and "g." in variant
                        and variant[-2].isalpha()
                        and variant[-3].isnumeric()
                    ):
                        logger.warning(
                            f"Assuming malformed deletion variant {variant} is {variant[:-2] + 'del'}"
                        )
                        variant = variant[:-2] + "del"
                        matches = gkb_match.match_positional_variant(graphkb_conn, variant)
                    else:
                        raise parse_err

                for ipr_row in get_ipr_statements_from_variants(
                    graphkb_conn,
                    matches,
                    disease_matches,
                ):
                    ipr_row["variant"] = row["key"]
                    ipr_row["variantType"] = row.get(
                        "variantType", "mut" if row.get("gene") else "sv"
                    )
                    alterations.append(Hashabledict(ipr_row))

            except FeatureNotFoundError as err:
                logger.debug(f"failed to match positional variants ({variant}): {err}")
                errors += 1
                if "gene" in row:
                    problem_genes.add(row["gene"])
                elif "gene1" in row and f"({row['gene1']})" in str(err):
                    problem_genes.add(row["gene1"])
                elif "gene2" in row and f"({row['gene2']})" in str(err):
                    problem_genes.add(row["gene2"])
                elif "gene1" in row and "gene2" in row:
                    problem_genes.add(row["gene1"])
                    problem_genes.add(row["gene2"])
                else:
                    raise err
            except HTTPError as err:
                errors += 1
                logger.error(f"failed to match positional variants ({variant}): {err}")

    if problem_genes:
        logger.error(f"gene finding failures for {sorted(problem_genes)}")
        logger.error(f"{len(problem_genes)} gene finding failures for positional variants")
    if errors:
        logger.error(f"skipped {errors} positional variants due to errors")

    # drop duplicates
    alterations = list(set(alterations))

    variant_types = ", ".join(sorted(set([alt["variantType"] for alt in alterations])))
    logger.info(
        f"matched {len(variants)} {variant_types} positional variants to {len(alterations)} graphkb annotations"
    )

    return alterations


def annotate_signature_variants(
    graphkb_conn: GraphKBConnection,
    disease_matches: List[str],
    variants: List[IprSignatureVariant] = [],
    show_progress: bool = False,
) -> List[KbMatch]:
    """Annotate Signature variants with GraphKB in the IPR alterations format.

    Match to corresponding GraphKB Variants, then to linked GraphKB Statements

    Args:
        graphkb_conn (GraphKBConnection): the graphkb api connection object
        disease_matches (list.str): GraphKB disease RIDs
        variants (list.IprSignatureVariant): list of signature variants
        show_progress (bool): progressbar displayed for long runs; default to False

    Returns:
        list of kbMatches records for IPR
    """
    alterations: List[Hashabledict] = []

    iterfunc = tqdm if show_progress else iter
    for variant in iterfunc(variants):
        try:
            # Matching signature variant to GKB Variants
            matched_variants: List[Variant] = gkb_match.match_category_variant(
                graphkb_conn,
                variant["signatureName"],
                variant["variantTypeName"],
                reference_class="Signature",
            )
            # KBDEV-1246
            # Keep support for 'high mutation burden' until statement datafix
            if (
                variant["signatureName"] == TMB_SIGNATURE
                and TMB_SIGNATURE != 'high mutation burden'
            ):
                matched_variants.extend(
                    gkb_match.match_category_variant(
                        graphkb_conn,
                        'high mutation burden',
                        variant["variantTypeName"],
                        reference_class="Signature",
                    )
                )
            # Matching GKB Variants to GKB Statements
            for ipr_row in get_ipr_statements_from_variants(
                graphkb_conn, matched_variants, disease_matches
            ):
                ipr_row["variant"] = variant["key"]
                ipr_row["variantType"] = "sigv"
                alterations.append(Hashabledict(ipr_row))

        except ValueError as err:
            logger.error(f"failed to match signature category variant '{variant}': {err}")

    # drop duplicates
    alterations = list(set(alterations))

    logger.info(
        f"matched {len(variants)} signature category variants to {len(alterations)} graphkb annotations"
    )

    return alterations


def annotate_variants(
    graphkb_conn: GraphKBConnection,
    interactive: bool = False,
    disease_matches: List[str] = [],
    signature_variants: List[IprSignatureVariant] = [],
    small_mutations: List[IprSmallMutationVariant] = [],
    structural_variants: List[IprStructuralVariant] = [],
    copy_variants: List[IprCopyVariant] = [],
    expression_variants: List[IprExprVariant] = [],
) -> List[Hashabledict]:
    """Annotating (matching to GraphKB) all observed variants, per type
    Args:
        graphkb_conn: the graphkb api connection object
        interactive: progressbars for interactive users
        disease_matches: list of matched disease RID strings,
        signature_variants: signature CategoryVariants (incl. cosmic, dmmr, hla, tmb & msi),
        small_mutations: small PositionalVariants,
        structural_variants: structural PositionalVariants (incl. fusion)
        copy_variants: copy number CategoryVariants (e.g. of type 'copy loss', 'copy gain', etc.),
        expression_variants: expression CategoryVariant (e.g. of type 'overexpression', etc. ),
    Returns:
        A list of matched Statements to GraphKB
    """
    gkb_matches: List[Hashabledict] = []

    # MATCHING SIGNATURE CATEGORY VARIANTS
    logger.info(f"annotating {len(signature_variants)} signatures")
    gkb_matches.extend(
        annotate_signature_variants(
            graphkb_conn, disease_matches, signature_variants, show_progress=interactive
        )
    )
    logger.debug(f"\tgkb_matches: {len(gkb_matches)}")

    # MATCHING SMALL MUTATIONS
    logger.info(f"annotating {len(small_mutations)} small mutations")
    gkb_matches.extend(
        annotate_positional_variants(
            graphkb_conn, small_mutations, disease_matches, show_progress=interactive
        )
    )
    logger.debug(f"\tgkb_matches: {len(gkb_matches)}")

    # MATCHING STRUCTURAL VARIANTS
    logger.info(f"annotating {len(structural_variants)} structural variants")
    gkb_matches.extend(
        annotate_positional_variants(
            graphkb_conn,
            structural_variants,
            disease_matches,
            show_progress=interactive,
        )
    )
    logger.debug(f"\tgkb_matches: {len(gkb_matches)}")

    # MATCHING COPY VARIANTS
    logger.info(f"annotating {len(copy_variants)} copy variants")
    gkb_matches.extend(
        [
            Hashabledict(copy_var)
            for copy_var in annotate_copy_variants(
                graphkb_conn, disease_matches, copy_variants, show_progress=interactive
            )
        ]
    )
    logger.debug(f"\tgkb_matches: {len(gkb_matches)}")

    # MATCHING EXPRESSION VARIANTS
    logger.info(f"annotating {len(expression_variants)} expression variants")
    gkb_matches.extend(
        [
            Hashabledict(exp_var)
            for exp_var in annotate_expression_variants(
                graphkb_conn,
                disease_matches,
                expression_variants,
                show_progress=interactive,
            )
        ]
    )
    logger.debug(f"\tgkb_matches: {len(gkb_matches)}")

    return gkb_matches
