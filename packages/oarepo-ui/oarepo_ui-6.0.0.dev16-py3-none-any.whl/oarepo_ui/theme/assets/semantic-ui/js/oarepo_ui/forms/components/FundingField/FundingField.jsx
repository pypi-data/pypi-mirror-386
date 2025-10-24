import React, { useMemo } from "react";
import { FundingField as InvenioFundingField } from "@js/invenio_vocabularies";
import { overrideStore, OverridableContext } from "react-overridable";
import PropTypes from "prop-types";
import { useFieldData } from "../../hooks";
import {
  deserializeFunder,
  deserializeAward,
  computeFundingContents,
} from "./util";
import { FundingRemoteSelectField } from "./FundingRemoteSelectField";
import { SmallPagination } from "../../../search/SmallPagination";

const storeComponents = overrideStore.getAll();

export const FundingField = ({
  // TODO: we should deal with overrides centrally,
  // not at component-render-level - this might be quite non-deterministic
  overrides = {
    "InvenioVocabularies.CustomAwardForm.RemoteSelectField.Container":
      FundingRemoteSelectField,
    "awards.Pagination.element": SmallPagination,
  },
  icon = "money bill alternate outline",
  fieldPath,
  ...props
}) => {
  const mergedOverrides = useMemo(() => {
    return { ...overrides, ...storeComponents };
  }, [overrides]);
  const { getFieldData } = useFieldData();
  const fieldData = {
    ...getFieldData({ fieldPath, icon, fieldRepresentation: "text" }),
  };

  return (
    <OverridableContext.Provider value={mergedOverrides}>
      <div className="oarepo-funding-field-container">
        <InvenioFundingField
          fieldPath={fieldPath}
          searchConfig={{
            searchApi: {
              axios: {
                headers: {
                  Accept: "application/vnd.inveniordm.v1+json",
                },
                url: "/api/awards",
                withCredentials: false,
              },
            },
            initialQueryState: {
              sortBy: "bestmatch",
              sortOrder: "asc",
              layout: "list",
              page: 1,
              size: 5,
            },
          }}
          deserializeAward={deserializeAward}
          deserializeFunder={deserializeFunder}
          computeFundingContents={computeFundingContents}
          labelIcon={null}
          {...fieldData}
          {...props}
        />
      </div>
    </OverridableContext.Provider>
  );
};

FundingField.propTypes = {
  // eslint-disable-next-line react/require-default-props
  overrides: PropTypes.object,
  // eslint-disable-next-line react/require-default-props
  icon: PropTypes.string,
  fieldPath: PropTypes.string.isRequired,
};
