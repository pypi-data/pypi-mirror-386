// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
// Copyright (C) 2024 KTH Royal Institute of Technology.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { RequestActionContext } from "@js/invenio_requests/request/actions/context";
import PropTypes from "prop-types";
import React, { Component } from "react";
import { Trans } from "react-i18next";
import Overridable from "react-overridable";
import { Modal } from "semantic-ui-react";
import Error from "../../components/Error";
import { CancelButton } from "../../components/Buttons";
import { RequestActionButton } from "./RequestActionButton";

export class RequestActionModal extends Component {
  constructor(props) {
    super(props);
    this.cancelBtnRef = React.createRef();
  }

  componentDidMount() {
    this.subscribeToContext();
  }

  subscribeToContext = () => {
    const { modalId } = this.props;
    const { modalOpen } = this.context;
    if (modalId in modalOpen) {
      modalOpen[modalId] = false;
    }
  };

  render() {
    const { action, handleActionClick, modalId, children, requestType } = this.props;
    const { modalOpen, loading, toggleModal, error, cleanError, className, size } =
      this.context;

    const currentModalOpen = modalOpen[modalId];

    return (
      <Overridable id="InvenioRequests.RequestActionModal.layout" {...this.props}>
        {/* currentModalOpen prevents mounting multiple instances */}
        {currentModalOpen && (
          <Modal aria-label={action} role="dialog" id={modalId} open={currentModalOpen}>
            <Modal.Header as="h2" className="capitalize-first-char">
              <Overridable id={`RequestActionModal.title.${action}`}>
                <Trans defaults="{{action}} request" values={{ action: action }} />
              </Overridable>
            </Modal.Header>
            <Modal.Content>
              <Modal.Description>
                {error && <Error error={error.message} />}
                {children}
              </Modal.Description>
            </Modal.Content>
            <Modal.Actions>
              <CancelButton
                ref={this.cancelBtnRef}
                onClick={() => {
                  cleanError();
                  toggleModal(modalId, false);
                }}
                loading={loading}
                disabled={loading}
                floated="left"
                size="medium"
              />
              <RequestActionButton
                action={action}
                handleActionClick={handleActionClick}
                loading={loading}
                className={className}
                size={size}
                requestType={requestType}
              />
            </Modal.Actions>
          </Modal>
        )}
      </Overridable>
    );
  }
}

RequestActionModal.contextType = RequestActionContext;

RequestActionModal.propTypes = {
  action: PropTypes.string.isRequired,
  handleActionClick: PropTypes.func.isRequired,
  modalId: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  requestType: PropTypes.string.isRequired,
  loading: PropTypes.bool,
  modalOpen: PropTypes.bool,
};

RequestActionModal.defaultProps = {
  loading: false,
  modalOpen: false,
};

export default Overridable.component(
  "InvenioRequests.RequestActionModal",
  RequestActionModal
);
