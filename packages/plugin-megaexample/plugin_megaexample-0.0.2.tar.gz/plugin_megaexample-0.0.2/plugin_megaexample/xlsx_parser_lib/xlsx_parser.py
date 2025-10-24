
from django.db import transaction
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from simple_history.utils import bulk_create_with_history
from testy.tests_description.models import TestCase, TestSuite

from .exceptions import InvalidXlsx


class XlsxParser:
    def __init__(self, xlsx_file: bytes, project_id: int):
        self.ws: Worksheet = load_workbook(xlsx_file).active
        self.project_id = project_id

    @transaction.atomic
    def create_suites_with_cases(self):
        cases = []
        suites_counter = 0
        tmp_suite = None
        for idx, row in enumerate(self.ws.iter_rows(), 1):
            try:
                suite_cell, case_cell, scenario_cell = row
            except ValueError:
                raise InvalidXlsx(
                    f'Too many values in line: expected 3, got {len(row)}',
                )

            if not suite_cell.value and not tmp_suite:
                raise InvalidXlsx('Empty suite')

            if suite_cell.value:
                tmp_suite = TestSuite.objects.create(
                    project_id=self.project_id,
                    name=suite_cell.value,
                )
                suites_counter += 1

            if not case_cell.value or not scenario_cell.value:
                raise InvalidXlsx(f'Got empty suite or scenario in line {idx}')

            cases.append(
                TestCase(
                    project_id=self.project_id,
                    suite=tmp_suite,
                    scenario=scenario_cell.value,
                    name=case_cell.value,
                ),
            )

        bulk_create_with_history(cases, TestCase)
        return suites_counter, len(cases)
