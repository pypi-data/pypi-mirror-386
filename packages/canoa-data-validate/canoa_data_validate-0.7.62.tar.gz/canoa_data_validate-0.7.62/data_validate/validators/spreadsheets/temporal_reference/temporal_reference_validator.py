#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.validation.data_validation import (
    check_punctuation,
    check_unique_values,
)
from data_validate.models import SpTemporalReference
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


class SpTemporalReferenceValidator(ValidatorModelABC):
    """
    Validates the content of the SpTemporalReference spreadsheet.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpTemporalReference,
            **kwargs,
        )

        # Run pipeline
        self.run()

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        warnings = []

        columns_dont_punctuation = []
        columns_must_end_with_dot = [SpTemporalReference.RequiredColumn.COLUMN_DESCRIPTION.name]

        list_columns = list(columns_dont_punctuation + columns_must_end_with_dot)
        for column in list_columns:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(
            self._dataframe,
            self._filename,
            columns_dont_punctuation,
            columns_must_end_with_dot,
        )
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_reference_years(self) -> Tuple[List[str], List[str]]:
        errors = []

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name,
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)
                return errors, []

        # Remove first row: This is actual year
        column_series_symbol = SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.iloc[1:]
        years = column_series_symbol.unique()

        # Check if all years are greater than the current year
        for year in years:
            if int(year) < self._data_models_context.config.CURRENT_YEAR:
                errors.append(f"{self._filename}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.")

        return errors, []

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        errors = []

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_NAME.name,
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name,
        ]

        # Check if columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)

        __, unique_errors = check_unique_values(
            dataframe=self._dataframe,
            file_name=self._filename,
            columns_uniques=columns_to_check,
        )
        errors.extend(unique_errors)

        return errors, []

    def _prepare_statement(self):
        pass

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpTemporalReference."""

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_TEMP.value),
            (self.validate_reference_years, NamesEnum.YEARS_TEMP.value),
            (self.validate_unique_values, NamesEnum.UVR_TEMP.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
