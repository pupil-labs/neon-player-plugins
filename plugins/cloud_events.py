# /// script
# requires-python = ">=3.12"
# dependencies = [
# "aiohttp",
# "certifi",
# "keyring",
# ]
# ///

import asyncio
import dataclasses
import datetime
import logging
import re
import ssl
import webbrowser
from dataclasses import field

import aiohttp
import certifi
import keyring
import numpy as np
from pupil_labs.neon_player import Plugin, action
from pupil_labs.neon_player.plugins.events import IMMUTABLE_EVENTS, EventsPlugin
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from qt_property_widgets.utilities import action_params

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, order=True)
class Event:
    """Data class to represent a single, immutable event."""

    timestamp_ns: np.int64
    name: str
    type: str = "recording"
    _offset_s: float | None = field(default=None, compare=False)
    _updated_at: datetime.datetime | str | None = field(default=None, compare=False)


async def from_cloud(workspace_id: str, recording_id: str, token: str) -> list[Event]:
    """Create an Events instance from Pupil Cloud."""
    url = f"https://api.cloud.pupil-labs.com/v2/workspaces/{workspace_id}/recordings/{recording_id}/events"
    headers = {"api-key": token}

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers, ssl=ssl_context) as response,
    ):
        if response.status != 200:
            raise ConnectionError(
                f"Failed to fetch events from Pupil Cloud: {response.status} {response.reason}"
            )
        data = await response.json()

    events_data = data.get("result", [])

    if not events_data:
        return []

    return [
        Event(
            timestamp_ns=np.int64(event["epoch_ns"]),
            name=event["name"],
            type=event.get("origin", "recording"),
            _offset_s=event.get("offset_s"),
            _updated_at=event.get("updated_at", None),
        )
        for event in events_data
    ]


async def push_to_cloud(
    workspace_id: str,
    recording_id: str,
    token: str,
    events: list[Event],
    rec_start_time: int,
):
    """Push events to Pupil Cloud."""
    url = f"https://api.cloud.pupil-labs.com/v2/workspaces/{workspace_id}/recordings/{recording_id}/events"
    headers = {"api-key": token}

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession() as session:
        for event in events:
            offset_s = (int(event.timestamp_ns) - rec_start_time) / 1e9
            payload = {"name": event.name, "offset_s": float(offset_s)}
            async with session.post(
                url, headers=headers, json=payload, ssl=ssl_context
            ) as response:
                if response.status not in (200, 201):
                    error_msg = await response.text()
                    raise ConnectionError(
                        f"Failed to push event {event.name} to Pupil Cloud: {response.status} {response.reason} - {error_msg}"
                    )


class CloudEventsPlugin(Plugin):
    label = "Cloud Events"

    def _get_token(self):
        token = keyring.get_password("neon_player", "PL_CLOUD_TOKEN")
        if not token:
            token = self.app.get_secret("PL_CLOUD_TOKEN")
            if token:
                keyring.set_password("neon_player", "PL_CLOUD_TOKEN", token)
        return token

    @action
    @action_params(compact=True, icon=QIcon.fromTheme("dialog-password"))
    def set_cloud_token(self):
        token, ok = QInputDialog.getText(
            None, "Cloud Token", "Enter Pupil Cloud Token:"
        )
        if ok and token:
            keyring.set_password("neon_player", "PL_CLOUD_TOKEN", token)
            self.app.show_notification("Success", "Token saved to keyring.")

    @action
    @action_params(compact=True, icon=QIcon.fromTheme("edit-delete"))
    def remove_cloud_token(self):
        try:
            keyring.delete_password("neon_player", "PL_CLOUD_TOKEN")
            self.app.show_notification("Success", "Token removed from keyring.")
        except Exception:
            logging.exception("Failed to remove token from keyring")
            self.app.show_notification("Notice", "No token found in keyring.")

    def _get_local_events(self, events_plugin: EventsPlugin) -> list[Event]:
        local_events = []
        for name, times in events_plugin.events.items():
            if name in IMMUTABLE_EVENTS:
                continue
            
            for t in times:
                local_events.append(
                    Event(timestamp_ns=np.int64(t), name=name, type="player")
                )
        return local_events

    @action
    @action_params(compact=True, icon=QIcon.fromTheme("network-receive"))
    def pull_all_events(self):
        workspace_id = self.app.recording.info.get("workspace_id")
        recording_id = self.app.recording.info.get("recording_id")

        token = self._get_token()
        if not token:
            self.app.show_notification("Token missing", "Please set Cloud Token first.")
            return

        events_plugin: EventsPlugin = self.app.plugins_by_class["EventsPlugin"]

        async def _sync():
            try:
                cloud_events = await from_cloud(workspace_id, recording_id, token)
                events_to_add = {}
                for event in cloud_events:
                    if event.name in IMMUTABLE_EVENTS:
                        continue  # Skip immutable events
                    
                    logger.debug(
                        f"Fetched event from cloud: {event.name} at {event.timestamp_ns} ns"
                    )
                    if event.name not in events_to_add:
                        events_to_add[event.name] = []
                    events_to_add[event.name].append(int(event.timestamp_ns))
                
                if events_to_add:
                    events_plugin.add_events(events_to_add)
                self.app.show_notification("Success", "Events synced from Pupil Cloud.")
            except Exception as e:
                logger.exception("Failed to sync events from Pupil Cloud")
                self.app.show_notification("Error", f"Failed to sync events: {e}")

        asyncio.run(_sync())

    @action
    @action_params(compact=True, icon=QIcon.fromTheme("network-transmit"))
    def push_all_events(self):
        workspace_id = self.app.recording.info.get("workspace_id")
        recording_id = self.app.recording.info.get("recording_id")

        token = self._get_token()
        if not token:
            self.app.show_notification("Token missing", "Please set Cloud Token first.")
            return

        events_plugin: EventsPlugin = self.app.plugins_by_class["EventsPlugin"]

        async def _push():
            try:
                local_events = self._get_local_events(events_plugin)
                cloud_events = await from_cloud(workspace_id, recording_id, token)

                cloud_set = {(e.name, int(e.timestamp_ns)) for e in cloud_events}

                to_push = [
                    e
                    for e in local_events
                    if (e.name, int(e.timestamp_ns)) not in cloud_set
                    and e.name not in IMMUTABLE_EVENTS
                ]

                if not to_push:
                    self.app.show_notification("Push Events", "No new events to push.")
                    return

                rec_start = self.app.recording.start_time
                await push_to_cloud(
                    workspace_id, recording_id, token, to_push, rec_start
                )
                link = f"https://cloud.pupil-labs.com/workspaces/{workspace_id}/recordings?filterModel=%7B%22items%22%3A%5B%7B%22id%22%3A%22inactive%22%2C%22field%22%3A%22inactive%22%2C%22operator%22%3A%22is%22%2C%22value%22%3A%22false%22%7D%2C%7B%22id%22%3A%22f1076e8f-f97d-4e64-ba5a-e68e01f85696%22%2C%22field%22%3A%22id%22%2C%22value%22%3A%22{recording_id}%22%2C%22operator%22%3A%22contains%22%7D%5D%2C%22logicOperator%22%3A%22and%22%2C%22quickFilterValues%22%3A%5B%5D%2C%22quickFilterLogicOperator%22%3A%22and%22%2C%22quickFilterExcludeHiddenColumns%22%3Afalse%7D"

                msg_box = QMessageBox(self.app.main_window)
                msg_box.setWindowTitle("Upload Success")
                msg_box.setText(f"Pushed {len(to_push)} events to cloud.")
                open_btn = msg_box.addButton(
                    "Open in Browser", QMessageBox.ButtonRole.ActionRole
                )
                msg_box.addButton(QMessageBox.StandardButton.Ok)
                msg_box.exec()
                if msg_box.clickedButton() == open_btn:
                    webbrowser.open(link)
            except Exception as e:
                logger.exception("Failed to push events to Pupil Cloud")
                self.app.show_notification("Error", f"Failed to push events: {e}")

        asyncio.run(_push())

    @action
    @action_params(compact=True, icon=QIcon.fromTheme("system-search"))
    def compare_events_with_cloud(self):
        workspace_id = self.app.recording.info.get("workspace_id")
        recording_id = self.app.recording.info.get("recording_id")

        token = self._get_token()
        if not token:
            self.app.show_notification("Token missing", "Please set Cloud Token first.")
            return

        events_plugin: EventsPlugin = self.app.plugins_by_class["EventsPlugin"]

        async def _fetch_cloud():
            return await from_cloud(workspace_id, recording_id, token)

        try:
            cloud_events = asyncio.run(_fetch_cloud())
            local_events = self._get_local_events(events_plugin)

            local_set = {
                (e.name, int(e.timestamp_ns))
                for e in local_events
                if e.name not in IMMUTABLE_EVENTS
            }
            cloud_set = {
                (e.name, int(e.timestamp_ns))
                for e in cloud_events
                if e.name not in IMMUTABLE_EVENTS
            }

            all_events = sorted(local_set.union(cloud_set), key=lambda x: x[1])

            dialog = QDialog(self.app.main_window)
            dialog.setWindowTitle("Event Comparison (Local vs Cloud)")
            dialog.resize(700, 500)

            layout = QVBoxLayout(dialog)

            btn_layout = QHBoxLayout()
            select_all_btn = QPushButton("Select/Deselect All")
            import_btn = QPushButton("Import Selected to Local")
            upload_btn = QPushButton("Upload Selected to Cloud")

            btn_layout.addWidget(select_all_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(import_btn)
            btn_layout.addWidget(upload_btn)

            regex_layout = QHBoxLayout()
            regex_input = QLineEdit()
            regex_input.setPlaceholderText("Select names by regex (e.g., ^blink.*)")
            regex_btn = QPushButton("Select Matching")
            regex_layout.addWidget(regex_input)
            regex_layout.addWidget(regex_btn)

            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "Select",
                "Timestamp (ns)",
                "Time",
                "Name",
                "In Local",
                "In Cloud",
            ])
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                4, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                5, QHeaderView.ResizeMode.ResizeToContents
            )
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

            def on_cell_clicked(row, col):
                if col != 0:
                    chk = table.item(row, 0)
                    new_state = (
                        Qt.CheckState.Unchecked
                        if chk.checkState() == Qt.CheckState.Checked
                        else Qt.CheckState.Checked
                    )
                    chk.setCheckState(new_state)

            table.cellClicked.connect(on_cell_clicked)

            rec_start = self.app.recording.start_time

            def fmt_time(ts):
                delta_s = (ts - rec_start) / 1e9
                sign = "-" if delta_s < 0 else ""
                delta_s = abs(delta_s)
                h, r = divmod(delta_s, 3600)
                m, s = divmod(r, 60)
                ms = int((s - int(s)) * 1000)
                return f"{sign}{int(h):02d}:{int(m):02d}:{int(s):02d}.{ms:03d}"

            table.setRowCount(len(all_events))
            for row, (name, ts) in enumerate(all_events):
                in_local = "Yes" if (name, ts) in local_set else "No"
                in_cloud = "Yes" if (name, ts) in cloud_set else "No"

                chk = QTableWidgetItem("")
                chk.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                )
                if in_local != in_cloud:
                    chk.setCheckState(Qt.CheckState.Checked)
                else:
                    chk.setCheckState(Qt.CheckState.Unchecked)

                table.setItem(row, 0, chk)
                table.setItem(row, 1, QTableWidgetItem(str(ts)))
                table.setItem(row, 2, QTableWidgetItem(fmt_time(ts)))
                table.setItem(row, 3, QTableWidgetItem(name))
                table.setItem(row, 4, QTableWidgetItem(in_local))
                table.setItem(row, 5, QTableWidgetItem(in_cloud))

            layout.addLayout(regex_layout)
            layout.addWidget(table)
            layout.addLayout(btn_layout)

            def select_by_regex():
                pattern = regex_input.text()
                if not pattern:
                    return
                try:
                    prog = re.compile(pattern)
                except re.error as exc:
                    self.app.show_notification("Regex Error", f"Invalid regex: {exc}")
                    return

                for row in range(table.rowCount()):
                    name_val = table.item(row, 3).text()
                    if prog.search(name_val):
                        table.item(row, 0).setCheckState(Qt.CheckState.Checked)
                    else:
                        table.item(row, 0).setCheckState(Qt.CheckState.Unchecked)

            regex_btn.clicked.connect(select_by_regex)
            regex_input.returnPressed.connect(select_by_regex)

            toggle_state = [False]

            def toggle_select_all():
                toggle_state[0] = not toggle_state[0]
                state = (
                    Qt.CheckState.Checked
                    if toggle_state[0]
                    else Qt.CheckState.Unchecked
                )
                for row in range(table.rowCount()):
                    table.item(row, 0).setCheckState(state)

            select_all_btn.clicked.connect(toggle_select_all)

            def on_import():
                imported = 0
                for row in range(table.rowCount()):
                    if table.item(row, 0).checkState() == Qt.CheckState.Checked and (
                        table.item(row, 4).text() == "No"
                        and table.item(row, 5).text() == "Yes"
                    ):
                        name_val = table.item(row, 3).text()
                        ts_val = int(table.item(row, 1).text())

                        event_types = [
                            et
                            for et in events_plugin.event_types
                            if et.name == name_val
                        ]
                        if not event_types:
                            event_type = events_plugin.create_event_type(name_val)
                        else:
                            event_type = event_types[0]
                        events_plugin.add_event(event_type, ts_val)
                        imported += 1
                        table.item(row, 4).setText("Yes")
                        table.item(row, 0).setCheckState(Qt.CheckState.Unchecked)
                if imported > 0:
                    self.app.show_notification(
                        "Import", f"Imported {imported} events to local."
                    )
                else:
                    self.app.show_notification(
                        "Import", "No cloud-only events selected to import."
                    )

            def on_upload():
                to_push = []
                for row in range(table.rowCount()):
                    if table.item(row, 0).checkState() == Qt.CheckState.Checked and (
                        table.item(row, 4).text() == "Yes"
                        and table.item(row, 5).text() == "No"
                    ):
                        name_val = table.item(row, 3).text()
                        ts_val = int(table.item(row, 1).text())
                        to_push.append(
                            Event(timestamp_ns=np.int64(ts_val), name=name_val)
                        )

                if to_push:
                    try:
                        asyncio.run(
                            push_to_cloud(
                                workspace_id, recording_id, token, to_push, rec_start
                            )
                        )
                        link = f"https://cloud.pupil-labs.com/workspaces/{workspace_id}/recordings?filterModel=%7B%22items%22%3A%5B%7B%22id%22%3A%22inactive%22%2C%22field%22%3A%22inactive%22%2C%22operator%22%3A%22is%22%2C%22value%22%3A%22false%22%7D%2C%7B%22id%22%3A%22f1076e8f-f97d-4e64-ba5a-e68e01f85696%22%2C%22field%22%3A%22id%22%2C%22value%22%3A%22{recording_id}%22%2C%22operator%22%3A%22contains%22%7D%5D%2C%22logicOperator%22%3A%22and%22%2C%22quickFilterValues%22%3A%5B%5D%2C%22quickFilterLogicOperator%22%3A%22and%22%2C%22quickFilterExcludeHiddenColumns%22%3Afalse%7D"

                        msg_box = QMessageBox(dialog)
                        msg_box.setWindowTitle("Upload Success")
                        msg_box.setText(f"Uploaded {len(to_push)} events to cloud.")
                        open_btn = msg_box.addButton(
                            "Open in Browser", QMessageBox.ButtonRole.ActionRole
                        )
                        msg_box.addButton(QMessageBox.StandardButton.Ok)
                        msg_box.exec()
                        if msg_box.clickedButton() == open_btn:
                            webbrowser.open(link)

                        for row in range(table.rowCount()):
                            if table.item(
                                row, 0
                            ).checkState() == Qt.CheckState.Checked and (
                                table.item(row, 4).text() == "Yes"
                                and table.item(row, 5).text() == "No"
                            ):
                                table.item(row, 5).setText("Yes")
                                table.item(row, 0).setCheckState(
                                    Qt.CheckState.Unchecked
                                )
                    except Exception as exc:
                        logger.exception("Failed to upload selected events")
                        self.app.show_notification("Error", f"Failed to upload: {exc}")
                else:
                    self.app.show_notification(
                        "Upload", "No local-only events selected to upload."
                    )

            import_btn.clicked.connect(on_import)
            upload_btn.clicked.connect(on_upload)

            dialog.exec()

        except Exception as e:
            logger.exception("Failed to compare events with Pupil Cloud")
            self.app.show_notification("Error", f"Failed to compare events: {e}")
