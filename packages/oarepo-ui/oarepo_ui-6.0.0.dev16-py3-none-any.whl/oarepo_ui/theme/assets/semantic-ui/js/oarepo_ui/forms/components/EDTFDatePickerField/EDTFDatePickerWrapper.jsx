import React from "react";
import DatePicker from "react-datepicker";
import { DatePickerHeader } from "./DatePickerHeader";
import PropTypes from "prop-types";
import { i18next } from "@translations/oarepo_ui/i18next";
import { edtfDateFormatOptions } from "./utils";
import { useLoadLocaleObjects } from "../../../hooks";
import { InputElement } from "./InputElement";

export const EDTFDatePickerWrapper = ({
  fieldPath,
  placeholder = i18next.t("Choose a date."),
  clearButtonClassName = "clear-icon",
  dateEdtfFormat,
  setDateEdtfFormat,
  handleClear,
  datePickerProps = {},
  customInputProps = {},
  dateFormat,
}) => {
  useLoadLocaleObjects();
  return (
    <DatePicker
      locale={i18next.language}
      renderCustomHeader={(props) => (
        <DatePickerHeader
          dateEdtfFormat={dateEdtfFormat}
          setDateEdtfFormat={setDateEdtfFormat}
          edtfDateFormatOptions={edtfDateFormatOptions}
          {...props}
        />
      )}
      showYearPicker={dateEdtfFormat === "yyyy"}
      showMonthYearPicker={dateEdtfFormat === "yyyy-mm"}
      autoComplete="off"
      dateFormat={dateFormat}
      clearButtonClassName={clearButtonClassName}
      customInput={
        <InputElement
          handleClear={handleClear}
          fieldPath={fieldPath}
          clearButtonClassName={clearButtonClassName}
          autoComplete="off"
          {...customInputProps}
        />
      }
      placeholderText={placeholder}
      popperModifiers={[
        {
          name: "arrow",
          options: {
            padding: ({ popper, reference, placement }) => ({
              right: Math.min(popper.width, reference.width) - 24,
            }),
          },
        },
      ]}
      {...datePickerProps}
    />
  );
};

EDTFDatePickerWrapper.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  /* eslint-disable react/require-default-props */
  datePickerProps: PropTypes.object,
  required: PropTypes.bool,
  placeholder: PropTypes.string,
  clearButtonClassName: PropTypes.string,
  dateEdtfFormat: PropTypes.string.isRequired,
  setDateEdtfFormat: PropTypes.func.isRequired,
  handleClear: PropTypes.func,
  customInputProps: PropTypes.object,
  /* eslint-enable react/require-default-props */
  dateFormat: PropTypes.string.isRequired,
};
