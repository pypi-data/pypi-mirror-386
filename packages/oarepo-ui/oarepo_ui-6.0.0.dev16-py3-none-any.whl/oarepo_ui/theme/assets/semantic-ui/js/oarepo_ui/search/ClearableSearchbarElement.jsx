// no multiple options search bar

import React from "react";
import PropTypes from "prop-types";
import { withState } from "react-searchkit";
import { i18next } from "@translations/oarepo_ui/i18next";
import { Input } from "semantic-ui-react";

export const ClearableSearchbarElement = withState(
  ({
    queryString,
    onInputChange,
    updateQueryState,
    currentQueryState,
    iconName = "search",
    iconColor,
    placeholder: passedPlaceholder = i18next.t("Search"),
    actionProps,
  }) => {
    const placeholder = passedPlaceholder || i18next.t("Search");

    const onSearch = () => {
      updateQueryState({ ...currentQueryState, queryString, page: 1 });
    };
    const onBtnSearchClick = () => {
      onSearch();
    };
    const onKeyPress = (event) => {
      if (event.key === "Enter") {
        onSearch();
      }
    };

    const icon = queryString
      ? {
          icon: {
            name: "close",
            className: "clear-button",
            link: true,
            onClick: () => onInputChange(""),
            role: "button",
            "aria-label": i18next.t("Clear"),
            ...actionProps,
          },
        }
      : {};

    return (
      <Input
        {...icon}
        action={{
          icon: iconName,
          className: "search",
          color: iconColor,
          onClick: onBtnSearchClick,
          "aria-label": i18next.t("Search"),
          ...actionProps,
        }}
        fluid
        placeholder={placeholder}
        aria-label={placeholder}
        onChange={(event, { value }) => {
          onInputChange(value);
        }}
        value={queryString}
        onKeyPress={onKeyPress}
      />
    );
  }
);

ClearableSearchbarElement.propTypes = {
  placeholder: PropTypes.string,
  queryString: PropTypes.string,
  onInputChange: PropTypes.func,
  updateQueryState: PropTypes.func,
  currentQueryState: PropTypes.object,
  iconName: PropTypes.string,
  iconColor: PropTypes.string,
};
