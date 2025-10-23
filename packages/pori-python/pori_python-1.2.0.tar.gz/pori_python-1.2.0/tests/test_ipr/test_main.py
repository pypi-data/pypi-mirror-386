import json
import os
import pandas as pd
import pytest
import sys
from typing import Dict
from unittest.mock import MagicMock, patch

from pori_python.ipr.connection import IprConnection
from pori_python.ipr.main import command_interface
from pori_python.types import IprGene

from .constants import EXCLUDE_INTEGRATION_TESTS

EXCLUDE_BCGSC_TESTS = os.environ.get("EXCLUDE_BCGSC_TESTS") == "1"
EXCLUDE_ONCOKB_TESTS = os.environ.get("EXCLUDE_ONCOKB_TESTS") == "1"


def get_test_spec():
    ipr_spec = {"components": {"schemas": {"genesCreate": {"properties": {}}}}}
    ipr_gene_keys = IprGene.__required_keys__ | IprGene.__optional_keys__
    for key in ipr_gene_keys:
        ipr_spec["components"]["schemas"]["genesCreate"]["properties"][key] = ""
    return ipr_spec


def get_test_file(name: str) -> str:
    return os.path.join(os.path.dirname(__file__), "test_data", name)


@pytest.fixture(scope="module")
def report_upload_content(tmp_path_factory) -> Dict:
    mock = MagicMock()
    json_file = tmp_path_factory.mktemp("inputs") / "content.json"
    json_file.write_text(
        json.dumps(
            {
                "blargh": "some fake content",
                "comparators": [
                    {"analysisRole": "expression (disease)", "name": "1"},
                    {"analysisRole": "expression (primary site)", "name": "2"},
                    {"analysisRole": "expression (biopsy site)", "name": "3"},
                    {
                        "analysisRole": "expression (internal pancancer cohort)",
                        "name": "4",
                    },
                ],
                "patientId": "PATIENT001",
                "project": "TEST",
                "expressionVariants": json.loads(
                    pd.read_csv(get_test_file("expression.short.tab"), sep="\t").to_json(
                        orient="records"
                    )
                ),
                "smallMutations": json.loads(
                    pd.read_csv(get_test_file("small_mutations.short.tab"), sep="\t").to_json(
                        orient="records"
                    )
                ),
                "copyVariants": json.loads(
                    pd.read_csv(get_test_file("copy_variants.short.tab"), sep="\t").to_json(
                        orient="records"
                    )
                ),
                "structuralVariants": json.loads(
                    pd.read_csv(get_test_file("fusions.tab"), sep="\t").to_json(orient="records")
                ),
                "kbDiseaseMatch": "colorectal cancer",
            },
            allow_nan=False,
        )
    )

    def side_effect_function(*args, **kwargs):
        if 'templates' in args[0]:
            return [{"name": "genomic", "ident": "001"}]
        elif args[0] == "project":
            return [{"name": "TEST", "ident": "001"}]
        else:
            return []

    with patch.object(
        sys,
        "argv",
        [
            "ipr",
            "--username",
            os.environ.get("IPR_USER", os.environ["USER"]),
            "--password",
            os.environ["IPR_PASS"],
            "--ipr_url",
            "http://fake.url.ca",
            "--graphkb_username",
            os.environ.get("GRAPHKB_USER", os.environ["USER"]),
            "--graphkb_password",
            os.environ.get("GRAPHKB_PASS", os.environ["IPR_PASS"]),
            "--graphkb_url",
            os.environ.get("GRAPHKB_URL", False),
            "--content",
            str(json_file),
            "--therapeutics",
        ],
    ):
        with patch.object(IprConnection, "upload_report", new=mock):
            with patch.object(IprConnection, "get_spec", return_value=get_test_spec()):
                with patch.object(IprConnection, "get", side_effect=side_effect_function):
                    command_interface()

    assert mock.called

    report_content = mock.call_args[0][0]
    return report_content


@pytest.mark.skip(reason="KBDEV-1308; taking too long, getting canceled after reaching max delay")
@pytest.mark.skipif(EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests")
class TestCreateReport:
    def test_main_sections_present(self, report_upload_content: Dict) -> None:
        sections = set(report_upload_content.keys())

        for section in [
            "structuralVariants",
            "expressionVariants",
            "copyVariants",
            "smallMutations",
            "kbMatches",
            "genes",
        ]:
            assert section in sections

    def test_kept_low_quality_fusion(self, report_upload_content: Dict) -> None:
        fusions = [(sv["gene1"], sv["gene2"]) for sv in report_upload_content["structuralVariants"]]
        if (
            EXCLUDE_BCGSC_TESTS
        ):  # may be missing statements assoc with SUZ12 if no access to bcgsc data
            assert ("SARM1", "CDKL2") in fusions
        else:
            assert ("SARM1", "SUZ12") in fusions

    def test_pass_through_content_added(self, report_upload_content: Dict) -> None:
        # check the passthorough content was added
        assert "blargh" in report_upload_content

    def test_found_fusion_partner_gene(self, report_upload_content: Dict) -> None:
        genes = report_upload_content["genes"]
        # eg, A1BG
        assert any([g.get("knownFusionPartner", False) for g in genes])

    @pytest.mark.skipif(EXCLUDE_ONCOKB_TESTS, reason="excluding tests that depend on oncokb data")
    def test_found_oncogene(self, report_upload_content: Dict) -> None:
        genes = report_upload_content["genes"]
        # eg, ZBTB20
        assert any([g.get("oncogene", False) for g in genes])

    @pytest.mark.skipif(EXCLUDE_ONCOKB_TESTS, reason="excluding tests that depend on oncokb data)")
    def test_found_tumour_supressor(self, report_upload_content: Dict) -> None:
        genes = report_upload_content["genes"]
        # eg, ZNRF3
        assert any([g.get("tumourSuppressor", False) for g in genes])

    def test_found_kb_statement_related_gene(self, report_upload_content: Dict) -> None:
        genes = report_upload_content["genes"]
        assert any([g.get("kbStatementRelated", False) for g in genes])

    @pytest.mark.skipif(EXCLUDE_ONCOKB_TESTS, reason="excluding tests that depend on oncokb data")
    def test_found_cancer_gene_list_match_gene(self, report_upload_content: Dict) -> None:
        genes = report_upload_content["genes"]
        assert any([g.get("cancerGeneListMatch", False) for g in genes])
