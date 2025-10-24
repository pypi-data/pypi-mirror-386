import json
from pathlib import Path
import shutil
from nicegui import ui, app
import asyncio
from importlib import resources as importlib_resources
from typing import Dict, Any, Optional

from nemo_library_etl.adapter._utils.config import _deep_merge
from nemo_library_etl.adapter.migman.migmanutils import MigManUtils
from nemo_library_etl.adapter.migman.symbols import MIGMAN_PROJECT_POSTFIX_SEPARATOR


class MigManUI:
    """NiceGUI-based configuration UI for MigMan without hardcoded colors."""

    def load_configurations(self) -> tuple[dict, dict, dict]:
        """Load default and local configuration files and merge them."""
        resource_rel = "adapter/migman/config/default_config_migman.json"
        with importlib_resources.as_file(
            importlib_resources.files("nemo_library_etl").joinpath(resource_rel)
        ) as p:
            with p.open("r", encoding="utf-8") as f:
                global_config = json.load(f)

        local_config_file = Path("./config") / "migman.json"
        if local_config_file.exists():
            with local_config_file.open("r", encoding="utf-8") as f:
                local_config = json.load(f)
        else:
            local_config = {}

        merged_config = _deep_merge(global_config, local_config)
        return global_config, local_config, merged_config

    def _get_config_differences(
        self, current_config: Dict[str, Any], default_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get only the values that differ from default configuration."""
        differences = {}

        for key, value in current_config.items():
            if key not in default_config:
                # New key not in defaults, include it
                differences[key] = value
            elif isinstance(value, dict) and isinstance(default_config[key], dict):
                # Recursively check nested dictionaries
                nested_diff = self._get_config_differences(value, default_config[key])
                if nested_diff:  # Only include if there are differences
                    differences[key] = nested_diff
            elif value != default_config[key]:
                # Value differs from default
                differences[key] = value

        return differences

    def save_configuration(self, config_data: Dict[str, Any]) -> bool:
        """Save only non-default configuration values to local config file."""
        try:
            # Load the current default configuration
            resource_rel = "adapter/migman/config/default_config_migman.json"
            with importlib_resources.as_file(
                importlib_resources.files("nemo_library_etl").joinpath(resource_rel)
            ) as p:
                with p.open("r", encoding="utf-8") as f:
                    default_config = json.load(f)

            # Get only the differences from default configuration
            config_to_save = self._get_config_differences(config_data, default_config)

            local_config_file = Path("./config") / "migman.json"
            local_config_file.parent.mkdir(exist_ok=True)

            with local_config_file.open("w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)

            ui.notify("Configuration saved successfully!", type="positive")
            return True
        except Exception as e:
            ui.notify(f"Error saving configuration: {str(e)}", type="negative")
            return False

    def reset_configuration(self) -> bool:
        """Reset configuration to defaults by deleting local config file."""
        try:
            local_config_file = Path("./config") / "migman.json"
            if local_config_file.exists():
                local_config_file.unlink()
                ui.notify("Configuration reset successfully!", type="positive")
            else:
                ui.notify("No local configuration found to reset.", type="info")
            return True
        except Exception as e:
            ui.notify(f"Error resetting configuration: {str(e)}", type="negative")
            return False

    def run_ui(self, *, open_browser: bool = True) -> None:
        """Start the NiceGUI interface for MigMan configuration.

        Args:
            open_browser: whether to open the browser automatically
        """

        connected_clients = set()
        global_config, local_config, merged_config = self.load_configurations()

        # Load dark mode setting from configuration
        dark_mode_enabled = merged_config.get("ui_dark_model", True)

        migmandatabase = MigManUtils.MigManDatabaseLoad()
        migmanprojects = sorted(
            [
                project_name
                for project_name in [
                    (
                        (f"{m.project} {MIGMAN_PROJECT_POSTFIX_SEPARATOR} {m.postfix}")
                        if m.postfix and m.project
                        else m.project
                    )
                    for m in migmandatabase
                ]
                if project_name is not None
            ]
        )
        migmanprojects = sorted(list(set(migmanprojects)))

        # State to track changes and form data
        form_state = {
            "has_changes": False,
            "data": merged_config.copy(),
        }

        # Ensure ui_dark_model is set in form data
        if "ui_dark_model" not in form_state["data"]:
            form_state["data"]["ui_dark_model"] = dark_mode_enabled

        @app.on_connect
        def on_connect(client):
            connected_clients.add(client.id)

        @app.on_disconnect
        async def on_disconnect(client):
            connected_clients.discard(client.id)
            if not connected_clients:
                await asyncio.sleep(0.3)
                app.shutdown()

        @ui.page("/")
        def index():
            # Keep a small reactive state for dark mode so we can toggle it at runtime.
            state = {"dark": dark_mode_enabled}

            # Apply initial theme
            if state["dark"]:
                ui.dark_mode().enable()
            else:
                ui.dark_mode().disable()

            # UI component references
            content_container: Optional[ui.column] = None
            save_button: Optional[ui.button] = None
            nav_buttons = {}
            active = {"value": "Global"}

            def mark_changed():
                """Mark form as changed and enable save button."""
                form_state["has_changes"] = True
                if save_button:
                    save_button.props(remove="disable")

            def mark_saved():
                """Mark form as saved and disable save button."""
                form_state["has_changes"] = False
                if save_button:
                    save_button.props("disable")

            def set_active(name: str):
                """Update the active navigation button appearance using theme props."""
                active["value"] = name
                for key, btn in nav_buttons.items():
                    btn.props(remove="color unelevated")
                    btn.props("flat")
                    if key == name:
                        btn.props(remove="flat")
                        btn.props("color=primary unelevated")

            def save_config():
                """Save current configuration to file."""
                if self.save_configuration(form_state["data"]):
                    mark_saved()

            def reset_config():
                """Reset configuration to defaults."""
                if self.reset_configuration():
                    # Reload configurations
                    nonlocal global_config, local_config, merged_config
                    global_config, local_config, merged_config = (
                        self.load_configurations()
                    )

                    # Update form state with the new merged config
                    form_state["data"] = merged_config.copy()
                    form_state["has_changes"] = False

                    # Update dark mode from reset config and apply it
                    new_dark_mode = merged_config.get("ui_dark_model", True)
                    state["dark"] = new_dark_mode
                    if new_dark_mode:
                        ui.dark_mode().enable()
                    else:
                        ui.dark_mode().disable()

                    # Mark as saved (since we're back to defaults)
                    mark_saved()

                    # Re-render the current active section to reflect changes
                    current_active = active["value"]
                    if current_active == "Global":
                        render_global()
                    elif current_active == "Setup":
                        render_setup()
                    elif current_active == "Extract":
                        render_extract()
                    elif current_active == "Transform":
                        render_transform()
                    elif current_active == "Load":
                        render_load()

            # ---------- GLOBAL TOP BAR WITH SAVE BUTTON, RESET BUTTON AND DARK-MODE TOGGLE ----------
            with ui.element("div").classes("fixed top-2 right-4 z-50"):
                with ui.row().classes("items-center gap-3"):
                    # Reset button (with confirmation dialog)
                    def confirm_reset():
                        """Show confirmation dialog before resetting."""

                        async def on_confirm():
                            reset_config()
                            dialog.close()

                        async def on_cancel():
                            dialog.close()

                        with ui.dialog() as dialog, ui.card():
                            ui.label("Reset Configuration").classes(
                                "text-lg font-semibold"
                            )
                            ui.label(
                                "Do you really want to delete all individual configurations and reset to default values?"
                            ).classes("mb-4")

                            with ui.row().classes("gap-2 justify-end"):
                                ui.button("Cancel", on_click=on_cancel).props("flat")
                                ui.button("Reset", on_click=on_confirm).props(
                                    "color=negative"
                                )

                        dialog.open()

                    ui.button(
                        "Reset", icon="restart_alt", on_click=confirm_reset
                    ).props("color=negative outline")

                    # Save button (initially disabled)
                    save_button = ui.button(
                        "Save", icon="save", on_click=save_config
                    ).props("disable")

                    ui.separator().props("vertical")

                    ui.label("Dark mode")

                    def on_toggle(e):
                        """Enable/disable dark mode globally at runtime."""
                        state["dark"] = e.value
                        form_state["data"]["ui_dark_model"] = e.value
                        mark_changed()
                        if state["dark"]:
                            ui.dark_mode().enable()
                        else:
                            ui.dark_mode().disable()

                    ui.switch(value=state["dark"], on_change=on_toggle)

            # -------------------- Renderers --------------------
            def render_global():
                if not content_container:
                    return

                content_container.clear()
                with content_container:
                    ui.label("Global Settings").classes("text-2xl font-semibold")
                    ui.separator()
                    ui.label("Configure global settings for the MigMan ETL process.")

                    current_etl_directory = form_state["data"].get(
                        "etl_directory", "./etl/migman"
                    )

                    # --- ETL Directory (editable) ---
                    with ui.card().classes(""):
                        ui.label("ETL directory").classes("text-lg font-semibold mb-2")

                        def on_etl_dir_change(e):
                            form_state["data"]["etl_directory"] = e.value
                            mark_changed()

                        etl_dir_input = (
                            ui.input(
                                label="Path to ETL folder",
                                value=current_etl_directory,
                                placeholder="e.g. /Users/me/projects/migman/etl",
                                on_change=on_etl_dir_change,
                                validation={
                                    "Required": lambda v: bool(v and v.strip())
                                },
                            )
                            .props("dense")
                            .classes("w-[36rem]")
                        )
                        ui.label(
                            "Enter an absolute or relative path to a local folder."
                        ).classes("text-sm")

            def render_setup():
                if not content_container:
                    return

                content_container.clear()
                with content_container:
                    ui.label("Setup").classes("text-2xl font-semibold")
                    ui.separator()
                    ui.label("Configure system setup and connection parameters.")

                    # Setup configuration
                    setup_config = form_state["data"].setdefault("setup", {})

                    # --- Project Status File ---
                    with ui.card().classes("mt-4"):
                        ui.label("Project Status File").classes(
                            "text-lg font-semibold mb-2"
                        )

                        def on_project_status_file_change(e):
                            setup_config["project_status_file"] = (
                                e.value if e.value.strip() else None
                            )
                            mark_changed()

                        current_project_status_file = setup_config.get(
                            "project_status_file", ""
                        )
                        if current_project_status_file is None:
                            current_project_status_file = ""

                        with ui.row().classes("gap-2 items-end"):
                            project_status_file_input = (
                                ui.input(
                                    label="Path to project status file",
                                    value=current_project_status_file,
                                    placeholder="e.g. ./etl/migman/status/project_status.xlsx",
                                    on_change=on_project_status_file_change,
                                )
                                .props("dense")
                                .classes("w-[36rem]")
                            )

                            def import_projects_from_file():
                                """Import projects from the specified Excel file."""
                                file_path = project_status_file_input.value
                                if not file_path or not file_path.strip():
                                    ui.notify(
                                        "Please enter a file path first.",
                                        type="warning",
                                    )
                                    return

                                try:
                                    # Check if file exists
                                    import os

                                    if not os.path.exists(file_path):
                                        ui.notify(
                                            f"File not found: {file_path}",
                                            type="negative",
                                        )
                                        return

                                    imported_projects = (
                                        MigManUtils.get_migman_projects_from_excel(
                                            file_path
                                        )
                                    )

                                    # Filter imported projects to only include those that exist in migmanprojects
                                    valid_projects = [
                                        p
                                        for p in imported_projects
                                        if p in migmanprojects
                                    ]
                                    invalid_projects = [
                                        p
                                        for p in imported_projects
                                        if p not in migmanprojects
                                    ]

                                    if valid_projects:
                                        # Update the projects selection
                                        setup_config["projects"] = valid_projects
                                        projects_select.value = valid_projects
                                        mark_changed()
                                        update_selection_count()

                                        message = f"Imported {len(valid_projects)} projects successfully!"
                                        if invalid_projects:
                                            message += f" ({len(invalid_projects)} projects not found in database)"
                                        ui.notify(message, type="positive")
                                    else:
                                        ui.notify(
                                            "No valid projects found in the file.",
                                            type="warning",
                                        )
                                        if invalid_projects:
                                            ui.notify(
                                                f"Invalid projects: {', '.join(invalid_projects[:5])}",
                                                type="info",
                                            )

                                except Exception as e:
                                    ui.notify(
                                        f"Error importing file: {str(e)}",
                                        type="negative",
                                    )

                            ui.button(
                                "Import",
                                icon="upload_file",
                                on_click=import_projects_from_file,
                            ).props("size=sm outline").classes("mb-1")

                        ui.label(
                            "Optional file path to track project status and progress. Use the Import button to load projects from this Excel file."
                        ).classes("text-sm")

                    # --- Projects Selection ---
                    with ui.card().classes("mt-4"):
                        ui.label("Projects").classes("text-lg font-semibold mb-2")

                        current_projects = setup_config.get("projects", [])

                        # Display selection count (will be updated via function)
                        selection_count = ui.label(
                            f"Selected: {len(current_projects)}"
                        ).classes("text-sm font-medium")

                        def update_selection_count():
                            current_selection = setup_config.get("projects", [])
                            selection_count.text = f"Selected: {len(current_selection)}"

                        def on_projects_change(e):
                            setup_config["projects"] = e.value if e.value else []
                            mark_changed()
                            update_selection_count()

                        projects_select = (
                            ui.select(
                                options=migmanprojects,
                                value=current_projects,
                                multiple=True,
                                label="Select projects",
                                on_change=on_projects_change,
                            )
                            .props("use-chips clearable use-input input-debounce=0")
                            .classes("w-[48rem]")
                        )

                        # Add helper text
                        ui.label(
                            f"Select one or more projects from the list. Search functionality is available."
                        ).classes("text-sm mt-2")

                        # Add buttons for quick selection
                        with ui.row().classes("gap-2 mt-3"):

                            def select_all():
                                setup_config["projects"] = migmanprojects.copy()
                                projects_select.value = migmanprojects.copy()
                                mark_changed()
                                update_selection_count()

                            def select_none():
                                setup_config["projects"] = []
                                projects_select.value = []
                                mark_changed()
                                update_selection_count()

                            ui.button("Select All", on_click=select_all).props(
                                "size=sm outline"
                            )
                            ui.button("Select None", on_click=select_none).props(
                                "size=sm outline"
                            )

                    # --- Multi-Project List for Feature Assignments ---
                    with ui.card().classes("mt-4"):
                        ui.label("Multi-Project List for Feature Assignments").classes(
                            "text-lg font-semibold mb-2"
                        )

                        current_feature_assignments = setup_config.get(
                            "mult_project_list_feature_assignments", []
                        )

                        # Display selection count for feature assignments
                        feature_assignments_count = ui.label(
                            f"Keys: {len(current_feature_assignments)}"
                        ).classes("text-sm font-medium")

                        def update_feature_assignments_count():
                            current_selection = setup_config.get(
                                "mult_project_list_feature_assignments", []
                            )
                            feature_assignments_count.text = (
                                f"Keys: {len(current_selection)}"
                            )

                        def on_feature_assignments_change(e):
                            # Split by comma, strip whitespace, and filter out empty strings
                            keys = [
                                key.strip()
                                for key in (e.value or "").split(",")
                                if key.strip()
                            ]
                            setup_config["mult_project_list_feature_assignments"] = keys
                            mark_changed()
                            update_feature_assignments_count()

                        feature_assignments_input = (
                            ui.input(
                                label="Feature assignment keys (comma-separated)",
                                value=", ".join(current_feature_assignments),
                                placeholder="key1, key2, key3",
                                on_change=on_feature_assignments_change,
                            )
                            .props("dense")
                            .classes("w-[48rem]")
                        )

                        ui.label(
                            "Enter comma-separated keys for feature assignments. Each key should be a single word."
                        ).classes("text-sm mt-2")

                    # --- Multi-Project List for Texts ---
                    with ui.card().classes("mt-4"):
                        ui.label("Multi-Project List for Texts").classes(
                            "text-lg font-semibold mb-2"
                        )

                        current_texts = setup_config.get("mult_project_list_texts", [])

                        # Display selection count for texts
                        texts_count = ui.label(f"Keys: {len(current_texts)}").classes(
                            "text-sm font-medium"
                        )

                        def update_texts_count():
                            current_selection = setup_config.get(
                                "mult_project_list_texts", []
                            )
                            texts_count.text = f"Keys: {len(current_selection)}"

                        def on_texts_change(e):
                            # Split by comma, strip whitespace, and filter out empty strings
                            keys = [
                                key.strip()
                                for key in (e.value or "").split(",")
                                if key.strip()
                            ]
                            setup_config["mult_project_list_texts"] = keys
                            mark_changed()
                            update_texts_count()

                        texts_input = (
                            ui.input(
                                label="Text keys (comma-separated)",
                                value=", ".join(current_texts),
                                placeholder="text1, text2, text3",
                                on_change=on_texts_change,
                            )
                            .props("dense")
                            .classes("w-[48rem]")
                        )

                        ui.label(
                            "Enter comma-separated keys for texts. Each key should be a single word."
                        ).classes("text-sm mt-2")

            def render_extract():
                if not content_container:
                    return

                content_container.clear()
                with content_container:
                    ui.label("Extract").classes("text-2xl font-semibold")
                    ui.separator()
                    ui.label("Configure data sources and extraction parameters.")

                    # Extract configuration
                    extract_config = form_state["data"].setdefault("extract", {})

                    # General Extract Settings Card
                    with ui.card().classes("mt-4"):
                        ui.label("General Extract Settings").classes(
                            "text-lg font-semibold mb-2"
                        )

                        def on_extract_active_change(e):
                            extract_config["active"] = e.value
                            mark_changed()
                            # Re-render the extract section to update UI state
                            render_extract()

                        extract_active = extract_config.get("active", True)

                        ui.switch(
                            "Extract active",
                            value=extract_active,
                            on_change=on_extract_active_change,
                        )

                        def on_load_to_nemo_change(e):
                            extract_config["load_to_nemo"] = e.value
                            mark_changed()

                        load_to_nemo_switch = ui.switch(
                            "Load to NEMO",
                            value=extract_config.get("load_to_nemo", True),
                            on_change=on_load_to_nemo_change,
                        )
                        if not extract_active:
                            load_to_nemo_switch.props("disable")

                        def on_delete_temp_files_change(e):
                            extract_config["delete_temp_files"] = e.value
                            mark_changed()

                        delete_temp_files_switch = ui.switch(
                            "Delete temp files",
                            value=extract_config.get("delete_temp_files", True),
                            on_change=on_delete_temp_files_change,
                        )
                        if not extract_active:
                            delete_temp_files_switch.props("disable")

                        def on_nemo_project_prefix_change(e):
                            extract_config["nemo_project_prefix"] = e.value
                            mark_changed()

                        nemo_project_prefix_input = (
                            ui.input(
                                label="NEMO project prefix",
                                value=extract_config.get("nemo_project_prefix", "mme"),
                                placeholder="migman_extract_",
                                on_change=on_nemo_project_prefix_change,
                            )
                            .props("dense")
                            .classes("w-[36rem] mt-3")
                        )
                        if not extract_active:
                            nemo_project_prefix_input.props("disable")

                    # Adapter Selection
                    with ui.card().classes("mt-4"):
                        ui.label("Data Source Adapter").classes(
                            "text-lg font-semibold mb-2"
                        )
                        ui.label(
                            "Select which data source adapter to use for extraction."
                        ).classes("text-sm mb-4")

                        def on_adapter_change(e):
                            extract_config["adapter"] = e.value
                            mark_changed()
                            # Re-render the extract section to update adapter configuration
                            render_extract()

                        current_adapter = extract_config.get("adapter", "none")

                        adapter_select = (
                            ui.select(
                                label="Adapter",
                                options=[
                                    "none",
                                    "genericodbc",
                                    "inforcom",
                                    "sapecc",
                                    "proalpha",
                                ],
                                value=current_adapter,
                                on_change=on_adapter_change,
                            )
                            .props("dense")
                            .classes("w-48")
                        )
                        if not extract_active:
                            adapter_select.props("disable")

                    # Adapter Configuration
                    with ui.card().classes("mt-4") as adapters_card:
                        if not extract_active:
                            # Show disabled message when extract is not active
                            ui.label(
                                "Extract must be active to configure the data source adapter."
                            ).classes("text-sm text-gray-500 italic mb-4")
                            adapters_card.props("disable")
                        else:
                            if current_adapter == "inforcom":
                                render_inforcom_config(extract_config)
                            elif current_adapter == "sapecc":
                                render_sapecc_config(extract_config)
                            elif current_adapter == "proalpha":
                                render_proalpha_config(extract_config)
                            elif current_adapter == "genericodbc":
                                render_generic_odbc_config(extract_config)
                            elif current_adapter == "none":
                                ui.label("Adapter Configuration").classes(
                                    "text-lg font-semibold mb-3"
                                )
                                ui.label(
                                    "No adapter selected. No database extraction will be performed."
                                ).classes("text-sm text-gray-600")
                                ui.label(
                                    "You can still use file-based extraction if configured below."
                                ).classes("text-sm text-gray-600 mt-2")
                            else:
                                ui.label("Adapter Configuration").classes(
                                    "text-lg font-semibold mb-3"
                                )
                                ui.label(
                                    f"No configuration available for adapter '{current_adapter}'."
                                ).classes("text-sm text-gray-600 italic")

                    # File Configuration
                    with ui.card().classes("mt-4"):
                        ui.label("File Configuration").classes(
                            "text-lg font-semibold mb-2"
                        )
                        ui.label(
                            "Configure manual file imports for the extraction process. File paths are automatically validated for existence."
                        ).classes("text-sm mb-4")

                        file_config = extract_config.setdefault("file", [])

                        # Display existing files
                        for i, file_item in enumerate(file_config):
                            with ui.card().classes("mt-2 p-3"):
                                with ui.row().classes(
                                    "items-center justify-between w-full"
                                ):
                                    # Show project and file path as label
                                    import os

                                    file_display = f"{file_item.get('project', 'No Project')} - {os.path.basename(file_item.get('file_path', 'No Path'))}"
                                    file_label = ui.label(
                                        f"File: {file_display}"
                                    ).classes("font-medium")
                                    if not extract_active:
                                        file_label.classes("text-gray-500")

                                    delete_button = ui.button(
                                        icon="delete",
                                        on_click=lambda idx=i: remove_file_config(idx),
                                    ).props("flat round color=negative size=sm")
                                    if not extract_active:
                                        delete_button.props("disable")

                                with ui.column().classes("gap-2 w-full"):
                                    # File active toggle
                                    def on_file_active_change(e, idx=i):
                                        file_config[idx]["active"] = e.value
                                        mark_changed()
                                        # Re-render the extract section to update all UI elements including columns visibility
                                        render_extract()

                                    file_active_switch = ui.switch(
                                        "Active",
                                        value=file_item.get("active", True),
                                        on_change=lambda e, idx=i: on_file_active_change(
                                            e, idx
                                        ),
                                    )
                                    if not extract_active:
                                        file_active_switch.props("disable")

                                    # Project input
                                    def on_project_change(e, idx=i):
                                        file_config[idx]["project"] = e.value
                                        mark_changed()

                                    project_input = (
                                        ui.input(
                                            label="Project",
                                            value=file_item.get("project", ""),
                                            placeholder="Enter project name",
                                            on_change=lambda e, idx=i: on_project_change(
                                                e, idx
                                            ),
                                        )
                                        .props("dense")
                                        .classes("w-full")
                                    )
                                    if not extract_active:
                                        project_input.props("disable")

                                    # File path input with existence validation
                                    def on_file_path_change(e, idx=i):
                                        file_config[idx]["file_path"] = e.value
                                        mark_changed()
                                        # Check file existence and update UI feedback
                                        validate_file_path(
                                            e.value, file_path_input, file_status_label
                                        )

                                    def validate_file_path(
                                        file_path, input_element, status_element
                                    ):
                                        import os

                                        if file_path and file_path.strip():
                                            try:
                                                if os.path.isfile(file_path):
                                                    # File exists - clear error state
                                                    status_element.text = (
                                                        "✓ File exists"
                                                    )
                                                    status_element.classes(
                                                        remove="text-red-500"
                                                    )
                                                    status_element.classes(
                                                        "text-green-600"
                                                    )
                                                else:
                                                    # File doesn't exist - show warning
                                                    status_element.text = (
                                                        "⚠ File not found"
                                                    )
                                                    status_element.classes(
                                                        remove="text-green-600"
                                                    )
                                                    status_element.classes(
                                                        "text-red-500"
                                                    )
                                            except (OSError, PermissionError):
                                                # Cannot access file - show warning
                                                status_element.text = (
                                                    "⚠ Cannot access file"
                                                )
                                                status_element.classes(
                                                    remove="text-green-600"
                                                )
                                                status_element.classes("text-red-500")
                                        else:
                                            # Empty path - clear status
                                            status_element.text = ""
                                            status_element.classes(
                                                remove="text-green-600 text-red-500"
                                            )

                                    file_path_input = (
                                        ui.input(
                                            label="File Path",
                                            value=file_item.get("file_path", ""),
                                            placeholder="e.g. /path/to/your/file.csv",
                                            on_change=lambda e, idx=i: on_file_path_change(
                                                e, idx
                                            ),
                                        )
                                        .props("dense")
                                        .classes("w-full")
                                    )
                                    if not extract_active:
                                        file_path_input.props("disable")

                                    # Status label for file existence
                                    file_status_label = ui.label("").classes("text-sm")

                                    # File format settings
                                    with ui.row().classes("gap-4 mt-3"):
                                        # Separator select
                                        def on_separator_change(e, idx=i):
                                            file_config[idx]["separator"] = e.value
                                            mark_changed()

                                        separator_options = {
                                            ";": "Semicolon (;)",
                                            ",": "Comma (,)",
                                            "\t": "Tab (\\t)",
                                            "|": "Pipe (|)",
                                            ":": "Colon (:)",
                                            " ": "Space ( )",
                                        }

                                        separator_input = (
                                            ui.select(
                                                label="Separator",
                                                options=separator_options,
                                                value=file_item.get("separator", ";"),
                                                on_change=lambda e, idx=i: on_separator_change(
                                                    e, idx
                                                ),
                                            )
                                            .props("dense")
                                            .classes("w-40")
                                        )
                                        if not extract_active:
                                            separator_input.props("disable")

                                        # Quote input
                                        def on_quote_change(e, idx=i):
                                            file_config[idx]["quote"] = e.value
                                            mark_changed()

                                        quote_input = (
                                            ui.input(
                                                label="Quote",
                                                value=file_item.get("quote", '"'),
                                                placeholder='"',
                                                on_change=lambda e, idx=i: on_quote_change(
                                                    e, idx
                                                ),
                                            )
                                            .props("dense")
                                            .classes("w-24")
                                        )
                                        if not extract_active:
                                            quote_input.props("disable")

                                        # Date format input
                                        def on_dateformat_change(e, idx=i):
                                            file_config[idx]["dateformat"] = e.value
                                            mark_changed()

                                        dateformat_input = (
                                            ui.input(
                                                label="Date format",
                                                value=file_item.get(
                                                    "dateformat", "%d-%m-%Y"
                                                ),
                                                placeholder="%d-%m-%Y",
                                                on_change=lambda e, idx=i: on_dateformat_change(
                                                    e, idx
                                                ),
                                            )
                                            .props("dense")
                                            .classes("w-32")
                                        )
                                        if not extract_active:
                                            dateformat_input.props("disable")

                                        # Encoding select
                                        def on_encoding_change(e, idx=i):
                                            file_config[idx]["encoding"] = e.value
                                            mark_changed()

                                        encoding_input = (
                                            ui.select(
                                                label="Encoding",
                                                options=[
                                                    "utf-8",
                                                    "utf-16",
                                                    "latin-1",
                                                    "CP1252",
                                                ],
                                                value=file_item.get(
                                                    "encoding", "utf-8"
                                                ),
                                                on_change=lambda e, idx=i: on_encoding_change(
                                                    e, idx
                                                ),
                                            )
                                            .props("dense")
                                            .classes("w-32")
                                        )
                                        if not extract_active:
                                            encoding_input.props("disable")

                                    # Header toggle
                                    def on_header_change(e, idx=i):
                                        file_config[idx]["header"] = e.value
                                        mark_changed()
                                        # Update columns field visibility based on all conditions
                                        if hasattr(columns_container, "set_visibility"):
                                            # Show columns only if: extract active AND file active AND header false
                                            should_show = (
                                                extract_active
                                                and file_config[idx].get("active", True)
                                                and not e.value
                                            )
                                            columns_container.set_visibility(
                                                should_show
                                            )

                                    header_switch = ui.switch(
                                        "File has header row",
                                        value=file_item.get("header", True),
                                        on_change=lambda e, idx=i: on_header_change(
                                            e, idx
                                        ),
                                    ).classes("mt-3")
                                    if not extract_active:
                                        header_switch.props("disable")

                                    # All varchar toggle
                                    def on_all_varchar_change(e, idx=i):
                                        file_config[idx]["all_varchar"] = e.value
                                        mark_changed()

                                    all_varchar_switch = ui.switch(
                                        "Import all columns as text (VARCHAR) - recommended to avoid conversion errors",
                                        value=file_item.get("all_varchar", True),
                                        on_change=lambda e, idx=i: on_all_varchar_change(
                                            e, idx
                                        ),
                                    ).classes("mt-2")
                                    if not extract_active:
                                        all_varchar_switch.props("disable")

                                    # Columns field (in a container for visibility control)
                                    with ui.column().classes(
                                        "w-full"
                                    ) as columns_container:

                                        def add_column_chip(column_name, idx=i):
                                            """Add a column chip to the display."""
                                            current_columns = file_config[idx].get(
                                                "columns", []
                                            )
                                            if (
                                                column_name
                                                and column_name not in current_columns
                                            ):
                                                current_columns.append(column_name)
                                                file_config[idx][
                                                    "columns"
                                                ] = current_columns
                                                mark_changed()
                                                # Re-render the columns section
                                                render_columns_section(idx)

                                        def remove_column_chip(column_name, idx=i):
                                            """Remove a column chip from the display."""
                                            current_columns = file_config[idx].get(
                                                "columns", []
                                            )
                                            if column_name in current_columns:
                                                current_columns.remove(column_name)
                                                file_config[idx][
                                                    "columns"
                                                ] = current_columns
                                                mark_changed()
                                                # Re-render the entire columns section
                                                render_columns_section(idx)

                                        def render_columns_section(idx=i):
                                            """Render the columns chip interface."""
                                            current_columns = file_config[idx].get(
                                                "columns", []
                                            )

                                            columns_container.clear()

                                            with columns_container:
                                                ui.label("Column Names").classes(
                                                    "text-sm font-medium mt-2 mb-2"
                                                )

                                                # Container for chips that we can update
                                                chips_container = ui.row().classes(
                                                    "gap-1 mb-2 flex-wrap"
                                                )

                                                # Function to update chips display
                                                def update_chips():
                                                    chips_container.clear()
                                                    current_cols = file_config[idx].get(
                                                        "columns", []
                                                    )
                                                    with chips_container:
                                                        for i, column in enumerate(
                                                            current_cols
                                                        ):

                                                            def make_remove_handler(
                                                                col_name,
                                                            ):
                                                                def remove_handler():
                                                                    remove_column_chip(
                                                                        col_name, idx
                                                                    )

                                                                return remove_handler

                                                            def make_move_handlers(
                                                                col_idx,
                                                            ):
                                                                def move_left():
                                                                    if col_idx > 0:
                                                                        cols = file_config[
                                                                            idx
                                                                        ].get(
                                                                            "columns",
                                                                            [],
                                                                        )
                                                                        # Swap with previous column
                                                                        (
                                                                            cols[
                                                                                col_idx
                                                                            ],
                                                                            cols[
                                                                                col_idx
                                                                                - 1
                                                                            ],
                                                                        ) = (
                                                                            cols[
                                                                                col_idx
                                                                                - 1
                                                                            ],
                                                                            cols[
                                                                                col_idx
                                                                            ],
                                                                        )
                                                                        file_config[
                                                                            idx
                                                                        ][
                                                                            "columns"
                                                                        ] = cols
                                                                        mark_changed()
                                                                        update_chips()

                                                                def move_right():
                                                                    cols = file_config[
                                                                        idx
                                                                    ].get("columns", [])
                                                                    if (
                                                                        col_idx
                                                                        < len(cols) - 1
                                                                    ):
                                                                        # Swap with next column
                                                                        (
                                                                            cols[
                                                                                col_idx
                                                                            ],
                                                                            cols[
                                                                                col_idx
                                                                                + 1
                                                                            ],
                                                                        ) = (
                                                                            cols[
                                                                                col_idx
                                                                                + 1
                                                                            ],
                                                                            cols[
                                                                                col_idx
                                                                            ],
                                                                        )
                                                                        file_config[
                                                                            idx
                                                                        ][
                                                                            "columns"
                                                                        ] = cols
                                                                        mark_changed()
                                                                        update_chips()

                                                                return (
                                                                    move_left,
                                                                    move_right,
                                                                )

                                                            move_left, move_right = (
                                                                make_move_handlers(i)
                                                            )

                                                            # Create chip with move buttons
                                                            with ui.row().classes(
                                                                "items-center gap-1"
                                                            ):
                                                                # Move left button (only show if not first)
                                                                if i > 0:
                                                                    ui.button(
                                                                        icon="chevron_left",
                                                                        on_click=move_left,
                                                                    ).props(
                                                                        "size=xs flat round"
                                                                    ).classes(
                                                                        "p-1"
                                                                    )
                                                                else:
                                                                    ui.element(
                                                                        "div"
                                                                    ).classes(
                                                                        "w-6"
                                                                    )  # Placeholder for alignment

                                                                # The chip itself
                                                                chip = ui.chip(
                                                                    column,
                                                                    removable=True,
                                                                ).classes(
                                                                    "bg-blue-100 text-blue-800"
                                                                )
                                                                chip.on(
                                                                    "remove",
                                                                    make_remove_handler(
                                                                        column
                                                                    ),
                                                                )

                                                                # Move right button (only show if not last)
                                                                if (
                                                                    i
                                                                    < len(current_cols)
                                                                    - 1
                                                                ):
                                                                    ui.button(
                                                                        icon="chevron_right",
                                                                        on_click=move_right,
                                                                    ).props(
                                                                        "size=xs flat round"
                                                                    ).classes(
                                                                        "p-1"
                                                                    )
                                                                else:
                                                                    ui.element(
                                                                        "div"
                                                                    ).classes(
                                                                        "w-6"
                                                                    )  # Placeholder for alignment

                                                # Initial chips display
                                                update_chips()

                                                # Input for adding new columns
                                                def on_add_column():
                                                    """Add column from current input value."""
                                                    if (
                                                        new_column_input.value
                                                        and new_column_input.value.strip()
                                                    ):
                                                        # Handle comma-separated input
                                                        new_columns = [
                                                            col.strip()
                                                            for col in new_column_input.value.split(
                                                                ","
                                                            )
                                                            if col.strip()
                                                        ]
                                                        for col in new_columns:
                                                            # Add to data
                                                            current_columns = (
                                                                file_config[idx].get(
                                                                    "columns", []
                                                                )
                                                            )
                                                            if (
                                                                col
                                                                and col
                                                                not in current_columns
                                                            ):
                                                                current_columns.append(
                                                                    col
                                                                )
                                                                file_config[idx][
                                                                    "columns"
                                                                ] = current_columns
                                                                mark_changed()

                                                        # Update display
                                                        update_chips()
                                                        new_column_input.value = ""  # Clear input after adding

                                                def on_enter_key(e):
                                                    """Handle Enter key press."""
                                                    on_add_column()

                                                new_column_input = (
                                                    ui.input(
                                                        placeholder="Type column name and press Enter to add",
                                                    )
                                                    .props("dense")
                                                    .classes("w-full")
                                                )

                                                # Enable Enter key handling
                                                new_column_input.on(
                                                    "keydown.enter", on_enter_key
                                                )

                                                # Add button for manual addition
                                                with ui.row().classes("gap-2 mt-2"):
                                                    ui.button(
                                                        "Add Column",
                                                        icon="add",
                                                        on_click=on_add_column,
                                                    ).props("size=sm outline")

                                                if not extract_active:
                                                    new_column_input.props("disable")

                                                ui.label(
                                                    "Type column names and press Enter or click 'Add Column' (required when file has no header). Use ← → arrows to reorder columns."
                                                ).classes("text-sm text-gray-600 mt-1")

                                        # Initial render
                                        render_columns_section(i)

                                    # Set initial visibility based on all conditions
                                    if hasattr(columns_container, "set_visibility"):
                                        # Show columns only if: extract active AND file active AND header false
                                        should_show = (
                                            extract_active
                                            and file_item.get("active", True)
                                            and not file_item.get("header", True)
                                        )
                                        columns_container.set_visibility(should_show)

                                    # Check button to validate file configuration
                                    def check_file_config(idx=i):
                                        """Test file import with current configuration (first 500 records)."""
                                        file_item = file_config[idx]
                                        file_path = file_item.get("file_path", "")

                                        # Validate required fields
                                        if not file_path:
                                            ui.notify(
                                                "File path is required for checking.",
                                                type="warning",
                                            )
                                            return

                                        if not file_item.get(
                                            "header", True
                                        ) and not file_item.get("columns", []):
                                            ui.notify(
                                                "Column names are required when file has no header.",
                                                type="warning",
                                            )
                                            return

                                        try:
                                            import pandas as pd
                                            import os

                                            # Check if file exists
                                            if not os.path.isfile(file_path):
                                                ui.notify(
                                                    f"File not found: {file_path}",
                                                    type="negative",
                                                )
                                                return

                                            # STEP 1: First read without column names to determine actual structure
                                            detect_params = {
                                                "filepath_or_buffer": file_path,
                                                "sep": file_item.get("separator", ";"),
                                                "quotechar": file_item.get(
                                                    "quote", '"'
                                                ),
                                                "encoding": file_item.get(
                                                    "encoding", "utf-8"
                                                ),
                                                "nrows": 10,  # Just read a few rows for detection
                                                "header": None,  # Never use header for detection
                                            }

                                            if file_item.get("all_varchar", True):
                                                detect_params.update({"dtype": str})
                                            # Read file without forcing column names to get actual structure
                                            detect_df = pd.read_csv(**detect_params)
                                            actual_cols = detect_df.shape[1]

                                            # STEP 2: Analyze the raw structure
                                            issues = []

                                            # Check column count vs expectations
                                            expected_cols = None
                                            if file_item.get("header", True):
                                                # For files with headers, we expect the header row to define columns
                                                expected_cols = actual_cols  # We'll use what we find
                                            else:
                                                # For files without headers, check against user-defined columns
                                                user_columns = file_item.get(
                                                    "columns", []
                                                )
                                                if user_columns:
                                                    expected_cols = len(user_columns)
                                                    if actual_cols != expected_cols:
                                                        issues.append(
                                                            f"Expected {expected_cols} columns (based on column list) but found {actual_cols} in file. "
                                                            f"Check separator '{file_item.get('separator', ';')}' or column list."
                                                        )

                                            # Check for common separator issues by looking at first column content
                                            if actual_cols > 0:
                                                first_col_values = detect_df.iloc[
                                                    :, 0
                                                ].astype(str)

                                                # Check if first column contains other separator characters
                                                wrong_sep_indicators = []
                                                for sep_char in [
                                                    ";",
                                                    ",",
                                                    "\t",
                                                    "|",
                                                    ":",
                                                ]:
                                                    if sep_char != detect_params["sep"]:
                                                        if any(
                                                            sep_char in str(val)
                                                            for val in first_col_values
                                                        ):
                                                            wrong_sep_indicators.append(
                                                                sep_char
                                                            )

                                                if wrong_sep_indicators:
                                                    issues.append(
                                                        f"First column contains '{', '.join(wrong_sep_indicators)}' characters. "
                                                        f"Current separator '{detect_params['sep']}' might be incorrect."
                                                    )

                                                # Check if we have only one column but suspect more data
                                                if (
                                                    actual_cols == 1
                                                    and len(first_col_values) > 0
                                                ):
                                                    # Look for common separators in the single column
                                                    sample_val = (
                                                        str(first_col_values.iloc[0])
                                                        if len(first_col_values) > 0
                                                        else ""
                                                    )
                                                    potential_seps = []
                                                    for sep_char in [
                                                        ";",
                                                        ",",
                                                        "\t",
                                                        "|",
                                                    ]:
                                                        if sep_char in sample_val:
                                                            potential_seps.append(
                                                                sep_char
                                                            )

                                                    if potential_seps:
                                                        issues.append(
                                                            f"Only 1 column detected, but data contains '{', '.join(potential_seps)}'. "
                                                            f"Consider changing separator from '{detect_params['sep']}'."
                                                        )

                                                # Check for mostly empty columns (sign of wrong separator)
                                                if actual_cols > 1:
                                                    empty_cols = []
                                                    for col_idx in range(
                                                        1, min(actual_cols, 5)
                                                    ):
                                                        col_data = detect_df.iloc[
                                                            :, col_idx
                                                        ]
                                                        if (
                                                            col_data.isna().all()
                                                            or (
                                                                col_data.astype(
                                                                    str
                                                                ).str.strip()
                                                                == ""
                                                            ).all()
                                                        ):
                                                            empty_cols.append(col_idx)

                                                    if len(empty_cols) >= 2:
                                                        issues.append(
                                                            f"Columns {empty_cols} appear to be empty. "
                                                            f"This might indicate incorrect separator."
                                                        )

                                            # STEP 3: Try full read with user configuration for final validation
                                            full_read_params = {
                                                "filepath_or_buffer": file_path,
                                                "sep": file_item.get("separator", ";"),
                                                "quotechar": file_item.get(
                                                    "quote", '"'
                                                ),
                                                "encoding": file_item.get(
                                                    "encoding", "utf-8"
                                                ),
                                                "nrows": 500,  # Full sample for final test
                                            }

                                            # Apply header/column settings
                                            if file_item.get("header", True):
                                                full_read_params["header"] = 0
                                            else:
                                                full_read_params["header"] = None
                                                columns = file_item.get("columns", [])
                                                if columns:
                                                    # Only apply column names if count matches
                                                    if len(columns) == actual_cols:
                                                        full_read_params["names"] = (
                                                            columns
                                                        )
                                                    else:
                                                        # Don't force wrong number of columns
                                                        pass

                                            # Final read with configuration
                                            final_df = pd.read_csv(**full_read_params)
                                            final_rows, final_cols = final_df.shape

                                            # Build parameter info string
                                            param_info = f"sep='{full_read_params['sep']}', quote='{full_read_params['quotechar']}', encoding='{full_read_params['encoding']}'"
                                            if not file_item.get("header", True):
                                                user_columns = file_item.get(
                                                    "columns", []
                                                )
                                                param_info += f", custom columns ({len(user_columns)})"

                                            # Display results
                                            if issues:
                                                issue_text = "; ".join(issues)
                                                ui.notify(
                                                    f"⚠️ File configuration issues detected: {actual_cols} actual columns. {issue_text} ({param_info})",
                                                    type="warning",
                                                )
                                            else:
                                                column_preview = list(
                                                    final_df.columns[:5]
                                                )
                                                column_text = f"{column_preview}{' ...' if len(final_df.columns) > 5 else ''}"
                                                ui.notify(
                                                    f"✅ File configuration appears correct: {actual_cols} columns detected, {final_rows} rows read. "
                                                    f"Columns: {column_text} ({param_info})",
                                                    type="positive",
                                                )

                                        except ImportError:
                                            ui.notify(
                                                "❌ pandas library not available for file checking.",
                                                type="negative",
                                            )
                                        except Exception as e:
                                            import pandas as pd

                                            if isinstance(e, pd.errors.EmptyDataError):
                                                ui.notify(
                                                    "❌ File is empty or has no valid data.",
                                                    type="negative",
                                                )
                                            elif isinstance(e, pd.errors.ParserError):
                                                ui.notify(
                                                    f"❌ Parse error: {str(e)}",
                                                    type="negative",
                                                )
                                            elif isinstance(e, UnicodeDecodeError):
                                                ui.notify(
                                                    f"❌ Encoding error: {str(e)}. Try a different encoding.",
                                                    type="negative",
                                                )
                                            elif isinstance(e, FileNotFoundError):
                                                ui.notify(
                                                    f"❌ File not found: {file_path}",
                                                    type="negative",
                                                )
                                            elif isinstance(e, PermissionError):
                                                ui.notify(
                                                    f"❌ Permission denied accessing file: {file_path}",
                                                    type="negative",
                                                )
                                            else:
                                                ui.notify(
                                                    f"❌ Error reading file: {str(e)}",
                                                    type="negative",
                                                )

                                    check_button = (
                                        ui.button(
                                            "Check Configuration",
                                            icon="check_circle",
                                            on_click=lambda e, idx=i: check_file_config(
                                                idx
                                            ),
                                        )
                                        .props("color=primary outline size=sm")
                                        .classes("mt-3")
                                    )
                                    if not extract_active:
                                        check_button.props("disable")

                                    # Initial validation for existing file paths
                                    if file_item.get("file_path"):
                                        validate_file_path(
                                            file_item.get("file_path"),
                                            file_path_input,
                                            file_status_label,
                                        )

                        def remove_file_config(idx):
                            if idx < len(file_config):
                                file_config.pop(idx)
                                mark_changed()
                                render_extract()

                        # Add new file
                        if extract_active:
                            with ui.card().classes("mt-2 p-3 border-dashed"):
                                ui.label("Add New File").classes("font-medium mb-2")

                                new_file_data = {
                                    "active": True,
                                    "project": "",
                                    "file_path": "",
                                    "separator": ";",
                                    "quote": '"',
                                    "dateformat": "%d-%m-%Y",
                                    "encoding": "utf-8",
                                    "header": True,
                                    "columns": [],
                                    "all_varchar": True,
                                }

                                def on_new_project_change(e):
                                    new_file_data["project"] = e.value

                                def on_new_file_path_change(e):
                                    new_file_data["file_path"] = e.value

                                def on_new_separator_change(e):
                                    new_file_data["separator"] = e.value

                                def on_new_quote_change(e):
                                    new_file_data["quote"] = e.value

                                def on_new_dateformat_change(e):
                                    new_file_data["dateformat"] = e.value

                                def on_new_encoding_change(e):
                                    new_file_data["encoding"] = e.value

                                def on_new_header_change(e):
                                    new_file_data["header"] = e.value
                                    # Re-render to show/hide columns field
                                    render_extract()

                                def on_new_all_varchar_change(e):
                                    new_file_data["all_varchar"] = e.value

                                def on_new_columns_change(e):
                                    # Parse comma-separated values and strip whitespace
                                    columns = [
                                        col.strip()
                                        for col in e.value.split(",")
                                        if col.strip()
                                    ]
                                    new_file_data["columns"] = columns

                                def add_file():
                                    if (
                                        new_file_data["project"]
                                        and new_file_data["file_path"]
                                    ):
                                        # Check if header is False and columns are required
                                        if (
                                            not new_file_data["header"]
                                            and not new_file_data["columns"]
                                        ):
                                            ui.notify(
                                                "Please provide column names when file has no header row.",
                                                type="warning",
                                            )
                                            return

                                        file_config.append(new_file_data.copy())
                                        mark_changed()
                                        render_extract()
                                    else:
                                        ui.notify(
                                            "Please provide both project name and file path.",
                                            type="warning",
                                        )

                                with ui.column().classes("gap-2 w-full"):
                                    # Project for new file
                                    ui.input(
                                        label="Project",
                                        placeholder="Enter project name",
                                        on_change=on_new_project_change,
                                    ).props("dense").classes("w-full")

                                    # File path for new file
                                    ui.input(
                                        label="File Path",
                                        placeholder="e.g. /path/to/your/file.csv",
                                        on_change=on_new_file_path_change,
                                    ).props("dense").classes("w-full")

                                    # File format settings for new file
                                    with ui.row().classes("gap-4 mt-3"):
                                        ui.input(
                                            label="Separator",
                                            value=new_file_data["separator"],
                                            placeholder=";",
                                            on_change=on_new_separator_change,
                                        ).props("dense").classes("w-24")

                                        ui.input(
                                            label="Quote",
                                            value=new_file_data["quote"],
                                            placeholder='"',
                                            on_change=on_new_quote_change,
                                        ).props("dense").classes("w-24")

                                        ui.input(
                                            label="Date format",
                                            value=new_file_data["dateformat"],
                                            placeholder="%d-%m-%Y",
                                            on_change=on_new_dateformat_change,
                                        ).props("dense").classes("w-32")

                                        ui.select(
                                            label="Encoding",
                                            options=["utf-8", "utf-16", "latin-1"],
                                            value=new_file_data["encoding"],
                                            on_change=on_new_encoding_change,
                                        ).props("dense").classes("w-32")

                                    # Header toggle for new file
                                    ui.switch(
                                        "File has header row",
                                        value=new_file_data["header"],
                                        on_change=on_new_header_change,
                                    ).classes("mt-3")

                                    # All varchar toggle for new file
                                    ui.switch(
                                        "Import all columns as text (VARCHAR) - recommended to avoid conversion errors",
                                        value=new_file_data["all_varchar"],
                                        on_change=on_new_all_varchar_change,
                                    ).classes("mt-2")

                                    # Columns field for new file (only shown when header is False)
                                    if not new_file_data["header"]:
                                        columns_value = ", ".join(
                                            new_file_data["columns"]
                                        )
                                        ui.input(
                                            label="Column Names",
                                            value=columns_value,
                                            placeholder="column1, column2, column3",
                                            on_change=on_new_columns_change,
                                        ).props("dense").classes("w-full mt-2")

                                        ui.label(
                                            "Enter column names separated by commas (required when file has no header)"
                                        ).classes("text-sm text-gray-600 mt-1")

                                    ui.button(
                                        "Add File", icon="add", on_click=add_file
                                    ).props("color=primary").classes("mt-3")

                        else:
                            # Show disabled state message when extract is not active
                            with ui.card().classes("mt-2 p-3 bg-gray-100"):
                                ui.label(
                                    "File configurations are disabled because Extract is not active."
                                ).classes("text-sm text-gray-500 italic")

            def render_inforcom_config(extract_config):
                """Render INFORCOM adapter configuration."""
                inforcom_config = extract_config.setdefault("inforcom", {})

                ui.label("INFORCOM Configuration").classes("text-lg font-semibold mb-3")
                ui.label(
                    "ODBC-based extraction from INFORCOM (INFOR.* tables)"
                ).classes("text-sm mb-4")

                with ui.column().classes("gap-4"):
                    # ODBC Connection String
                    def on_odbc_connstr_change(e):
                        inforcom_config["odbc_connstr"] = e.value
                        mark_changed()

                    ui.textarea(
                        label="ODBC Connection String",
                        value=inforcom_config.get(
                            "odbc_connstr",
                            "Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        ),
                        placeholder="Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        on_change=on_odbc_connstr_change,
                    ).props("outlined").classes("w-full").style("min-height: 100px")

                    # Options row
                    with ui.row().classes("gap-4"):
                        # Chunk Size
                        def on_chunk_size_change(e):
                            try:
                                inforcom_config["chunk_size"] = (
                                    int(e.value) if e.value else 10000
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Chunk Size",
                            value=inforcom_config.get("chunk_size", 10000),
                            min=1,
                            on_change=on_chunk_size_change,
                        ).props("dense").classes("w-48")

                        # Timeout
                        def on_timeout_change(e):
                            try:
                                inforcom_config["timeout"] = (
                                    int(e.value) if e.value else 300
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Timeout (seconds)",
                            value=inforcom_config.get("timeout", 300),
                            min=1,
                            on_change=on_timeout_change,
                        ).props("dense").classes("w-48")

                        # Table Prefix
                        def on_table_prefix_change(e):
                            inforcom_config["table_prefix"] = e.value
                            mark_changed()

                        ui.input(
                            label="Table Prefix",
                            value=inforcom_config.get("table_prefix", "INFOR."),
                            placeholder="INFOR.",
                            on_change=on_table_prefix_change,
                        ).props("dense").classes("w-48")

                    # Table Selector
                    def on_table_selector_change(e):
                        inforcom_config["table_selector"] = e.value
                        mark_changed()
                        # Show/hide tables list based on selection
                        if e.value == "all":
                            tables_container.set_visibility(True)
                        else:
                            tables_container.set_visibility(False)

                    table_selector = (
                        ui.select(
                            label="Table Selector",
                            options=["all", "join_parser"],
                            value=inforcom_config.get("table_selector", "join_parser"),
                            on_change=on_table_selector_change,
                        )
                        .props("dense")
                        .classes("w-48")
                    )

                    # Tables List (conditionally visible)
                    current_tables = inforcom_config.get("tables", [])

                    with ui.column().classes("w-full") as tables_container:
                        ui.label("Tables").classes("text-base font-medium mt-2")

                        def on_tables_change(e):
                            inforcom_config["tables"] = e.value if e.value else []
                            mark_changed()

                        default_inforcom_tables = (
                            global_config.get("extract", {})
                            .get("inforcom", {})
                            .get("tables", [])
                        )

                        # Combine default tables with any custom tables that might be in current config
                        all_available_tables = list(
                            set(default_inforcom_tables + current_tables)
                        )
                        all_available_tables.sort()

                        tables_select = (
                            ui.select(
                                options=all_available_tables,
                                value=current_tables,
                                multiple=True,
                                label="Select tables to extract",
                                on_change=on_tables_change,
                            )
                            .props("use-chips clearable use-input input-debounce=0")
                            .classes("w-full")
                        )

                        # Add custom table functionality
                        with ui.row().classes("gap-2 items-end mt-3"):
                            new_table_input = (
                                ui.input(
                                    label="Add custom table",
                                    placeholder="Enter table name (e.g. INFOR.CUSTOM_TABLE)",
                                )
                                .props("dense")
                                .classes("flex-1")
                            )

                            def add_custom_table():
                                table_name = new_table_input.value.strip()
                                if (
                                    table_name
                                    and table_name not in all_available_tables
                                ):
                                    # Add to available options
                                    all_available_tables.append(table_name)
                                    all_available_tables.sort()
                                    tables_select.options = all_available_tables

                                    # Add to current selection
                                    current_selection = inforcom_config.get(
                                        "tables", []
                                    )
                                    if table_name not in current_selection:
                                        current_selection.append(table_name)
                                        inforcom_config["tables"] = current_selection
                                        tables_select.value = current_selection
                                        mark_changed()

                                    # Clear input
                                    new_table_input.value = ""
                                    ui.notify(
                                        f"Added table: {table_name}", type="positive"
                                    )
                                elif table_name in all_available_tables:
                                    ui.notify(
                                        f"Table '{table_name}' already exists",
                                        type="warning",
                                    )
                                else:
                                    ui.notify(
                                        "Please enter a table name", type="warning"
                                    )

                            ui.button(
                                "Add Table", icon="add", on_click=add_custom_table
                            ).props("size=sm color=primary")

                        ui.label(
                            "You can add custom tables not in the default list above."
                        ).classes("text-sm text-gray-600 mt-2")

                    # Set initial visibility based on current selection
                    if inforcom_config.get("table_selector", "join_parser") != "all":
                        tables_container.set_visibility(False)

            def render_sapecc_config(extract_config):
                """Render SAP ECC adapter configuration."""
                sapecc_config = extract_config.setdefault("sapecc", {})

                ui.label("SAP ECC Configuration").classes("text-lg font-semibold mb-3")
                ui.label("HANA DB-based extraction from SAP ECC").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # Connection parameters row
                    with ui.row().classes("gap-4 w-full"):
                        # Address
                        def on_address_change(e):
                            sapecc_config["address"] = e.value
                            mark_changed()

                        ui.input(
                            label="Server Address",
                            value=sapecc_config.get("address", "your_sap_hana_server"),
                            placeholder="your_sap_hana_server",
                            on_change=on_address_change,
                        ).props("dense").classes("flex-grow")

                        # Port
                        def on_port_change(e):
                            try:
                                port = int(e.value) if e.value else 30015
                                if 1 <= port <= 65535:
                                    sapecc_config["port"] = port
                                    mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Port",
                            value=sapecc_config.get("port", 30015),
                            min=1,
                            max=65535,
                            on_change=on_port_change,
                        ).props("dense").classes("w-32")

                    # Credentials row
                    with ui.row().classes("gap-4 w-full"):
                        # Username
                        def on_user_change(e):
                            sapecc_config["user"] = e.value
                            mark_changed()

                        ui.input(
                            label="Username",
                            value=sapecc_config.get("user", "your_username"),
                            placeholder="your_username",
                            on_change=on_user_change,
                        ).props("dense").classes("flex-1")

                        # Password
                        def on_password_change(e):
                            sapecc_config["password"] = e.value
                            mark_changed()

                        ui.input(
                            label="Password",
                            value=sapecc_config.get("password", "your_password"),
                            placeholder="your_password",
                            password=True,
                            password_toggle_button=True,
                            on_change=on_password_change,
                        ).props("dense").classes("flex-1")

                    # Settings row
                    with ui.row().classes("gap-4 items-center"):
                        # Autocommit
                        def on_autocommit_change(e):
                            sapecc_config["autocommit"] = e.value
                            mark_changed()

                        ui.switch(
                            "Autocommit",
                            value=sapecc_config.get("autocommit", True),
                            on_change=on_autocommit_change,
                        )

                        # Chunk Size
                        def on_chunk_size_change(e):
                            try:
                                sapecc_config["chunk_size"] = (
                                    int(e.value) if e.value else 10000
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Chunk Size",
                            value=sapecc_config.get("chunk_size", 10000),
                            min=1,
                            on_change=on_chunk_size_change,
                        ).props("dense").classes("w-48")

                    # Table Selector
                    def on_table_selector_change(e):
                        sapecc_config["table_selector"] = e.value
                        mark_changed()
                        # Show/hide tables list based on selection
                        if e.value == "all":
                            tables_container.set_visibility(True)
                        else:
                            tables_container.set_visibility(False)

                    table_selector = (
                        ui.select(
                            label="Table Selector",
                            options=["all", "join_parser"],
                            value=sapecc_config.get("table_selector", "join_parser"),
                            on_change=on_table_selector_change,
                        )
                        .props("dense")
                        .classes("w-48")
                    )

                    # Tables List (conditionally visible)
                    current_tables = sapecc_config.get("tables", [])

                    with ui.column().classes("w-full") as tables_container:
                        ui.label("Tables").classes("text-base font-medium mt-2")

                        def on_tables_change(e):
                            sapecc_config["tables"] = e.value if e.value else []
                            mark_changed()

                        default_sapecc_tables = (
                            global_config.get("extract", {})
                            .get("sapecc", {})
                            .get("tables", [])
                        )

                        # Combine default tables with any custom tables that might be in current config
                        all_available_tables = list(
                            set(default_sapecc_tables + current_tables)
                        )
                        all_available_tables.sort()

                        tables_select = (
                            ui.select(
                                options=all_available_tables,
                                value=current_tables,
                                multiple=True,
                                label="Select tables to extract",
                                on_change=on_tables_change,
                            )
                            .props("use-chips clearable use-input input-debounce=0")
                            .classes("w-full")
                        )

                        # Add custom table functionality
                        with ui.row().classes("gap-2 items-end mt-3"):
                            new_table_input = (
                                ui.input(
                                    label="Add custom table",
                                    placeholder="Enter table name (e.g. SAPSR3.CUSTOM_TABLE)",
                                )
                                .props("dense")
                                .classes("flex-1")
                            )

                            def add_custom_table():
                                table_name = new_table_input.value.strip()
                                if (
                                    table_name
                                    and table_name not in all_available_tables
                                ):
                                    # Add to available options
                                    all_available_tables.append(table_name)
                                    all_available_tables.sort()
                                    tables_select.options = all_available_tables

                                    # Add to current selection
                                    current_selection = sapecc_config.get("tables", [])
                                    if table_name not in current_selection:
                                        current_selection.append(table_name)
                                        sapecc_config["tables"] = current_selection
                                        tables_select.value = current_selection
                                        mark_changed()

                                    # Clear input
                                    new_table_input.value = ""
                                    ui.notify(
                                        f"Added table: {table_name}", type="positive"
                                    )
                                elif table_name in all_available_tables:
                                    ui.notify(
                                        f"Table '{table_name}' already exists",
                                        type="warning",
                                    )
                                else:
                                    ui.notify(
                                        "Please enter a table name", type="warning"
                                    )

                            ui.button(
                                "Add Table", icon="add", on_click=add_custom_table
                            ).props("size=sm color=primary")

                        ui.label(
                            "You can add custom tables not in the default list above."
                        ).classes("text-sm text-gray-600 mt-2")

                    # Set initial visibility based on current selection
                    if sapecc_config.get("table_selector", "join_parser") != "all":
                        tables_container.set_visibility(False)

            def render_generic_odbc_config(extract_config):
                """Render Generic ODBC adapter configuration."""
                generic_odbc_config = extract_config.setdefault("genericodbc", {})

                ui.label("Generic ODBC Configuration").classes(
                    "text-lg font-semibold mb-3"
                )
                ui.label(
                    "Generic ODBC-based extraction from any ODBC-compatible database"
                ).classes("text-sm mb-4")

                with ui.column().classes("gap-4"):
                    # ODBC Connection String
                    def on_odbc_connstr_change(e):
                        generic_odbc_config["odbc_connstr"] = e.value
                        mark_changed()

                    ui.textarea(
                        label="ODBC Connection String",
                        value=generic_odbc_config.get(
                            "odbc_connstr",
                            "Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        ),
                        placeholder="Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        on_change=on_odbc_connstr_change,
                    ).props("outlined").classes("w-full").style("min-height: 100px")

                    # Options row
                    with ui.row().classes("gap-4"):
                        # Chunk Size
                        def on_chunk_size_change(e):
                            try:
                                generic_odbc_config["chunk_size"] = (
                                    int(e.value) if e.value else 10000
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Chunk Size",
                            value=generic_odbc_config.get("chunk_size", 10000),
                            min=1,
                            on_change=on_chunk_size_change,
                        ).props("dense").classes("w-48")

                        # Timeout
                        def on_timeout_change(e):
                            try:
                                generic_odbc_config["timeout"] = (
                                    int(e.value) if e.value else 300
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Timeout (seconds)",
                            value=generic_odbc_config.get("timeout", 300),
                            min=1,
                            on_change=on_timeout_change,
                        ).props("dense").classes("w-48")

                        # Table Prefix (optional for generic ODBC)
                        def on_table_prefix_change(e):
                            generic_odbc_config["table_prefix"] = e.value
                            mark_changed()

                        ui.input(
                            label="Table Prefix (optional)",
                            value=generic_odbc_config.get("table_prefix", ""),
                            placeholder="e.g. schema_name.",
                            on_change=on_table_prefix_change,
                        ).props("dense").classes("w-48")

                    # Table Selector
                    def on_table_selector_change(e):
                        generic_odbc_config["table_selector"] = e.value
                        mark_changed()
                        # Show/hide tables list based on selection
                        if e.value == "all":
                            tables_container.set_visibility(True)
                        else:
                            tables_container.set_visibility(False)

                    table_selector = (
                        ui.select(
                            label="Table Selector",
                            options=["all", "join_parser"],
                            value=generic_odbc_config.get(
                                "table_selector", "join_parser"
                            ),
                            on_change=on_table_selector_change,
                        )
                        .props("dense")
                        .classes("w-48")
                    )

                    # Tables List (conditionally visible)
                    current_tables = generic_odbc_config.get("tables", [])

                    with ui.column().classes("w-full") as tables_container:
                        ui.label("Tables").classes("text-base font-medium mt-2")

                        def on_tables_change(e):
                            generic_odbc_config["tables"] = e.value if e.value else []
                            mark_changed()

                        default_generic_odbc_tables = (
                            global_config.get("extract", {})
                            .get("genericodbc", {})
                            .get("tables", [])
                        )

                        # Combine default tables with any custom tables that might be in current config
                        all_available_tables = list(
                            set(default_generic_odbc_tables + current_tables)
                        )
                        all_available_tables.sort()

                        tables_select = (
                            ui.select(
                                options=all_available_tables,
                                value=current_tables,
                                multiple=True,
                                label="Select tables to extract",
                                on_change=on_tables_change,
                            )
                            .props("use-chips clearable use-input input-debounce=0")
                            .classes("w-full")
                        )

                        # Add custom table functionality
                        with ui.row().classes("gap-2 items-end mt-3"):
                            new_table_input = (
                                ui.input(
                                    label="Add custom table",
                                    placeholder="Enter table name (e.g. schema.table_name)",
                                )
                                .props("dense")
                                .classes("flex-1")
                            )

                            def add_custom_table():
                                table_name = new_table_input.value.strip()
                                if (
                                    table_name
                                    and table_name not in all_available_tables
                                ):
                                    # Add to available options
                                    all_available_tables.append(table_name)
                                    all_available_tables.sort()
                                    tables_select.options = all_available_tables

                                    # Add to current selection
                                    current_selection = generic_odbc_config.get(
                                        "tables", []
                                    )
                                    if table_name not in current_selection:
                                        current_selection.append(table_name)
                                        generic_odbc_config["tables"] = (
                                            current_selection
                                        )
                                        tables_select.value = current_selection
                                        mark_changed()

                                    # Clear input
                                    new_table_input.value = ""
                                    ui.notify(
                                        f"Added table: {table_name}", type="positive"
                                    )
                                elif table_name in all_available_tables:
                                    ui.notify(
                                        f"Table '{table_name}' already exists",
                                        type="warning",
                                    )
                                else:
                                    ui.notify(
                                        "Please enter a table name", type="warning"
                                    )

                            ui.button(
                                "Add Table", icon="add", on_click=add_custom_table
                            ).props("size=sm color=primary")

                        ui.label(
                            "You can add custom tables not in the default list above."
                        ).classes("text-sm text-gray-600 mt-2")

                    # Set initial visibility based on current selection
                    if (
                        generic_odbc_config.get("table_selector", "join_parser")
                        != "all"
                    ):
                        tables_container.set_visibility(False)

            def render_proalpha_config(extract_config):
                """Render ProAlpha adapter configuration."""
                proalpha_config = extract_config.setdefault("proalpha", {})

                ui.label("ProAlpha Configuration").classes("text-lg font-semibold mb-3")
                ui.label("ODBC-based extraction from ProAlpha ERP system").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # ODBC Connection String
                    def on_odbc_connstr_change(e):
                        proalpha_config["odbc_connstr"] = e.value
                        mark_changed()

                    ui.textarea(
                        label="ODBC Connection String",
                        value=proalpha_config.get(
                            "odbc_connstr",
                            "Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        ),
                        placeholder="Driver={SQL Server};Server=your_server;Database=your_database;UID=your_username;PWD=your_password;",
                        on_change=on_odbc_connstr_change,
                    ).props("outlined").classes("w-full").style("min-height: 100px")

                    # Options row
                    with ui.row().classes("gap-4"):
                        # Chunk Size
                        def on_chunk_size_change(e):
                            try:
                                proalpha_config["chunk_size"] = (
                                    int(e.value) if e.value else 10000
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Chunk Size",
                            value=proalpha_config.get("chunk_size", 10000),
                            min=1,
                            on_change=on_chunk_size_change,
                        ).props("dense").classes("w-48")

                        # Timeout
                        def on_timeout_change(e):
                            try:
                                proalpha_config["timeout"] = (
                                    int(e.value) if e.value else 300
                                )
                                mark_changed()
                            except ValueError:
                                pass

                        ui.number(
                            label="Timeout (seconds)",
                            value=proalpha_config.get("timeout", 300),
                            min=1,
                            on_change=on_timeout_change,
                        ).props("dense").classes("w-48")

                        # Table Prefix
                        def on_table_prefix_change(e):
                            proalpha_config["table_prefix"] = e.value
                            mark_changed()

                        ui.input(
                            label="Table Prefix",
                            value=proalpha_config.get("table_prefix", "PROALPHA."),
                            placeholder="PROALPHA.",
                            on_change=on_table_prefix_change,
                        ).props("dense").classes("w-48")

                    # Table Selector
                    def on_table_selector_change(e):
                        proalpha_config["table_selector"] = e.value
                        mark_changed()
                        # Show/hide tables list based on selection
                        if e.value == "all":
                            tables_container.set_visibility(True)
                        else:
                            tables_container.set_visibility(False)

                    table_selector = (
                        ui.select(
                            label="Table Selector",
                            options=["all", "join_parser"],
                            value=proalpha_config.get("table_selector", "join_parser"),
                            on_change=on_table_selector_change,
                        )
                        .props("dense")
                        .classes("w-48")
                    )

                    # Tables List (conditionally visible)
                    current_tables = proalpha_config.get("tables", [])

                    with ui.column().classes("w-full") as tables_container:
                        ui.label("Tables").classes("text-base font-medium mt-2")

                        def on_tables_change(e):
                            proalpha_config["tables"] = e.value if e.value else []
                            mark_changed()

                        default_proalpha_tables = (
                            global_config.get("extract", {})
                            .get("proalpha", {})
                            .get("tables", [])
                        )

                        # Combine default tables with any custom tables that might be in current config
                        all_available_tables = list(
                            set(default_proalpha_tables + current_tables)
                        )
                        all_available_tables.sort()

                        tables_select = (
                            ui.select(
                                options=all_available_tables,
                                value=current_tables,
                                multiple=True,
                                label="Select tables to extract",
                                on_change=on_tables_change,
                            )
                            .props("use-chips clearable use-input input-debounce=0")
                            .classes("w-full")
                        )

                        # Add custom table functionality
                        with ui.row().classes("gap-2 items-end mt-3"):
                            new_table_input = (
                                ui.input(
                                    label="Add custom table",
                                    placeholder="Enter table name (e.g. PROALPHA.CUSTOM_TABLE)",
                                )
                                .props("dense")
                                .classes("flex-1")
                            )

                            def add_custom_table():
                                table_name = new_table_input.value
                                if table_name and table_name.strip():
                                    table_name = table_name.strip()
                                    if table_name not in all_available_tables:
                                        # Add to the options list
                                        all_available_tables.append(table_name)
                                        all_available_tables.sort()
                                        tables_select.options = all_available_tables

                                        # Add to current selection
                                        current_selection = proalpha_config.get(
                                            "tables", []
                                        )
                                        if table_name not in current_selection:
                                            current_selection.append(table_name)
                                            proalpha_config["tables"] = (
                                                current_selection
                                            )
                                            tables_select.value = current_selection
                                            mark_changed()

                                        ui.notify(
                                            f"Added table: {table_name}",
                                            type="positive",
                                        )
                                        new_table_input.value = ""
                                    else:
                                        ui.notify(
                                            f"Table {table_name} already exists",
                                            type="warning",
                                        )
                                else:
                                    ui.notify(
                                        "Please enter a table name", type="warning"
                                    )

                            ui.button(
                                "Add Table", icon="add", on_click=add_custom_table
                            ).props("size=sm color=primary")

                        ui.label(
                            "You can add custom tables not in the default list above."
                        ).classes("text-sm text-gray-600 mt-2")

                    # Set initial visibility based on current selection
                    if proalpha_config.get("table_selector", "join_parser") != "all":
                        tables_container.set_visibility(False)

            def render_transform():
                if not content_container:
                    return

                content_container.clear()
                with content_container:
                    ui.label("Transform").classes("text-2xl font-semibold")
                    ui.separator()
                    ui.label("Define transformations, mappings and validations.")

                    # Transform configuration
                    transform_config = form_state["data"].setdefault("transform", {})

                    # General Transform Settings Card
                    with ui.card().classes("mt-4"):
                        ui.label("General Transform Settings").classes(
                            "text-lg font-semibold mb-3"
                        )

                        with ui.column().classes("gap-3"):
                            # Transform active toggle
                            def on_transform_active_change(e):
                                transform_config["active"] = e.value
                                mark_changed()
                                # Re-render the transform section to update disabled states
                                render_transform()

                            transform_active = transform_config.get("active", True)

                            ui.switch(
                                "Transform active",
                                value=transform_active,
                                on_change=on_transform_active_change,
                            )

                            # Load to Nemo toggle
                            def on_load_to_nemo_change(e):
                                transform_config["load_to_nemo"] = e.value
                                mark_changed()
                                # Re-render the transform section to update disabled states
                                render_transform()

                            load_to_nemo_switch = ui.switch(
                                "Load to Nemo",
                                value=transform_config.get("load_to_nemo", True),
                                on_change=on_load_to_nemo_change,
                            )
                            if not transform_active:
                                load_to_nemo_switch.props("disable")

                            # Delete temp files toggle
                            def on_delete_temp_files_change(e):
                                transform_config["delete_temp_files"] = e.value
                                mark_changed()

                            load_to_nemo = transform_config.get("load_to_nemo", True)
                            delete_temp_files_switch = ui.switch(
                                "Delete temporary files",
                                value=transform_config.get("delete_temp_files", True),
                                on_change=on_delete_temp_files_change,
                            )
                            if not transform_active or not load_to_nemo:
                                delete_temp_files_switch.props("disable")

                            # Dump files toggle
                            def on_dump_files_change(e):
                                transform_config["dump_files"] = e.value
                                mark_changed()

                            dump_files_switch = ui.switch(
                                "Dump files",
                                value=transform_config.get("dump_files", True),
                                on_change=on_dump_files_change,
                            )
                            if not transform_active:
                                dump_files_switch.props("disable")

                            # Nemo project prefix
                            def on_nemo_project_prefix_change(e):
                                transform_config["nemo_project_prefix"] = e.value
                                mark_changed()

                            nemo_prefix_input = (
                                ui.input(
                                    label="Nemo Project Prefix",
                                    value=transform_config.get(
                                        "nemo_project_prefix", "mmt"
                                    ),
                                    on_change=on_nemo_project_prefix_change,
                                )
                                .props("dense")
                                .classes("w-80")
                            )
                            if not transform_active:
                                nemo_prefix_input.props("disable")

                    # Transform Components with Tabs
                    with ui.card().classes("mt-4"):
                        ui.label("Transform Components").classes(
                            "text-lg font-semibold mb-3"
                        )

                        transform_components_container = ui.column().classes("w-full")

                        if transform_active:
                            with transform_components_container:
                                with ui.tabs().classes("w-full") as tabs:
                                    join_tab = ui.tab("Join")
                                    mapping_tab = ui.tab("Mapping")
                                    nonempty_tab = ui.tab("Non-Empty")
                                    duplicate_tab = ui.tab("Duplicate")

                                with ui.tab_panels(tabs, value=join_tab).classes(
                                    "w-full"
                                ):
                                    with ui.tab_panel(join_tab):
                                        render_transform_join_config(transform_config)

                                    with ui.tab_panel(mapping_tab):
                                        render_transform_mapping_config(
                                            transform_config
                                        )

                                    with ui.tab_panel(duplicate_tab):
                                        render_transform_duplicate_config(
                                            transform_config
                                        )
                                    with ui.tab_panel(nonempty_tab):
                                        render_transform_nonempty_config(
                                            transform_config
                                        )

                        else:
                            with transform_components_container:
                                ui.label(
                                    "Transform components are disabled because Transform is not active."
                                ).classes("text-sm text-gray-500 italic p-4")

            def render_transform_join_config(transform_config):
                """Render join transformation configuration."""
                join_config = transform_config.setdefault("join", {})

                ui.label("Join Configuration").classes("text-lg font-semibold mb-3")
                ui.label("Configure table joins and relationships").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # Join active toggle
                    def on_join_active_change(e):
                        join_config["active"] = e.value
                        mark_changed()
                        # Re-render the transform section to update disabled states
                        render_transform()

                    join_active = join_config.get("active", True)

                    ui.switch(
                        "Join active",
                        value=join_active,
                        on_change=on_join_active_change,
                    )

                    # Limit configuration
                    def on_limit_change(e):
                        try:
                            join_config["limit"] = int(e.value) if e.value else None
                            mark_changed()
                        except ValueError:
                            pass

                    limit_input = (
                        ui.number(
                            label="Limit (optional)",
                            value=join_config.get("limit", None),
                            min=1,
                            placeholder="No limit",
                            on_change=on_limit_change,
                        )
                        .props("dense clearable")
                        .classes("w-48 mt-3")
                    )
                    if not join_active:
                        limit_input.props("disable")

                    ui.label(
                        "Set a limit on the number of rows to process during joins (leave empty for no limit)"
                    ).classes("text-sm text-gray-600 mb-2")

                    # Joins configuration
                    joins_config_label = ui.label("Join Configurations").classes(
                        "text-md font-medium mt-4"
                    )
                    if not join_active:
                        joins_config_label.classes("text-gray-500")

                    joins_config = join_config.setdefault("joins", {})

                    # Display existing joins
                    for join_name, join_settings in joins_config.items():
                        with ui.card().classes("mt-2 p-3"):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                join_label = ui.label(f"Join: {join_name}").classes(
                                    "font-medium"
                                )
                                if not join_active:
                                    join_label.classes("text-gray-500")

                                with ui.row().classes("gap-2"):
                                    customize_button = ui.button(
                                        "Customize",
                                        icon="settings",
                                        on_click=lambda name=join_name, file=join_settings.get(
                                            "file", ""
                                        ): customize_join(
                                            name, file
                                        ),
                                    ).props("flat size=sm color=primary")
                                    if not join_active:
                                        customize_button.props("disable")

                                    delete_button = ui.button(
                                        icon="delete",
                                        on_click=lambda name=join_name: remove_join(
                                            name
                                        ),
                                    ).props("flat round color=negative size=sm")
                                    if not join_active:
                                        delete_button.props("disable")

                            def on_join_item_active_change(e, name=join_name):
                                joins_config[name]["active"] = e.value
                                mark_changed()

                            def on_join_item_file_change(e, name=join_name):
                                joins_config[name]["file"] = e.value
                                mark_changed()

                            join_item_switch = ui.switch(
                                "Active",
                                value=join_settings.get("active", True),
                                on_change=lambda e, name=join_name: on_join_item_active_change(
                                    e, name
                                ),
                            )
                            if not join_active:
                                join_item_switch.props("disable")

                            join_file_input = (
                                ui.input(
                                    label="File",
                                    value=join_settings.get("file", ""),
                                    placeholder="Path to join configuration file",
                                    on_change=lambda e, name=join_name: on_join_item_file_change(
                                        e, name
                                    ),
                                )
                                .props("dense")
                                .classes("w-full")
                            )
                            if not join_active:
                                join_file_input.props("disable")

                    def remove_join(join_name):
                        if join_name in joins_config:
                            del joins_config[join_name]
                            mark_changed()
                            render_transform()

                    def customize_join(join_name, file):
                        """Customize join configuration - placeholder for your implementation."""

                        adapter = (
                            form_state["data"]
                            .get("extract", {})
                            .get("adapter", "unknown_adapter")
                        )
                        indiv_file = Path(f"./config/{adapter}/joins/") / file
                        if indiv_file.exists():
                            ui.notify(
                                f"Custom join file {indiv_file} exists", type="negative"
                            )
                            return

                        default_file = (
                            importlib_resources.files("nemo_library_etl")
                            / "adapter"
                            / "migman"
                            / "config"
                            / "joins"
                            / f"{adapter}"
                            / file
                        )

                        # check for existence of the default file
                        if not default_file.exists():
                            ui.notify(
                                f"Default join configuration file {default_file} not found.",
                                type="negative",
                            )
                            return

                        # copy default file to the indiv_file location
                        indiv_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(default_file, indiv_file)
                        ui.notify(
                            f"Customized join file created at {indiv_file}", type="info"
                        )

                    # Add new join
                    if join_active:
                        with ui.card().classes("mt-2 p-3 border-dashed"):
                            ui.label("Add New Join").classes("font-medium mb-2")

                            new_join_name = {"value": ""}
                            new_join_file = {"value": ""}

                            def on_new_join_name_change(e):
                                new_join_name["value"] = e.value

                            def on_new_join_file_change(e):
                                new_join_file["value"] = e.value

                            def add_join():
                                if new_join_name["value"] and new_join_file["value"]:
                                    joins_config[new_join_name["value"]] = {
                                        "active": True,
                                        "file": new_join_file["value"],
                                    }
                                    mark_changed()
                                    render_transform()

                            with ui.row().classes("gap-2 items-end w-full"):
                                ui.input(
                                    label="Join Name",
                                    placeholder="Enter join name",
                                    on_change=on_new_join_name_change,
                                ).props("dense").classes("flex-1")

                                ui.input(
                                    label="File Path",
                                    placeholder="Path to join configuration file",
                                    on_change=on_new_join_file_change,
                                ).props("dense").classes("flex-1")

                                ui.button(
                                    "Add Join", icon="add", on_click=add_join
                                ).props("color=primary")
                    else:
                        # Show disabled state message when joins is not active
                        with ui.card().classes("mt-2 p-3 bg-gray-100"):
                            ui.label(
                                "Join configurations are disabled because Join is not active."
                            ).classes("text-sm text-gray-500 italic")

            def render_transform_mapping_config(transform_config):
                """Render mapping transformation configuration."""
                mapping_config = transform_config.setdefault("mapping", {})

                ui.label("Mapping Configuration").classes("text-lg font-semibold mb-3")
                ui.label("Configure field mappings and transformations").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # Mapping active toggle
                    def on_mapping_active_change(e):
                        mapping_config["active"] = e.value
                        mark_changed()

                    ui.switch(
                        "Mapping active",
                        value=mapping_config.get("active", True),
                        on_change=on_mapping_active_change,
                    )

                    ui.label(
                        "This transformation will apply field mappings and data transformations according to the configured rules."
                    ).classes("text-sm text-gray-600")

            def render_transform_nonempty_config(transform_config):
                """Render non-empty transformation configuration."""
                nonempty_config = transform_config.setdefault("nonempty", {})

                ui.label("Non-Empty Configuration").classes(
                    "text-lg font-semibold mb-3"
                )
                ui.label("Filter out empty records during transformation").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # Non-empty active toggle
                    def on_nonempty_active_change(e):
                        nonempty_config["active"] = e.value
                        mark_changed()

                    ui.switch(
                        "Non-empty filter active",
                        value=nonempty_config.get("active", True),
                        on_change=on_nonempty_active_change,
                    )

                    ui.label(
                        "This transformation will remove records with empty or null values in key fields."
                    ).classes("text-sm text-gray-600")

            def render_transform_duplicate_config(transform_config):
                """Render duplicate transformation configuration."""
                duplicate_config = transform_config.setdefault("duplicate", {})

                ui.label("Duplicate Configuration").classes(
                    "text-lg font-semibold mb-3"
                )
                ui.label("Configure duplicate detection and handling").classes(
                    "text-sm mb-4"
                )

                with ui.column().classes("gap-4"):
                    # Duplicate active toggle
                    def on_duplicate_active_change(e):
                        duplicate_config["active"] = e.value
                        mark_changed()
                        # Re-render the transform section to update disabled states
                        render_transform()

                    duplicate_active = duplicate_config.get("active", True)

                    ui.switch(
                        "Duplicate detection active",
                        value=duplicate_active,
                        on_change=on_duplicate_active_change,
                    )

                    # Duplicates configuration
                    duplicates_config_label = ui.label(
                        "Duplicate Configurations"
                    ).classes("text-md font-medium mt-4")
                    if not duplicate_active:
                        duplicates_config_label.classes("text-gray-500")

                    duplicates_config = duplicate_config.setdefault("duplicates", {})

                    # Display existing duplicate configurations
                    for object_name, duplicate_settings in duplicates_config.items():
                        with ui.card().classes("mt-2 p-3"):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                object_label = ui.label(
                                    f"Object: {object_name}"
                                ).classes("font-medium")
                                if not duplicate_active:
                                    object_label.classes("text-gray-500")

                                delete_button = ui.button(
                                    icon="delete",
                                    on_click=lambda name=object_name: remove_duplicate_config(
                                        name
                                    ),
                                ).props("flat round color=negative size=sm")
                                if not duplicate_active:
                                    delete_button.props("disable")

                            def on_duplicate_obj_active_change(e, name=object_name):
                                duplicates_config[name]["active"] = e.value
                                mark_changed()

                            def on_threshold_change(e, name=object_name):
                                try:
                                    threshold = int(e.value)
                                    if 0 <= threshold <= 100:
                                        duplicates_config[name]["threshold"] = threshold
                                        mark_changed()
                                except (ValueError, TypeError):
                                    pass

                            def on_primary_key_change(e, name=object_name):
                                duplicates_config[name]["primary_key"] = e.value
                                mark_changed()

                            def on_fields_change(e, name=object_name):
                                # Split by comma and clean up
                                fields = [
                                    field.strip()
                                    for field in e.value.split(",")
                                    if field.strip()
                                ]
                                duplicates_config[name]["fields"] = fields
                                mark_changed()

                            duplicate_obj_switch = ui.switch(
                                "Active",
                                value=duplicate_settings.get("active", True),
                                on_change=lambda e, name=object_name: on_duplicate_obj_active_change(
                                    e, name
                                ),
                            )
                            if not duplicate_active:
                                duplicate_obj_switch.props("disable")

                            with ui.row().classes("gap-2 w-full"):
                                threshold_input = (
                                    ui.number(
                                        label="Similarity Threshold (%)",
                                        value=duplicate_settings.get("threshold", 90),
                                        min=0,
                                        max=100,
                                        on_change=lambda e, name=object_name: on_threshold_change(
                                            e, name
                                        ),
                                    )
                                    .props("dense")
                                    .classes("w-48")
                                )
                                if not duplicate_active:
                                    threshold_input.props("disable")

                                primary_key_input = (
                                    ui.input(
                                        label="Primary Key",
                                        value=duplicate_settings.get("primary_key", ""),
                                        placeholder="Enter primary key field",
                                        on_change=lambda e, name=object_name: on_primary_key_change(
                                            e, name
                                        ),
                                    )
                                    .props("dense")
                                    .classes("flex-1")
                                )
                                if not duplicate_active:
                                    primary_key_input.props("disable")

                            fields_input = (
                                ui.input(
                                    label="Fields (comma-separated)",
                                    value=", ".join(
                                        duplicate_settings.get("fields", [])
                                    ),
                                    placeholder="field1, field2, field3",
                                    on_change=lambda e, name=object_name: on_fields_change(
                                        e, name
                                    ),
                                )
                                .props("dense")
                                .classes("w-full")
                            )
                            if not duplicate_active:
                                fields_input.props("disable")

                    def remove_duplicate_config(object_name):
                        if object_name in duplicates_config:
                            del duplicates_config[object_name]
                            mark_changed()
                            render_transform()

                    # Add new duplicate configuration
                    if duplicate_active:
                        with ui.card().classes("mt-2 p-3 border-dashed"):
                            ui.label("Add New Duplicate Configuration").classes(
                                "font-medium mb-2"
                            )

                            new_object_name = {"value": ""}
                            new_primary_key = {"value": ""}
                            new_threshold = {"value": 90}
                            new_fields = {"value": ""}

                            def on_new_object_name_change(e):
                                new_object_name["value"] = e.value

                            def on_new_primary_key_change(e):
                                new_primary_key["value"] = e.value

                            def on_new_threshold_change(e):
                                try:
                                    threshold = int(e.value)
                                    if 0 <= threshold <= 100:
                                        new_threshold["value"] = threshold
                                except (ValueError, TypeError):
                                    pass

                            def on_new_fields_change(e):
                                new_fields["value"] = e.value

                            def add_duplicate_config():
                                if (
                                    new_object_name["value"]
                                    and new_primary_key["value"]
                                ):
                                    fields = [
                                        field.strip()
                                        for field in new_fields["value"].split(",")
                                        if field.strip()
                                    ]
                                    duplicates_config[new_object_name["value"]] = {
                                        "active": True,
                                        "threshold": new_threshold["value"],
                                        "primary_key": new_primary_key["value"],
                                        "fields": fields,
                                    }
                                    mark_changed()
                                    render_transform()

                            with ui.column().classes("gap-2 w-full"):
                                with ui.row().classes("gap-2 w-full"):
                                    ui.input(
                                        label="Object Name",
                                        placeholder="Enter object name",
                                        on_change=on_new_object_name_change,
                                    ).props("dense").classes("flex-1")

                                    ui.number(
                                        label="Threshold (%)",
                                        value=90,
                                        min=0,
                                        max=100,
                                        on_change=on_new_threshold_change,
                                    ).props("dense").classes("w-32")

                                with ui.row().classes("gap-2 w-full"):
                                    ui.input(
                                        label="Primary Key",
                                        placeholder="Enter primary key field",
                                        on_change=on_new_primary_key_change,
                                    ).props("dense").classes("flex-1")

                                    ui.input(
                                        label="Fields (comma-separated)",
                                        placeholder="field1, field2, field3",
                                        on_change=on_new_fields_change,
                                    ).props("dense").classes("flex-1")

                                ui.button(
                                    "Add Configuration",
                                    icon="add",
                                    on_click=add_duplicate_config,
                                ).props("color=primary")
                    else:
                        # Show disabled state message when duplicate detection is not active
                        with ui.card().classes("mt-2 p-3 bg-gray-100"):
                            ui.label(
                                "Duplicate configurations are disabled because Duplicate detection is not active."
                            ).classes("text-sm text-gray-500 italic")

            def render_load():
                if not content_container:
                    return

                content_container.clear()
                with content_container:
                    ui.label("Load").classes("text-2xl font-semibold")
                    ui.separator()
                    ui.label("Load data into target system.")

                    # Load active toggle
                    load_config = form_state["data"].setdefault("load", {})

                    with ui.card().classes("mt-4"):
                        ui.label("Load Settings").classes("text-lg font-semibold mb-2")

                        def on_load_active_change(e):
                            load_config["active"] = e.value
                            mark_changed()
                            # Re-render the load section to update disabled states
                            render_load()

                        load_active = load_config.get("active", True)

                        ui.switch(
                            "Load active",
                            value=load_active,
                            on_change=on_load_active_change,
                        )

                        def on_delete_temp_files_change(e):
                            load_config["delete_temp_files"] = e.value
                            mark_changed()

                        delete_temp_files_switch = ui.switch(
                            "Delete temp files",
                            value=load_config.get("delete_temp_files", True),
                            on_change=on_delete_temp_files_change,
                        )
                        if not load_active:
                            delete_temp_files_switch.props("disable")

                        def on_delete_projects_before_load_change(e):
                            load_config["delete_projects_before_load"] = e.value
                            mark_changed()

                        delete_projects_before_load_switch = ui.switch(
                            "Delete projects before load",
                            value=load_config.get("delete_projects_before_load", True),
                            on_change=on_delete_projects_before_load_change,
                        )
                        if (
                            not load_active
                            or load_config.get(
                                "development_deficiency_mining_only", False
                            )
                            or load_config.get("development_load_reports_only", False)
                        ):
                            delete_projects_before_load_switch.props("disable")

                        def update_delete_projects_before_load_state():
                            """Helper function to update the delete_projects_before_load switch state."""
                            development_deficiency_only = load_config.get(
                                "development_deficiency_mining_only", False
                            )
                            development_reports_only = load_config.get(
                                "development_load_reports_only", False
                            )

                            if development_deficiency_only or development_reports_only:
                                load_config["delete_projects_before_load"] = False
                                delete_projects_before_load_switch.value = False
                                delete_projects_before_load_switch.props("disable")
                            else:
                                # If both development switches are disabled and load is active, re-enable the switch
                                if load_active:
                                    delete_projects_before_load_switch.props(
                                        remove="disable"
                                    )

                        def on_development_deficiency_mining_only_change(e):
                            load_config["development_deficiency_mining_only"] = e.value
                            update_delete_projects_before_load_state()
                            mark_changed()

                        development_deficiency_mining_only_switch = ui.switch(
                            "DEVELOPMENT: deficiency mining only",
                            value=load_config.get(
                                "development_deficiency_mining_only", False
                            ),
                            on_change=on_development_deficiency_mining_only_change,
                        )
                        if not load_active:
                            development_deficiency_mining_only_switch.props("disable")

                        def on_development_load_reports_only_change(e):
                            load_config["development_load_reports_only"] = e.value
                            update_delete_projects_before_load_state()
                            mark_changed()

                        development_load_reports_only_switch = ui.switch(
                            "DEVELOPMENT: load reports only",
                            value=load_config.get(
                                "development_load_reports_only", False
                            ),
                            on_change=on_development_load_reports_only_change,
                        )
                        if not load_active:
                            development_load_reports_only_switch.props("disable")

                        def on_nemo_project_prefix_change(e):
                            load_config["nemo_project_prefix"] = e.value
                            mark_changed()

                        nemo_project_prefix_input = (
                            ui.input(
                                label="NEMO project prefix",
                                value=load_config.get("nemo_project_prefix", "mml"),
                                placeholder="",
                                on_change=on_nemo_project_prefix_change,
                            )
                            .props("dense")
                            .classes("w-[36rem] mt-3")
                        )
                        if not load_active:
                            nemo_project_prefix_input.props("disable")

            # ---------- LEFT DRAWER ----------
            with ui.left_drawer(value=True, fixed=True).classes("w-64 p-4"):
                ui.label("MigMan UI").classes("text-lg font-semibold mb-4")

                def make_nav_button(name: str, cb):
                    b = (
                        ui.button(name, on_click=cb)
                        .props("flat")
                        .classes("w-full justify-start mb-2")
                    )
                    nav_buttons[name] = b
                    return b

                make_nav_button(
                    "Global", lambda: (set_active("Global"), render_global())
                )
                make_nav_button("Setup", lambda: (set_active("Setup"), render_setup()))
                make_nav_button(
                    "Extract", lambda: (set_active("Extract"), render_extract())
                )
                make_nav_button(
                    "Transform", lambda: (set_active("Transform"), render_transform())
                )
                make_nav_button("Load", lambda: (set_active("Load"), render_load()))

            # ---------- MAIN CONTENT ----------
            with ui.element("div"):
                with ui.column() as content:
                    content_container = content
                    set_active("Global")
                    render_global()

        ui.run(reload=False, show=open_browser)
