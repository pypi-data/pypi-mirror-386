# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""UI Components for the Render Submitter"""

from __future__ import annotations

import logging
import os
import sys
import json
from typing import Any, Dict, Optional, Protocol
import yaml

from qtpy.QtCore import QSize, Qt  # pylint: disable=import-error
from qtpy.QtGui import QKeyEvent  # pylint: disable=import-error
from qtpy.QtWidgets import (  # pylint: disable=import-error; type: ignore
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .submit_job_progress_dialog import SubmitJobProgressDialog

from ..dataclasses import HostRequirements
from ... import api
from ..deadline_authentication_status import DeadlineAuthenticationStatus
from .. import block_signals
from ...config import get_setting, set_setting, config_file
from ...exceptions import UserInitiatedCancel, NonValidInputError
from ...job_bundle import create_job_history_bundle_dir
from ...job_bundle.parameters import JobParameter
from ...job_bundle.submission import AssetReferences
from ..widgets.deadline_authentication_status_widget import DeadlineAuthenticationStatusWidget
from ..widgets.job_attachments_tab import JobAttachmentsWidget
from ..widgets.shared_job_settings_tab import SharedJobSettingsWidget
from ..widgets.host_requirements_tab import HostRequirementsWidget
from . import DeadlineConfigDialog, DeadlineLoginDialog
from ._types import JobBundlePurpose

logger = logging.getLogger(__name__)

# initialize early so once the UI opens, things are already initialized
DeadlineAuthenticationStatus.getInstance()


class OnCreateJobBundleCallback(Protocol):
    """This protocol defines the callback for creating a job bundle in the SubmitJobToDeadlineDialog."""

    def __call__(
        self,
        widget: SubmitJobToDeadlineDialog,
        job_bundle_dir: str,
        settings: Any,
        queue_parameters: list[JobParameter],
        asset_references: AssetReferences,
        host_requirements: Optional[Dict[str, Any]] = None,
        *,
        purpose: JobBundlePurpose,
    ) -> Optional[dict[str, Any]]: ...


class SubmitJobToDeadlineDialog(QDialog):
    """
    A widget containing all the standard tabs for submitting an AWS Deadline Cloud job.

    If you're using this dialog within an application and want it to stay in front,
    pass f=Qt.Tool, a flag that tells it to do that.

    Args:
        job_setup_widget_type (QWidget): The type of the widget for the job-specific settings.
        initial_job_settings (dataclass): A dataclass containing the initial job settings
        initial_shared_parameter_values (dict[str, Any]): A dict of parameter values {<name>, <value>, ...}
            to override default queue parameter values from the queue. For example,
            a Rez queue environment may have a default "" for the RezPackages parameter, but a Maya
            submitter would override that default with "maya-2023" or similar.
        auto_detected_attachments (AssetReferences): The job attachments that were automatically detected
            from the input document/scene file or starting job bundle.
        attachments (AssetReferences): The job attachments that have been added to the job by the user.
        on_create_job_bundle_callback (OnCreateJobBundleCallback): A function to call when the dialog
            needs to create a Job Bundle. It is called with arguments:
            (widget, job_bundle_dir, settings, queue_parameters, asset_references, host_requirements, purpose).
            It can return either None or a dict with parameters about the submission. Currently,
            the additional parameters supported are:
            {
                # See documentation for deadline.client.api.create_job_from_job_bundle about these parameters
                "job_parameters": [{"name": "ParameterName", "value": "Parameter Value", ...}],
                "known_asset_paths": ["/path/1", ...],
            }
        parent: parent of the widget
        f: Qt Window Flags
        show_host_requirements_tab: Display the host requirements tab in dialog if set to True. Default
            to False.
        submitter_name: Override the default submitter_name value
    """

    def __init__(
        self,
        *,
        job_setup_widget_type: type[QWidget],
        initial_job_settings,
        initial_shared_parameter_values: dict[str, Any],
        auto_detected_attachments: AssetReferences,
        attachments: AssetReferences,
        on_create_job_bundle_callback: OnCreateJobBundleCallback,
        parent=None,
        f=Qt.WindowFlags(),
        show_host_requirements_tab=False,
        host_requirements: Optional[HostRequirements] = None,
        submitter_name: Optional[str] = None,
        known_asset_paths: Optional[list[str]] = None,
    ):
        # The Qt.Tool flag makes sure our widget stays in front of the main application window
        super().__init__(parent=parent, f=f)
        self.setWindowTitle("Submit to AWS Deadline Cloud")
        self.setMinimumSize(400, 400)

        self.job_settings_type = type(initial_job_settings)
        self.submitter_name = submitter_name or self.job_settings_type().submitter_name
        self.on_create_job_bundle_callback = on_create_job_bundle_callback
        self.job_id = None
        self.job_history_bundle_dir: Optional[str] = None
        self.deadline_authentication_status = DeadlineAuthenticationStatus.getInstance()
        self.show_host_requirements_tab = show_host_requirements_tab
        self.known_asset_paths = known_asset_paths or []
        self.should_close = False

        self._build_ui(
            job_setup_widget_type,
            initial_job_settings,
            initial_shared_parameter_values,
            auto_detected_attachments,
            attachments,
            host_requirements,
        )

        self.gui_update_counter: Any = None
        self.refresh_deadline_settings()

    def _submission_succeeded_signal_receiver(self, job_id: str):
        self.job_id = job_id

        set_setting("defaults.job_id", job_id)

    def _close_event_receiver(self):
        if self.submitter_name != "JobBundle" and self.job_id:
            self.close()

    def sizeHint(self):
        return QSize(540, 700)

    def refresh(
        self,
        *,
        job_settings: Optional[Any] = None,
        auto_detected_attachments: Optional[AssetReferences] = None,
        attachments: Optional[AssetReferences] = None,
        load_new_bundle: bool = False,
    ):
        # Refresh the UI components
        self.refresh_deadline_settings()
        if (auto_detected_attachments is not None) or (attachments is not None):
            self.job_attachments.refresh_ui(auto_detected_attachments, attachments)

        if job_settings is not None:
            self.job_settings_type = type(job_settings)
            # Refresh shared job settings
            self.shared_job_settings.refresh_ui(job_settings, load_new_bundle)
            # Refresh job specific settings
            if hasattr(self.job_settings, "refresh_ui"):
                self.job_settings.refresh_ui(job_settings)

    def _build_ui(
        self,
        job_setup_widget_type,
        initial_job_settings,
        initial_shared_parameter_values,
        auto_detected_attachments: AssetReferences,
        attachments: AssetReferences,
        host_requirements: Optional[HostRequirements],
    ):
        self.lyt = QVBoxLayout(self)
        self.lyt.setContentsMargins(5, 5, 5, 5)

        man_layout = QFormLayout()
        self.lyt.addLayout(man_layout)
        self.tabs = QTabWidget()
        self.lyt.addWidget(self.tabs)

        self._build_shared_job_settings_tab(initial_job_settings, initial_shared_parameter_values)
        self._build_job_settings_tab(job_setup_widget_type, initial_job_settings)
        self._build_job_attachments_tab(auto_detected_attachments, attachments)

        # Show host requirements only if requested by the constructor
        if self.show_host_requirements_tab:
            self._build_host_requirements_tab(host_requirements)

        self.auth_status_box = DeadlineAuthenticationStatusWidget(self)
        self.auth_status_box.switch_profile_clicked.connect(self.on_switch_profile_clicked)
        self.auth_status_box.logout_clicked.connect(self.on_logout)
        self.auth_status_box.login_clicked.connect(self.on_login)
        self.lyt.addWidget(self.auth_status_box)
        self.deadline_authentication_status.api_availability_changed.connect(
            self.refresh_deadline_settings
        )

        # Refresh the submit button enable state once queue parameter status changes
        self.shared_job_settings.valid_parameters.connect(self._set_submit_button_state)

        self.button_box = QDialogButtonBox(Qt.Horizontal)
        self.settings_button = QPushButton("Settings...")
        self.settings_button.clicked.connect(self.on_settings_button_clicked)
        self.button_box.addButton(self.settings_button, QDialogButtonBox.ResetRole)
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.on_submit)
        self.button_box.addButton(self.submit_button, QDialogButtonBox.AcceptRole)
        self.export_bundle_button = QPushButton("Export bundle")
        self.export_bundle_button.clicked.connect(self.on_export_bundle)
        self.button_box.addButton(self.export_bundle_button, QDialogButtonBox.AcceptRole)

        self.lyt.addWidget(self.button_box)

    def _set_submit_button_state(self):
        # Enable/disable the Submit button based on whether the
        # AWS Deadline Cloud API is accessible and the farm+queue are configured.
        api_available = self.deadline_authentication_status.api_availability is True
        farm_configured = get_setting("defaults.farm_id") != ""
        queue_configured = get_setting("defaults.queue_id") != ""
        queue_valid = self.shared_job_settings.is_queue_valid()

        enable = api_available and farm_configured and queue_configured and queue_valid

        self.submit_button.setEnabled(enable)

        if not enable:
            issues = []
            if not api_available:
                issues.append(
                    "AWS Deadline Cloud API is not accessible. Check your authentication status."
                )
            if not farm_configured:
                issues.append(
                    "No farm is configured. Click Settings to select a farm for job submission."
                )
            if not queue_configured:
                issues.append(
                    "No queue is configured. Click Settings to select a queue within your farm."
                )
            if farm_configured and queue_configured and not queue_valid:
                issues.append(
                    "Queue parameters are not valid. Check Shared job settings tab for details."
                )

            self.submit_button.setToolTip("Cannot submit job:\n\n• " + "\n\n• ".join(issues))
        else:
            self.submit_button.setToolTip("")

    def refresh_deadline_settings(self):
        self._set_submit_button_state()

        self.shared_job_settings.deadline_cloud_settings_box.refresh_setting_controls(
            self.deadline_authentication_status.api_availability is True
        )
        # If necessary, this reloads the queue parameters
        self.shared_job_settings.refresh_queue_parameters()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Override to capture any enter/return key presses so that the Submit
        button isn't "pressed" when the enter/return key is.
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            return
        super().keyPressEvent(event)

    def _build_shared_job_settings_tab(self, initial_job_settings, initial_shared_parameter_values):
        self.shared_job_settings_tab = QScrollArea()
        self.tabs.addTab(self.shared_job_settings_tab, "Shared job settings")
        self.shared_job_settings = SharedJobSettingsWidget(
            initial_settings=initial_job_settings,
            initial_shared_parameter_values=initial_shared_parameter_values,
            parent=self,
        )
        self.shared_job_settings.parameter_changed.connect(self.on_shared_job_parameter_changed)
        self.shared_job_settings_tab.setWidget(self.shared_job_settings)
        self.shared_job_settings_tab.setWidgetResizable(True)
        self.shared_job_settings.parameter_changed.connect(self.on_shared_job_parameter_changed)

    def _build_job_settings_tab(self, job_setup_widget_type, initial_job_settings):
        self.job_settings_tab = QScrollArea()
        self.tabs.addTab(self.job_settings_tab, "Job-specific settings")
        self.job_settings_tab.setWidgetResizable(True)

        self.job_settings = job_setup_widget_type(
            initial_settings=initial_job_settings, parent=self
        )
        self.job_settings_tab.setWidget(self.job_settings)
        if hasattr(self.job_settings, "parameter_changed"):
            self.job_settings.parameter_changed.connect(self.on_job_template_parameter_changed)

    def _build_job_attachments_tab(
        self, auto_detected_attachments: AssetReferences, attachments: AssetReferences
    ):
        self.job_attachments_tab = QScrollArea()
        self.tabs.addTab(self.job_attachments_tab, "Job attachments")
        self.job_attachments = JobAttachmentsWidget(
            auto_detected_attachments, attachments, parent=self
        )
        self.job_attachments_tab.setWidget(self.job_attachments)
        self.job_attachments_tab.setWidgetResizable(True)

    def _build_host_requirements_tab(self, host_requirements: Optional[HostRequirements]):
        self.host_requirements = HostRequirementsWidget()
        self.host_requirements_tab = QScrollArea()
        self.tabs.addTab(self.host_requirements_tab, "Host requirements")
        self.host_requirements_tab.setWidget(self.host_requirements)
        self.host_requirements_tab.setWidgetResizable(True)
        if host_requirements:
            self.host_requirements.set_requirements(host_requirements)

    def on_shared_job_parameter_changed(self, parameter: dict[str, Any]):
        """
        Handles an edit to a shared job parameter, for example one of the
        queue parameters.

        When a queue parameter and a job template parameter have
        the same name, we update between them to keep them consistent.
        """
        try:
            if hasattr(self.job_settings, "set_parameter_value"):
                with block_signals(self.job_settings):
                    self.job_settings.set_parameter_value(parameter)
        except KeyError:
            # If there is no corresponding job template parameter,
            # just ignore it.
            pass

    def on_job_template_parameter_changed(self, parameter: dict[str, Any]):
        """
        Handles an edit to a job template parameter.

        When a queue parameter and a job template parameter have
        the same name, we update between them to keep them consistent.
        """
        try:
            with block_signals(self.shared_job_settings):
                self.shared_job_settings.set_parameter_value(parameter)
        except KeyError:
            # If there is no corresponding queue parameter,
            # just ignore it.
            pass

    def on_login(self):
        DeadlineLoginDialog.login(parent=self)
        self.refresh_deadline_settings()
        # This widget watches the auth files, but that does
        # not always catch a change so force a refresh here.
        self.deadline_authentication_status.refresh_status()

    def on_logout(self):
        api.logout()
        self.refresh_deadline_settings()
        # This widget watches the auth files, but that does
        # not always catch a change so force a refresh here.
        self.deadline_authentication_status.refresh_status()

    def on_switch_profile_clicked(self):
        if DeadlineConfigDialog.configure_settings(parent=self, set_profile_focus=True):
            self.refresh_deadline_settings()

    def on_settings_button_clicked(self):
        if DeadlineConfigDialog.configure_settings(parent=self):
            self.refresh_deadline_settings()

    def on_export_bundle(self):
        """
        Exports a Job Bundle, but does not submit the job.
        """
        # Retrieve all the settings into the dataclass
        settings = self.job_settings_type()
        self.shared_job_settings.update_settings(settings)
        self.job_settings.update_settings(settings)

        queue_parameters = self.shared_job_settings.get_parameters()

        asset_references = self.job_attachments.get_asset_references()

        # Save the bundle
        try:
            self.job_history_bundle_dir = create_job_history_bundle_dir(
                self.submitter_name, settings.name
            )

            if self.show_host_requirements_tab:
                host_requirements = self.host_requirements.get_requirements()
                parameters_from_callback = self.on_create_job_bundle_callback(
                    self,
                    self.job_history_bundle_dir,
                    settings,
                    queue_parameters,
                    asset_references,
                    host_requirements,
                    purpose=JobBundlePurpose.EXPORT,
                )
            else:
                # Maintaining backward compatibility for submitters that do not support host_requirements yet
                parameters_from_callback = self.on_create_job_bundle_callback(
                    self,
                    self.job_history_bundle_dir,
                    settings,
                    queue_parameters,
                    asset_references,
                    purpose=JobBundlePurpose.EXPORT,
                )
            if parameters_from_callback is None:
                parameters_from_callback = {}

            # If the callback returned job parameters, update them in the job bundle as well so that
            # submission from the job history dir is equivalent.
            job_parameters = parameters_from_callback.get("job_parameters", [])
            if job_parameters:
                self.save_job_parameters_to_job_bundle(self.job_history_bundle_dir, job_parameters)

            logger.info(f"Saved the submission as a job bundle: {self.job_history_bundle_dir}")
            if sys.platform == "win32":
                # Open the directory in the OS's file explorer
                os.startfile(self.job_history_bundle_dir)
            QMessageBox.information(
                self,
                f"{self.submitter_name} job submission",
                f"Saved the submission as a job bundle:\n{self.job_history_bundle_dir}",
            )
            # Close the submitter window to signal the submission is done
            self.close()

        except NonValidInputError as nvie:
            QMessageBox.critical(self, "Non valid inputs detected", str(nvie))

        except Exception as exc:
            logger.exception("Error saving bundle")
            message = str(exc)
            QMessageBox.critical(self, f"{self.submitter_name} job submission", message)  # type: ignore[call-arg]

    def save_job_parameters_to_job_bundle(
        self, job_bundle_dir: str, job_parameters: list[JobParameter]
    ):
        """
        Saves the job parameters to the job bundle. If the job bundle already has a parameter_values file,
        it updates it. Otherwise it creates it.
        """
        job_parameters_dict = {param["name"]: param for param in job_parameters}

        job_parameters_file = os.path.join(job_bundle_dir, "parameter_values.yaml")
        if os.path.exists(job_parameters_file):
            with open(job_parameters_file, "r", encoding="utf8") as f:
                existing_job_parameters = yaml.safe_load(f).get("parameterValues", [])
        else:
            job_parameters_file = os.path.join(job_bundle_dir, "parameter_values.json")
            if os.path.exists(job_parameters_file):
                with open(job_parameters_file, "r", encoding="utf8") as f:
                    existing_job_parameters = json.load(f).get("parameterValues", [])
            else:
                existing_job_parameters = []

        # Overwrite any existing values, and add new values at the end
        combined_job_parameters = []
        for param in existing_job_parameters:
            combined_job_parameters.append(job_parameters_dict.pop(param["name"], param))
        combined_job_parameters.extend(job_parameters_dict.values())

        with open(job_parameters_file, "w", encoding="utf8") as f:
            json.dump({"parameterValues": combined_job_parameters}, f, indent=1)

    def on_submit(self):
        """
        Perform a submission when the submit button is pressed
        """
        # Retrieve all the settings into the dataclass
        settings = self.job_settings_type()
        self.shared_job_settings.update_settings(settings)
        self.job_settings.update_settings(settings)

        queue_parameters = self.shared_job_settings.get_parameters()

        asset_references = self.job_attachments.get_asset_references()

        job_progress_dialog = SubmitJobProgressDialog(parent=self)
        job_progress_dialog.submission_thread_succeeded.connect(
            self._submission_succeeded_signal_receiver
        )
        job_progress_dialog.progress_window_closed.connect(self._close_event_receiver)
        job_progress_dialog.show()
        QApplication.instance().processEvents()  # type: ignore[union-attr]

        # Submit the job
        try:
            self.job_history_bundle_dir = create_job_history_bundle_dir(
                self.submitter_name, settings.name
            )

            if self.show_host_requirements_tab:
                requirements = self.host_requirements.get_requirements()
                parameters_from_callback = self.on_create_job_bundle_callback(
                    self,
                    self.job_history_bundle_dir,
                    settings,
                    queue_parameters,
                    asset_references,
                    requirements,
                    purpose=JobBundlePurpose.SUBMISSION,
                )
            else:
                # Maintaining backward compatibility for submitters that do not support host_requirements yet
                parameters_from_callback = self.on_create_job_bundle_callback(
                    self,
                    self.job_history_bundle_dir,
                    settings,
                    queue_parameters,
                    asset_references,
                    purpose=JobBundlePurpose.SUBMISSION,
                )
            if parameters_from_callback is None:
                parameters_from_callback = {}

            # If the callback returned job parameters, update them in the job bundle as well so that
            # submission from the job history dir is equivalent.
            job_parameters = parameters_from_callback.get("job_parameters", [])
            if job_parameters:
                self.save_job_parameters_to_job_bundle(self.job_history_bundle_dir, job_parameters)

            job_progress_dialog.start_job_submission(
                job_bundle_dir=self.job_history_bundle_dir,
                submitter_name=self.submitter_name,
                config=config_file.read_config(),
                require_paths_exist=self.job_attachments.get_require_paths_exist(),
                job_parameters=job_parameters,
                known_asset_paths=self.known_asset_paths
                + parameters_from_callback.get("known_asset_paths", []),
            )

        except UserInitiatedCancel as uic:
            logger.info("Canceling submission.")
            QMessageBox.information(self, f"{self.submitter_name} job submission", str(uic))
            job_progress_dialog.close()
        except NonValidInputError as nvie:
            QMessageBox.critical(self, "Non valid inputs detected", str(nvie))
            job_progress_dialog.close()
        except Exception as exc:
            logger.exception("error submitting job")
            api.get_deadline_cloud_library_telemetry_client().record_error(
                event_details={"exception_scope": "on_submit"},
                exception_type=str(type(exc)),
                from_gui=True,
            )
            QMessageBox.critical(self, f"{self.submitter_name} job submission", str(exc))  # type: ignore[call-arg]
            job_progress_dialog.close()
