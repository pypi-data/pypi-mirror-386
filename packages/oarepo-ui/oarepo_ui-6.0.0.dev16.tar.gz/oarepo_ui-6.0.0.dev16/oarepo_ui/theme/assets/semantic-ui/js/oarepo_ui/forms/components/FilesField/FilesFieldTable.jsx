import React from "react";
import PropTypes from "prop-types";
import { Table, Popup, Icon } from "semantic-ui-react";
import { i18next } from "@translations/oarepo_ui/i18next";
import { humanReadableBytes } from "react-invenio-forms";
import { EditFileButton, DeleteFileButton } from "./FilesFieldButtons";
import _truncate from "lodash/truncate";

const StatusIcon = ({ status }) => {
  return status === "completed" ? (
    <Popup
      position="top center"
      content={i18next.t("File uploaded successfully.")}
      trigger={<Icon name="check circle" color="green" />}
    />
  ) : (
    <Popup
      position="top center"
      content={i18next.t(
        "File was not uploaded correctly. Please delete it and try again."
      )}
      trigger={<Icon name="exclamation circle" color="red" />}
    />
  );
};

StatusIcon.propTypes = {
  status: PropTypes.string.isRequired,
};

const DeleteFileButtonCmp = ({
  file,
  handleFileDeletion = () => {},
  className = "",
}) => {
  return (
    <Popup
      position="top center"
      content={i18next.t("Delete file")}
      trigger={
        <div className={className}>
          <DeleteFileButton
            file={file}
            handleFileDeletion={handleFileDeletion}
          />
        </div>
      }
    />
  );
};

DeleteFileButtonCmp.propTypes = {
  file: PropTypes.object.isRequired,
  // eslint-disable-next-line react/require-default-props
  handleFileDeletion: PropTypes.func,
  // eslint-disable-next-line react/require-default-props
  className: PropTypes.string,
};

const EditFileButtonCmp = ({
  fileName,
  record,
  className = "",
  allowedFileTypes = ["*/*"],
}) => {
  return (
    <Popup
      // quirky issue where while in UPPY UI the popup goes over it
      style={{ zIndex: 1 }}
      position="top center"
      content={i18next.t("Edit file metadata")}
      trigger={
        <div className={className}>
          <EditFileButton
            fileName={fileName}
            record={record}
            allowedFileTypes={allowedFileTypes}
          />
        </div>
      }
    />
  );
};

EditFileButtonCmp.propTypes = {
  fileName: PropTypes.string.isRequired,
  record: PropTypes.object.isRequired,
  // eslint-disable-next-line react/require-default-props
  className: PropTypes.string,
  // eslint-disable-next-line react/require-default-props
  allowedFileTypes: PropTypes.arrayOf(PropTypes.string),
};

export const FilesFieldTable = ({
  files,
  record,
  handleFileDeletion = () => {},
  lockFileUploader = false,
  fileMetadataFields = [],
  allowedFileTypes = ["*/*"],
}) => {
  return (
    files?.length > 0 && (
      <React.Fragment>
        <Table
          compact
          className="computer tablet only files-table-computer-tablet"
        >
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>{i18next.t("File name")}</Table.HeaderCell>
              <Table.HeaderCell textAlign="center">
                {i18next.t("File size")}
              </Table.HeaderCell>
              <Table.HeaderCell textAlign="center">
                {i18next.t("Status")}
              </Table.HeaderCell>
              <Table.HeaderCell />
              <Table.HeaderCell />
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {files?.map((file) => {
              const { key: fileName, size, status } = file;
              return (
                <Table.Row key={fileName}>
                  <Table.Cell width={4}>
                    <a
                      href={file?.links?.content}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {fileName &&
                        _truncate(fileName, {
                          length: 40,
                          omission: "...",
                        })}
                    </a>
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    {humanReadableBytes(size)}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <StatusIcon status={status} />
                  </Table.Cell>
                  {!lockFileUploader && fileMetadataFields?.length > 0 && (
                    <Table.Cell width={1} textAlign="center">
                      {status === "completed" && (
                        <EditFileButtonCmp
                          fileName={fileName}
                          record={record}
                          allowedFileTypes={allowedFileTypes}
                        />
                      )}
                    </Table.Cell>
                  )}
                  {!lockFileUploader && (
                    <Table.Cell width={1} textAlign="center">
                      <DeleteFileButtonCmp
                        file={file}
                        handleFileDeletion={handleFileDeletion}
                        lockFileUploader={lockFileUploader}
                      />
                    </Table.Cell>
                  )}
                </Table.Row>
              );
            })}
          </Table.Body>
        </Table>
        <div className="mobile only rel-mb-1">
          {files.map((file) => {
            const { key: fileName, size, status } = file;
            return (
              <Table className="files-table-mobile" unstackable key={fileName}>
                <Table.Body>
                  <Table.Row>
                    <Table.Cell width={6}>
                      <strong>{i18next.t("File name")}</strong>
                    </Table.Cell>
                    <Table.Cell className="flex justify-center">
                      <a
                        href={file?.links?.content}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {fileName &&
                          _truncate(fileName, { length: 40, omission: "..." })}
                      </a>
                    </Table.Cell>
                  </Table.Row>
                  {size && (
                    <Table.Row>
                      <Table.Cell width={6}>
                        <strong>{i18next.t("File size")}</strong>
                      </Table.Cell>
                      <Table.Cell className="flex justify-center">
                        {humanReadableBytes(size)}
                      </Table.Cell>
                    </Table.Row>
                  )}
                  <Table.Row>
                    <Table.Cell width={6}>
                      <strong>{i18next.t("Status")}</strong>
                    </Table.Cell>
                    <Table.Cell className="flex justify-center">
                      <StatusIcon status={status} />
                    </Table.Cell>
                  </Table.Row>
                  {!lockFileUploader && (
                    <Table.Row verticalAlign="middle">
                      <Table.Cell width={6}>
                        <strong>{i18next.t("Delete")}</strong>
                      </Table.Cell>
                      <Table.Cell
                        textAlign="center"
                        className="flex justify-center"
                      >
                        <DeleteFileButtonCmp
                          file={file}
                          handleFileDeletion={handleFileDeletion}
                        />
                      </Table.Cell>
                    </Table.Row>
                  )}
                  {status === "completed" &&
                    !lockFileUploader &&
                    fileMetadataFields?.length > 0 && (
                      <Table.Row>
                        <Table.Cell width={6}>
                          <strong>{i18next.t("Edit")}</strong>
                        </Table.Cell>
                        <Table.Cell
                          textAlign="center"
                          className="flex justify-center"
                        >
                          <EditFileButtonCmp
                            fileName={fileName}
                            record={record}
                            allowedFileTypes={allowedFileTypes}
                          />
                        </Table.Cell>
                      </Table.Row>
                    )}
                </Table.Body>
              </Table>
            );
          })}
        </div>
      </React.Fragment>
    )
  );
};

FilesFieldTable.propTypes = {
  files: PropTypes.array.isRequired,
  record: PropTypes.object.isRequired,
  lockFileUploader: PropTypes.bool.isRequired,
  /* eslint-disable react/require-default-props */
  handleFileDeletion: PropTypes.func,
  allowedFileTypes: PropTypes.arrayOf(PropTypes.string),
  fileMetadataFields: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      defaultValue: PropTypes.string,
      isUserInput: PropTypes.bool.isRequired,
    })
  ),
  /* eslint-enable react/require-default-props */
};
