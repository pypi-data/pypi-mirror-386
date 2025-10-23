// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Label, Icon } from "semantic-ui-react";
import { i18next } from "@translations/invenio_requests/i18next";

export const LabelStatusSubmit = (props) => {
  return (
    <Label horizontal className="primary" size="small">
      <Icon name="clock outline" />
      {i18next.t("Submitted")}
    </Label>
  );
};

export const LabelStatusDelete = (props) => {
  return (
    <Label horizontal className="negative" size="small">
      <Icon name="trash" />
      {i18next.t("Deleted")}
    </Label>
  );
};

export const LabelStatusAccept = (props) => {
  return (
    <Label horizontal className="positive" size="small">
      <Icon name="check circle" />
      {i18next.t("Accepted")}
    </Label>
  );
};

export const LabelStatusDecline = (props) => {
  return (
    <Label horizontal className="negative" size="small">
      <Icon name="times" />
      {i18next.t("Declined")}
    </Label>
  );
};

export const LabelStatusCancel = (props) => {
  return (
    <Label horizontal className="neutral" size="small">
      <Icon name="stop" />
      {i18next.t("Cancelled")}
    </Label>
  );
};

export const LabelStatusExpire = (props) => {
  return (
    <Label horizontal className="expired" size="small">
      <Icon name="calendar times outline" />
      {i18next.t("Expired")}
    </Label>
  );
};
