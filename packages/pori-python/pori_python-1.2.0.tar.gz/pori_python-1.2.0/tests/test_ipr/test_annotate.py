import os
import pytest

from pori_python.graphkb import GraphKBConnection
from pori_python.ipr.annotate import annotate_positional_variants, annotate_signature_variants
from pori_python.ipr.constants import (
    COSMIC_SIGNATURE_VARIANT_TYPE,
    HLA_SIGNATURE_VARIANT_TYPE,
    MSI_MAPPING,
    TMB_SIGNATURE,
    TMB_SIGNATURE_VARIANT_TYPE,
)
from pori_python.ipr.inputs import preprocess_signature_variants
from pori_python.types import IprSmallMutationVariant
from .test_ipr import DISEASE_RIDS

EXCLUDE_BCGSC_TESTS = os.environ.get("EXCLUDE_BCGSC_TESTS") == "1"


# TP53 examples from https://www.bcgsc.ca/jira/browse/SDEV-3122
# Mutations are actually identical but on alternate transcripts.

TP53_MUT_DICT = {
    "pref": IprSmallMutationVariant(  # type: ignore
        {
            "key": "SDEV-3122_preferred",
            "gene": "TP53",
            "hgvsGenomic": "chr17:g.7674252C>T",
            "hgvsCds": "ENST00000269305:c.711G>A",
            "hgvsProtein": "TP53:p.M237I",
        }
    ),
    "intersect": IprSmallMutationVariant(  # type: ignore
        {
            "key": "SDEV-3122_alt",
            "gene": "TP53",
            "hgvsGenomic": "chr17:g.7674252C>T",
            "hgvsCds": "ENST00000610292:c.594G>A",
            "hgvsProtein": "TP53:p.M198I",
        }
    ),
    "prot_only": IprSmallMutationVariant(  # type: ignore
        {"key": "prot_only", "gene": "TP53", "hgvsProtein": "TP53:p.M237I"}
    ),
    "cds_only": IprSmallMutationVariant(  # type: ignore
        {"key": "cds_only", "gene": "TP53", "hgvsCds": "ENST00000269305:c.711G>A"}
    ),
    "genome_only": IprSmallMutationVariant(  # type: ignore
        {"key": "genome_only", "gene": "TP53", "hgvsGenomic": "chr17:g.7674252C>T"}
    ),
}

KBDEV1231_TP53_ERR_MATCH_WT = {
    "altSeq": "",
    "chromosome": "chr17",
    "comments": "",
    "endPosition": "",
    "gene": "TP53",
    "germline": False,
    "hgvsCds": "ENST00000269305:c.853G>A",
    "hgvsGenomic": "chr17:g.7673767C>T",
    "hgvsProtein": "TP53:p.E285K",
    "key": "c23a7b0387335e7a5ed6c1081a1822ae",
    "library": "F145233;F145265",
    "ncbiBuild": "GRCh38",
    "normalAltCount": "",
    "normalDepth": "",
    "normalRefCount": "",
    "proteinChange": "p.E285K",
    "refSeq": "",
    "rnaAltCount": 311,
    "rnaDepth": 370,
    "rnaRefCount": 59,
    "startPosition": "",
    "transcript": "ENST00000269305",
    "tumourAltCopies": "",
    "tumourAltCount": 64,
    "tumourDepth": 100,
    "tumourRefCopies": "",
    "tumourRefCount": 36,
    "variant": "TP53:p.E285K",
    "variantType": "mut",
    "zygosity": "",
}


@pytest.fixture(scope="module")
def graphkb_conn():
    username = os.environ.get("GRAPHKB_USER", os.environ["IPR_USER"])
    password = os.environ.get("GRAPHKB_PASS", os.environ["IPR_PASS"])
    graphkb_url = os.environ.get("GRAPHKB_URL", False)
    if graphkb_url:
        graphkb_conn = GraphKBConnection(graphkb_url)
    else:
        graphkb_conn = GraphKBConnection()
    graphkb_conn.login(username, password)
    return graphkb_conn


@pytest.mark.skipif(
    EXCLUDE_BCGSC_TESTS, reason="excluding tests that depend on BCGSC-specific data"
)
class TestAnnotation:
    def test_annotate_nonsense_vs_missense(self, graphkb_conn):
        """Verify missense (point mutation) is not mistaken for a nonsense (stop codon) mutation."""
        disease = "cancer"
        for key in ("prot_only", "cds_only", "genome_only", "pref"):
            matched = annotate_positional_variants(graphkb_conn, [TP53_MUT_DICT[key]], DISEASE_RIDS)
            # nonsense - stop codon - should not match.  This is missense not nonsense (#164:933).
            nonsense = [a for a in matched if a["kbVariant"] == "TP53 nonsense"]
            assert not nonsense, f"nonsense matched to {key}: {TP53_MUT_DICT[key]}"
            assert matched, f"should have matched in {key}: {TP53_MUT_DICT[key]}"

    def test_annotate_nonsense_vs_missense_protein(self, graphkb_conn):
        """Verify missense (point mutation) is not mistaken for a nonsense (stop codon) mutation."""
        disease = "cancer"
        for key in ("prot_only", "pref"):
            matched = annotate_positional_variants(graphkb_conn, [TP53_MUT_DICT[key]], DISEASE_RIDS)
            # nonsense - stop codon - should not match.  This is missense not nonsense (#164:933).
            nonsense = [a for a in matched if "nonsense" in a["kbVariant"]]
            assert not nonsense, f"nonsense matched to {key}: {TP53_MUT_DICT[key]}"
            assert matched, f"should have matched in {key}: {TP53_MUT_DICT[key]}"

    def test_annotate_signature_variants_cosmic(self, graphkb_conn):
        """Test a Cosmic Signature CVs with known GKB statements"""
        signature = 'SBS10B'
        cosmic = annotate_signature_variants(
            graphkb_conn,
            DISEASE_RIDS,
            preprocess_signature_variants(
                [
                    {
                        "displayName": f"{signature} {COSMIC_SIGNATURE_VARIANT_TYPE}",
                        "signatureName": signature,
                        "variantTypeName": COSMIC_SIGNATURE_VARIANT_TYPE,
                    }
                ]
            ),
        )
        assert len(cosmic) != 0

    @pytest.mark.skip(reason="no GKB statement for dMMR Signature CVs yet")
    def test_annotate_signature_variants_dmmr(self, graphkb_conn):
        """Test a dMMR (from Cosmic) Signature CVs with known GKB statements"""
        signature = 'DMMR'
        dmmr = annotate_signature_variants(
            graphkb_conn,
            DISEASE_RIDS,
            preprocess_signature_variants(
                [
                    {
                        "displayName": f"{signature} {COSMIC_SIGNATURE_VARIANT_TYPE}",
                        "signatureName": signature,
                        "variantTypeName": COSMIC_SIGNATURE_VARIANT_TYPE,
                    }
                ]
            ),
        )
        assert len(dmmr) != 0

    @pytest.mark.skip(reason="no GKB statement for HLA Signature CVs yet")
    def test_annotate_signature_variants_hla(self, graphkb_conn):
        """Test an HLA Signature CVs with known GKB statements"""
        signature = 'HLA-A*02:01'
        hla = annotate_signature_variants(
            graphkb_conn,
            DISEASE_RIDS,
            preprocess_signature_variants(
                [
                    {
                        "displayName": f"{signature} {HLA_SIGNATURE_VARIANT_TYPE}",
                        "signatureName": signature,
                        "variantTypeName": HLA_SIGNATURE_VARIANT_TYPE,
                    }
                ]
            ),
        )
        assert len(hla) != 0

    def test_annotate_signature_variants_tmb(self, graphkb_conn):
        """Test a TMB Signature CVs with known GKB statements"""
        tmb = annotate_signature_variants(
            graphkb_conn,
            DISEASE_RIDS,
            preprocess_signature_variants(
                [
                    {
                        "displayName": f"{TMB_SIGNATURE} {TMB_SIGNATURE_VARIANT_TYPE}",
                        "signatureName": TMB_SIGNATURE,
                        "variantTypeName": TMB_SIGNATURE_VARIANT_TYPE,
                    }
                ]
            ),
        )
        # Should also be matching to 'high mutation burden high signature'
        assert len(tmb) != 0

    def test_annotate_signature_variants_msi(self, graphkb_conn):
        """Test a MSI Signature CVs with known GKB statements"""
        msi = annotate_signature_variants(
            graphkb_conn,
            DISEASE_RIDS,
            preprocess_signature_variants([MSI_MAPPING.get('microsatellite instability')]),
        )
        assert len(msi) != 0

    def test_annotate_structural_variants_tp53(self, graphkb_conn):
        """Verify alternate TP53 variants match."""
        ref_key = "prot_only"
        pref = annotate_positional_variants(graphkb_conn, [TP53_MUT_DICT[ref_key]], DISEASE_RIDS)
        # GERO-299 - nonsense - stop codon - should not match.  This is missense not nonsense (#164:933).
        nonsense = [a for a in pref if a["kbVariant"] == "TP53 nonsense"]
        assert not nonsense
        pref_vars = set([m["kbVariant"] for m in pref])
        assert pref_vars, f"No matches to {TP53_MUT_DICT[pref]}"
        print(pref_vars)
        for key, alt_rep in TP53_MUT_DICT.items():
            if key == ref_key:
                continue
            if key in ('cds_only', 'genome_only'):
                # KBDEV-1259. Temporarely disabled until issue resolution.
                continue
            alt = annotate_positional_variants(graphkb_conn, [alt_rep], DISEASE_RIDS)
            alt_vars = set([m["kbVariant"] for m in alt])
            diff = pref_vars.symmetric_difference(alt_vars)
            missing = pref_vars.difference(alt_vars)

            known_issues = set()
            if key == "genome_only":
                # genome_only matched to more precise type 'TP53 deleterious mutation' but not 'TP53 mutation'
                known_issues.add("TP53 mutation")

            missing = pref_vars.difference(alt_vars).difference(known_issues)
            print(alt_vars)
            assert not missing, f"{key} missing{missing}: {diff}"

    def test_wt_not_matched(self, graphkb_conn):
        """Verify wildtypes are not matched to mutations."""
        disease = "cancer"
        matches = annotate_positional_variants(
            graphkb_conn, [KBDEV1231_TP53_ERR_MATCH_WT], DISEASE_RIDS
        )
        # KBDEV-1231 - wildtype - should not match.  A mutation is not wildtype
        wt_matches = sorted(set([m["kbVariant"] for m in matches if "wildtype" in m["kbVariant"]]))
        assert not wt_matches, f"Mutation 'TP53:p.E285K' should NOT match {wt_matches}"
