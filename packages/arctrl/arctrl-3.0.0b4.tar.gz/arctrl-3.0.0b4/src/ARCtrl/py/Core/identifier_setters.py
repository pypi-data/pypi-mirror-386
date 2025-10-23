from __future__ import annotations
from .arc_types import (ArcAssay, ArcStudy, ArcInvestigation)
from .Helper.identifier import check_valid_characters
from .Table.arc_table import ArcTable

def set_arc_table_name(new_name: str, table: ArcTable) -> ArcTable:
    check_valid_characters(new_name)
    table.Name = new_name
    return table


def set_assay_identifier(new_identifier: str, assay: ArcAssay) -> ArcAssay:
    check_valid_characters(new_identifier)
    assay.Identifier = new_identifier
    return assay


def set_study_identifier(new_identifier: str, study: ArcStudy) -> ArcStudy:
    check_valid_characters(new_identifier)
    study.Identifier = new_identifier
    return study


def set_investigation_identifier(new_identifier: str, investigation: ArcInvestigation) -> ArcInvestigation:
    check_valid_characters(new_identifier)
    investigation.Identifier = new_identifier
    return investigation


__all__ = ["set_arc_table_name", "set_assay_identifier", "set_study_identifier", "set_investigation_identifier"]

