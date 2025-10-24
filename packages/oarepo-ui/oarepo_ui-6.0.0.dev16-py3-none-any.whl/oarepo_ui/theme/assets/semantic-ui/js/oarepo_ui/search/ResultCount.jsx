import React, { useContext } from "react";
import PropTypes from "prop-types";
import { i18next } from "@translations/oarepo_ui/i18next";
import { withState, buildUID as searchkitUID } from "react-searchkit";
import { SearchConfigurationContext } from "@js/invenio_search_ui/components";
import Overridable from "react-overridable";

export const CountElement = ({ totalResults }) => {
  return (
    <label className="rel-mr-1">
      {i18next.t("totalResults", { count: totalResults })}
    </label>
  );
};

CountElement.propTypes = {
  totalResults: PropTypes.number.isRequired,
};

export const ResultCount = ({ currentResultsState = {} }) => {
  const total = currentResultsState?.data?.total;
  const { loading } = currentResultsState;
  // determine if we are in searchApp context or pure searchkit
  const searchAppContext = useContext(SearchConfigurationContext);
  let buildUID = searchkitUID;
  if (searchAppContext === true) buildUID = searchAppContext.buildUID;
  const resultsLoaded = !loading && total > 0;

  return (
    resultsLoaded && (
      <Overridable id={buildUID("Count.element")} totalResults={total}>
        <CountElement totalResults={total} />
      </Overridable>
    )
  );
};

ResultCount.propTypes = {
  // eslint-disable-next-line react/require-default-props
  currentResultsState: PropTypes.object,
};
export const ResultCountWithState = withState(ResultCount);
