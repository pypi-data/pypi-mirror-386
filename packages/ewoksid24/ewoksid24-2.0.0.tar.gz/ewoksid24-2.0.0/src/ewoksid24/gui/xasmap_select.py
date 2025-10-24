import json
import os
from typing import List
from typing import Optional
from typing import Tuple

from silx.gui import icons
from silx.gui import qt

from .settings import get_settings


class XasMapInputWidget(qt.QWidget):
    # Signal to notify the main window when the input is changed
    data_changed = qt.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings: Optional[qt.QSettings] = None

        # Buttons to add/remove XAS maps
        xasmap_box = qt.QGroupBox("XAS maps:")
        xasmap_layout = qt.QVBoxLayout(xasmap_box)

        # List of XAS maps
        self._xasmaps_widget = qt.QListWidget()
        self._xasmaps_widget.setSelectionMode(qt.QListWidget.SingleSelection)
        self._xasmaps_widget.itemSelectionChanged.connect(self._select_xasmap)
        self._xasmaps_widget.setContextMenuPolicy(qt.Qt.CustomContextMenu)
        self._xasmaps_widget.customContextMenuRequested.connect(
            self._xasmaps_context_menu
        )

        delete_button = qt.QPushButton("Remove")
        delete_button.clicked.connect(self._remove_selected_xasmap)

        # Layout to hold the current XAS maps
        xasmap_layout.addWidget(self._xasmaps_widget)
        xasmap_layout.addWidget(delete_button, alignment=qt.Qt.AlignRight)

        # Layout to hold the XAS map parameters
        parameters_box = qt.QGroupBox("Parameters:")
        parameters_layout = qt.QVBoxLayout(parameters_box)

        # XAS map parameters: files
        self._last_dir = os.path.expanduser("~")

        replace_files_button = qt.QToolButton()
        replace_files_button.setIcon(icons.getQIcon("document-open"))
        replace_files_button.setToolTip("Replace file")
        replace_files_button.clicked.connect(self._replace_files)

        add_files_button = qt.QToolButton()
        add_files_button.setIcon(icons.getQIcon("folder"))
        add_files_button.setToolTip("Add files")
        add_files_button.clicked.connect(self._add_files)

        self._filenames_widget = qt.QListWidget()
        self._filenames_widget.setSelectionMode(qt.QListWidget.ExtendedSelection)
        self._filenames_widget.setContextMenuPolicy(qt.Qt.CustomContextMenu)
        self._filenames_widget.customContextMenuRequested.connect(
            self._filenames_context_menu
        )
        self._filenames_widget.itemChanged.connect(self._parameters_changed)
        self._filenames_widget.model().rowsInserted.connect(self._parameters_changed)
        self._filenames_widget.model().rowsRemoved.connect(self._parameters_changed)

        file_layout = qt.QHBoxLayout()
        file_layout.addWidget(self._filenames_widget)
        file_selection_layout = qt.QVBoxLayout()
        file_selection_layout.addWidget(replace_files_button)
        file_selection_layout.addWidget(add_files_button)
        file_layout.addLayout(file_selection_layout)
        file_row_widget = qt.QWidget()
        file_row_widget.setLayout(file_layout)

        # XAS map parameters: all others
        parameter_form = qt.QFormLayout()
        parameters_layout.addLayout(parameter_form)

        self._dim0_counter_input = qt.QLineEdit()
        self._dim1_counter_input = qt.QLineEdit()
        self._energy_counter_input = qt.QLineEdit()
        self._mu_counter_input = qt.QLineEdit()
        self._scan_range_input = qt.QLineEdit()
        self._exclude_scans_input = qt.QLineEdit()

        self._dim0_counter_input.textChanged.connect(self._parameters_changed)
        self._dim1_counter_input.textChanged.connect(self._parameters_changed)
        self._energy_counter_input.textChanged.connect(self._parameters_changed)
        self._mu_counter_input.textChanged.connect(self._parameters_changed)
        self._scan_range_input.textChanged.connect(self._parameters_changed)
        self._exclude_scans_input.textChanged.connect(self._parameters_changed)

        parameter_form.addRow("Files", file_row_widget)
        parameter_form.addRow("X-Axis", self._dim0_counter_input)
        parameter_form.addRow("Y-Axis", self._dim1_counter_input)
        parameter_form.addRow("Energy", self._energy_counter_input)
        parameter_form.addRow("Mu", self._mu_counter_input)
        parameter_form.addRow("Scan ranges", self._scan_range_input)
        parameter_form.addRow("Exclude scans", self._exclude_scans_input)

        button_layout = qt.QHBoxLayout()
        parameters_layout.addLayout(button_layout)

        create_button = qt.QPushButton("New")
        create_button.clicked.connect(self._create_xasmap)

        self._modify_button = qt.QPushButton("Update")
        self._modify_button.setEnabled(False)
        self._modify_button.clicked.connect(self._modify_xasmap)

        self._reset_button = qt.QPushButton("Reset")
        self._reset_button.setEnabled(False)
        self._reset_button.clicked.connect(self._select_xasmap)

        button_layout.addWidget(create_button)
        button_layout.addWidget(self._modify_button)
        button_layout.addWidget(self._reset_button)

        # Add all components to the main layout
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(xasmap_box)
        main_layout.addWidget(parameters_box)

    def add_xasmap(
        self,
        filenames: Optional[List[str]] = None,
        dim0_counter: Optional[str] = None,
        dim1_counter: Optional[str] = None,
        energy_counter: Optional[str] = None,
        mu_counter: Optional[str] = None,
        scan_ranges: Optional[List[List[int]]] = None,
        exclude_scans: Optional[List[int]] = None,
    ) -> None:
        do_create = False
        if filenames:
            self._set_filenames(filenames)
            do_create = True

        if dim0_counter is not None:
            self._set_parameter_as_string(self._dim0_counter_input, dim0_counter)
            do_create = True

        if dim1_counter is not None:
            self._set_parameter_as_string(self._dim1_counter_input, dim1_counter)
            do_create = True

        if energy_counter is not None:
            self._set_parameter_as_string(self._energy_counter_input, energy_counter)
            do_create = True

        if mu_counter is not None:
            self._set_parameter_as_string(self._mu_counter_input, mu_counter)
            do_create = True

        if scan_ranges:
            scan_ranges = _parse_list_of_lists_of_ints(scan_ranges, two_tuple=True)
            self._set_scan_ranges(scan_ranges)
            do_create = True
        elif filenames:
            self._set_scan_ranges(None)

        if exclude_scans:
            exclude_scans = _parse_list_of_lists_of_ints(exclude_scans, two_tuple=False)
            self._set_exclude_scans(exclude_scans)
            do_create = True
        elif filenames:
            self._set_exclude_scans(None)

        if do_create:
            self._create_xasmap()

    def get_current_xasmap(self) -> Optional[dict]:
        return self._get_selected_xasmap()

    def save_settings(self) -> None:
        if self._settings is None:
            return
        xasmaps = self._get_xasmaps()
        xasmap_index = self._xasmaps_widget.currentRow()

        self._settings.beginGroup("XasMapInputWidget")
        self._settings.setValue("xasmaps", xasmaps)
        self._settings.setValue("xasmap_index", xasmap_index)
        self._settings.endGroup()

    def load_settings(self) -> None:
        """Load input sets from QSettings and restore the form fields."""
        if self._settings is None:
            self._settings = get_settings()

        self._settings.beginGroup("XasMapInputWidget")
        xasmaps = self._settings.value("xasmaps", None)
        xasmap_index = int(self._settings.value("xasmap_index", -1))
        self._settings.endGroup()

        self._set_xasmaps(xasmaps)
        if xasmap_index != -1:
            self._xasmaps_widget.setCurrentRow(xasmap_index)

    def _add_files(self) -> None:
        """Open a QFileDialog to select multiple files to add to the current ones."""
        filenames, _ = qt.QFileDialog.getOpenFileNames(
            self,
            "Select XAS Data Files",
            self._last_dir,
            "HDF5 Files (*.h5);;All Files (*)",
        )
        self._add_filenames(filenames)

    def _replace_files(self) -> None:
        """Open a QFileDialog to select a single file to replace the current ones."""
        filename, _ = qt.QFileDialog.getOpenFileName(
            self,
            "Select XAS Data File",
            self._last_dir,
            "HDF5 Files (*.h5);;All Files (*)",
        )
        self._set_filenames([filename])

    def _get_filenames(self) -> List[str]:
        nitems = self._filenames_widget.count()
        return [
            self._filenames_widget.item(i).data(qt.Qt.UserRole) for i in range(nitems)
        ]

    def _set_filenames(self, filenames: Optional[List[Tuple[str, str]]]) -> None:
        self._filenames_widget.clear()
        if not filenames:
            return
        for filename in filenames:
            _ = self._add_filename(filename)

    def _add_filenames(self, filenames: Optional[List[str]]) -> None:
        if not filenames:
            return
        for filename in filenames:
            self._add_filename(filename)
        self.save_settings()

    def _add_filename(self, filename: str) -> None:
        self._last_dir = os.path.dirname(filename)
        filelabel = os.path.basename(filename)
        filename = os.path.abspath(filename)

        item = qt.QListWidgetItem(filelabel)
        item.setData(qt.Qt.UserRole, filename)
        self._filenames_widget.addItem(item)

    def _filenames_context_menu(self, pos) -> None:
        """Show the context menu for right-click on the file list."""
        context_menu = qt.QMenu(self)

        duplicate_action = context_menu.addAction("Duplicate")
        remove_action = context_menu.addAction("Remove")
        action = context_menu.exec_(self._filenames_widget.mapToGlobal(pos))

        if action == remove_action:
            self._remove_selected_filenames()
        elif action == duplicate_action:
            self._duplicate_selected_filenames()

    def _remove_selected_filenames(self) -> None:
        """Remove the selected files from the file list."""
        selected_items = self._filenames_widget.selectedItems()
        if selected_items is None:
            return
        for selected_item in selected_items:
            index = self._filenames_widget.row(selected_item)
            self._filenames_widget.takeItem(index)
        self.save_settings()

    def _duplicate_selected_filenames(self) -> None:
        """Duplicate the selected files in the file list."""
        selected_items = self._filenames_widget.selectedItems()
        if selected_items is None:
            return
        for selected_item in selected_items:
            filename = selected_item.data(qt.Qt.UserRole)
            self._add_filename(filename)
        self.save_settings()

    def _get_xasmaps(self) -> List[dict]:
        nitems = self._xasmaps_widget.count()
        return [
            self._xasmaps_widget.item(i).data(qt.Qt.UserRole) for i in range(nitems)
        ]

    def _set_xasmaps(self, xasmaps: Optional[List[dict]]) -> None:
        self._xasmaps_widget.clear()
        if xasmaps:
            for xasmap in xasmaps:
                self._add_xasmap(xasmap)

    def _add_xasmap(self, xasmap: dict) -> None:
        label = self._get_xasmap_id(xasmap)
        item = qt.QListWidgetItem(label)
        item.setData(qt.Qt.UserRole, xasmap)
        self._xasmaps_widget.addItem(item)

    def _select_last_xasmap(self) -> None:
        count = self._xasmaps_widget.count()
        if count > 0:
            self._xasmaps_widget.setCurrentRow(count - 1)

    def _get_xasmap_id(self, xasmap: dict) -> str:
        filenames = xasmap.get("filenames", [])
        scan_ranges = xasmap.get("scan_ranges", [])
        if not scan_ranges:
            scan_ranges = [None] * len(filenames)

        names = []
        for filename, scan_range in zip(filenames, scan_ranges):
            name = os.path.basename(filename)

            if scan_range:
                name = f"{name}: {scan_range[0]} -> {scan_range[1]}"
            names.append(name)

        return ", ".join(names)

    def _get_selected_xasmap(self) -> Optional[dict]:
        selected_item = self._xasmaps_widget.currentItem()
        if selected_item:
            return selected_item.data(qt.Qt.UserRole)

    def _xasmaps_context_menu(self, pos) -> None:
        """Show the context menu for right-click on the XAS map list."""
        context_menu = qt.QMenu(self)

        remove_action = context_menu.addAction("Remove")
        action = context_menu.exec_(self._xasmaps_widget.mapToGlobal(pos))

        if action == remove_action:
            self._remove_selected_xasmap()

    def _remove_selected_xasmap(self) -> None:
        """Remove the current XAS map."""
        selected_index = self._xasmaps_widget.currentRow()
        if selected_index != -1:
            self._xasmaps_widget.takeItem(selected_index)
            self.save_settings()
            self._select_xasmap()

    def _create_xasmap(self) -> None:
        """Add the current parameters as a new XAS map."""
        xasmap = self._get_edited_xasmap()
        if xasmap:
            self._add_xasmap(xasmap)
            self.save_settings()
            self._select_last_xasmap()

    def _emit_xasmap(self, xasmap: dict) -> None:
        self.data_changed.emit(xasmap)

    def _modify_xasmap(self) -> None:
        selected_item = self._xasmaps_widget.currentItem()
        if selected_item is None:
            return
        xasmap = self._get_edited_xasmap()
        if xasmap is None:
            return
        selected_item.setData(qt.Qt.UserRole, xasmap)
        label = self._get_xasmap_id(xasmap)
        selected_item.setText(label)
        self.save_settings()
        self._select_xasmap()

    def _get_edited_xasmap(self) -> Optional[dict]:
        try:
            filenames = self._get_xasmap_filenames()
            scan_ranges = self._get_scan_ranges()
            exclude_scans = self._get_exclude_scans()
            dim0_counter = self._get_parameter_as_string(
                self._dim0_counter_input, "X-Axis"
            )
            dim1_counter = self._get_parameter_as_string(
                self._dim1_counter_input, "Y-Axis"
            )
            energy_counter = self._get_parameter_as_string(
                self._energy_counter_input, "Energy"
            )
            mu_counter = self._get_parameter_as_string(self._mu_counter_input, "Mu")
        except _Return:
            return None

        return {
            "filenames": filenames,
            "dim0_counter": dim0_counter,
            "dim1_counter": dim1_counter,
            "energy_counter": energy_counter,
            "mu_counter": mu_counter,
            "scan_ranges": scan_ranges,
            "exclude_scans": exclude_scans,
        }

    def _select_xasmap(self) -> None:
        xasmap = self._get_selected_xasmap()
        if not xasmap:
            return
        self._set_parameter_as_string(
            self._dim0_counter_input, xasmap.get("dim0_counter")
        )
        self._set_parameter_as_string(
            self._dim1_counter_input, xasmap.get("dim1_counter")
        )
        self._set_parameter_as_string(
            self._energy_counter_input, xasmap.get("energy_counter")
        )
        self._set_parameter_as_string(self._mu_counter_input, xasmap.get("mu_counter"))
        self._set_scan_ranges(xasmap.get("scan_ranges"))
        self._set_exclude_scans(xasmap.get("exclude_scans"))
        self._set_filenames(xasmap.get("filenames"))
        self._update_button_states(False)
        self._emit_xasmap(xasmap)

    def _get_xasmap_filenames(self) -> List[str]:
        filenames = self._get_filenames()
        if not filenames:
            qt.QMessageBox.warning(
                self, "No Files Selected", "Please select at least one file."
            )
            raise _Return
        return filenames

    def _get_parameter_as_string(self, w: qt.QLineEdit, name: str) -> str:
        value = w.text()
        if not value:
            qt.QMessageBox.warning(self, "Invalid Input", f"'{name}' is not defined")
            raise _Return
        return value

    def _set_parameter_as_string(self, w: qt.QLineEdit, value: Optional[str]) -> None:
        if value is None:
            w.setText("")
        else:
            w.setText(str(value))

    def _get_scan_ranges(self) -> Optional[List[List[int]]]:
        scan_ranges = self._scan_range_input.text() or None
        if not scan_ranges:
            return None
        try:
            return _parse_list_of_lists_of_ints(scan_ranges, two_tuple=True)
        except (TypeError, json.JSONDecodeError) as e:
            qt.QMessageBox.warning(
                self,
                "Invalid Value",
                f"The scan ranges must be a list of lists of two integers ({e}).",
            )
            raise _Return

    def _set_scan_ranges(self, scan_ranges: Optional[List[List[int]]]) -> None:
        if scan_ranges:
            self._scan_range_input.setText(json.dumps(scan_ranges))
        else:
            self._scan_range_input.setText("")

    def _get_exclude_scans(self) -> Optional[List[List[int]]]:
        exclude_scans = self._exclude_scans_input.text() or None
        if not exclude_scans:
            return None
        try:
            return _parse_list_of_lists_of_ints(exclude_scans, two_tuple=False)
        except (TypeError, json.JSONDecodeError) as e:
            qt.QMessageBox.warning(
                self,
                "Invalid Value",
                f"The scans to exclude must be a list of lists of integers ({e}).",
            )
            raise _Return

    def _set_exclude_scans(self, exclude_scans: Optional[List[List[int]]]) -> None:
        if exclude_scans:
            self._exclude_scans_input.setText(json.dumps(exclude_scans))
        else:
            self._exclude_scans_input.setText("")

    def _parameters_changed(self):
        self._update_button_states(True)

    def _update_button_states(self, enable: bool) -> None:
        self._modify_button.setEnabled(enable)
        self._reset_button.setEnabled(enable)


def _parse_list_of_lists_of_ints(
    value: str, two_tuple: bool
) -> Optional[List[List[int]]]:
    value = json.loads(value)
    if value is None:
        return None
    if isinstance(value, int):
        if two_tuple:
            value = [[value, value]]
        else:
            value = [[value]]
    if not isinstance(value, list):
        raise TypeError("Not a list")
    if len({isinstance(v, int) for v in value}) == 2:
        raise TypeError("List is a mixture of integers and other types")
    if all(isinstance(v, int) for v in value):
        value = [value]
    for lst in value:
        if not all(isinstance(v, int) for v in lst):
            raise TypeError("Sub-list must contain integers")
        if two_tuple and len(lst) != 2:
            raise TypeError("Sub-list only has two values (first and last scan number)")
    return value


class _Return(Exception):
    pass
