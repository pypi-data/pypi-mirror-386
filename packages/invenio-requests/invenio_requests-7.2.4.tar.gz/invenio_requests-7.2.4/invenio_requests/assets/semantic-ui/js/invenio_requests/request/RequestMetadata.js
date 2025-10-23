// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
// Copyright (C) 2024 Graz University of Technology.
// Copyright (C) 2024 KTH Royal Institute of Technology.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_requests/i18next";
import PropTypes from "prop-types";
import React, { Component } from "react";
import { Image } from "react-invenio-forms";
import Overridable from "react-overridable";
import { Divider, Header, Icon, Message } from "semantic-ui-react";
import { toRelativeTime } from "react-invenio-forms";
import RequestStatus from "./RequestStatus";
import RequestTypeLabel from "./RequestTypeLabel";

const User = ({ user }) => (
  <div className="flex">
    <Image
      src={user.links.avatar}
      avatar
      size="tiny"
      className="mr-5"
      ui={false}
      rounded
    />
    <span>
      {user.profile?.full_name ||
        user?.username ||
        user?.email ||
        i18next.t("Anonymous user")}
    </span>
  </div>
);

User.propTypes = {
  user: PropTypes.shape({
    links: PropTypes.shape({
      avatar: PropTypes.string.isRequired,
    }).isRequired,
    profile: PropTypes.shape({
      full_name: PropTypes.string,
    }),
    username: PropTypes.string,
    email: PropTypes.string,
  }).isRequired,
};

const Community = ({ community }) => (
  <div className="flex">
    <Image src={community.links.logo} avatar size="tiny" className="mr-5" ui={false} />
    <a href={`/communities/${community.slug}`}>{community.metadata.title}</a>
  </div>
);

Community.propTypes = {
  community: PropTypes.shape({
    links: PropTypes.shape({
      logo: PropTypes.string.isRequired,
    }).isRequired,
    slug: PropTypes.string.isRequired,
    metadata: PropTypes.shape({
      title: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

const ExternalEmail = ({ email }) => (
  <div className="flex">
    <Icon name="mail" className="mr-5" />
    <span>
      {i18next.t("Email")}: {email.id}
    </span>
  </div>
);

ExternalEmail.propTypes = {
  email: PropTypes.shape({
    id: PropTypes.string.isRequired,
  }).isRequired,
};

const Group = ({ group }) => (
  <div className="flex">
    <Icon name="group" className="mr-5" />
    <span>
      {i18next.t("Group")}: {group?.name}
    </span>
  </div>
);

Group.propTypes = {
  group: PropTypes.shape({
    name: PropTypes.string.isRequired,
  }).isRequired,
};

const EntityDetails = ({ userData, details }) => {
  const isUser = "user" in userData;
  const isCommunity = "community" in userData;
  const isExternalEmail = "email" in userData;
  const isGroup = "group" in userData;

  if (isUser) {
    return <User user={details} />;
  } else if (isCommunity) {
    return <Community community={details} />;
  } else if (isExternalEmail) {
    return <ExternalEmail email={details} />;
  } else if (isGroup) {
    return <Group group={details} />;
  }
  return null;
};

EntityDetails.propTypes = {
  userData: PropTypes.object.isRequired,
  details: PropTypes.oneOfType([
    PropTypes.shape({
      links: PropTypes.shape({
        avatar: PropTypes.string,
        logo: PropTypes.string,
      }),
      profile: PropTypes.shape({
        full_name: PropTypes.string,
      }),
      username: PropTypes.string,
      email: PropTypes.string,
      slug: PropTypes.string,
      metadata: PropTypes.shape({
        title: PropTypes.string,
      }),
      id: PropTypes.string,
      name: PropTypes.string,
    }),
    PropTypes.object,
  ]).isRequired,
};

const DeletedResource = ({ details }) => (
  <Message negative>{details.metadata.title}</Message>
);

DeletedResource.propTypes = {
  details: PropTypes.shape({
    metadata: PropTypes.shape({
      title: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

class RequestMetadata extends Component {
  isResourceDeleted = (details) => details.is_ghost === true;

  render() {
    const { request } = this.props;
    const expandedCreatedBy = request.expanded?.created_by;
    const expandedReceiver = request.expanded?.receiver;
    return (
      <Overridable id="InvenioRequest.RequestMetadata.Layout" request={request}>
        <>
          {expandedCreatedBy !== undefined && (
            <>
              <Header as="h3" size="tiny">
                {i18next.t("Creator")}
              </Header>
              {this.isResourceDeleted(expandedCreatedBy) ? (
                <DeletedResource details={expandedCreatedBy} />
              ) : (
                <EntityDetails
                  userData={request.created_by}
                  details={request.expanded?.created_by}
                />
              )}
              <Divider />
            </>
          )}

          <Header as="h3" size="tiny">
            {i18next.t("Receiver")}
          </Header>
          {this.isResourceDeleted(expandedReceiver) ? (
            <DeletedResource details={expandedReceiver} />
          ) : (
            <EntityDetails
              userData={request.receiver}
              details={request.expanded?.receiver}
            />
          )}
          <Divider />

          <Header as="h3" size="tiny">
            {i18next.t("Request type")}
          </Header>
          <RequestTypeLabel type={request.type} />
          <Divider />

          <Header as="h3" size="tiny">
            {i18next.t("Status")}
          </Header>
          <RequestStatus status={request.status} />
          <Divider />

          <Header as="h3" size="tiny">
            {i18next.t("Created")}
          </Header>
          {toRelativeTime(request.created, i18next.language)}

          {request.expires_at && (
            <>
              <Divider />
              <Header as="h3" size="tiny">
                {i18next.t("Expires")}
              </Header>
              {toRelativeTime(request.expires_at, i18next.language)}
            </>
          )}

          {request.status === "accepted" && request.topic?.record && (
            <>
              <Divider />
              <Header as="h3" size="tiny">
                {i18next.t("Record")}
              </Header>
              <a href={`/records/${request.topic.record}`}>{request.title}</a>
            </>
          )}
        </>
      </Overridable>
    );
  }
}

RequestMetadata.propTypes = {
  request: PropTypes.object.isRequired,
};

export default Overridable.component(
  "InvenioRequests.RequestMetadata",
  RequestMetadata
);
