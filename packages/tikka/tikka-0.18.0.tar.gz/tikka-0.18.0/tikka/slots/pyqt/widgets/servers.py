# Copyright 2021 Vincent Texier <vit@free.fr>
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import sys
from typing import Optional

from PyQt5.QtCore import QMutex, QPoint, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyledItemDelegate, QWidget

from tikka.domains.application import Application
from tikka.domains.entities.constants import DATA_PATH
from tikka.domains.entities.events import (
    ConnectionsEvent,
    CurrencyEvent,
    IndexersEvent,
    NodesEvent,
)
from tikka.domains.entities.indexer import Indexer
from tikka.domains.entities.node import Node
from tikka.slots.pyqt.entities.constants import (
    INDEXERS_TABLE_SORT_COLUMN_PREFERENCES_KEY,
    INDEXERS_TABLE_SORT_ORDER_PREFERENCES_KEY,
    NODES_TABLE_SORT_COLUMN_PREFERENCES_KEY,
    NODES_TABLE_SORT_ORDER_PREFERENCES_KEY,
)
from tikka.slots.pyqt.entities.worker import AsyncQWorker
from tikka.slots.pyqt.models.indexers import IndexersTableModel
from tikka.slots.pyqt.models.nodes import NodesTableModel
from tikka.slots.pyqt.resources.gui.widgets.servers_rc import Ui_ServersWidget
from tikka.slots.pyqt.widgets.indexer_menu import IndexerPopupMenu
from tikka.slots.pyqt.widgets.node_menu import NodePopupMenu
from tikka.slots.pyqt.windows.indexer_add import IndexerAddWindow
from tikka.slots.pyqt.windows.node_add import NodeAddWindow


class HighlightNodeDelegate(QStyledItemDelegate):
    """
    Class to highlight connected node row
    """

    def __init__(self, table_model, application):
        """
        Initialize HighlightNodeDelegate instance

        :param table_model: TableModel of
        :param application:
        """
        super().__init__()
        self.table_model = table_model
        self.application = application

    def paint(self, painter, option, index):
        # get current url/row node
        current_node_url = self.application.nodes.get_current_url()
        node = self.table_model.nodes[index.row()]
        # check connection...
        if node.url == current_node_url:
            color = (
                QColor("lightgreen")
                if self.application.connections.node.is_connected()
                else QColor("lightcoral")
            )
            painter.fillRect(option.rect, color)

        # paint rectangle
        super().paint(painter, option, index)


class HighlightIndexerDelegate(QStyledItemDelegate):
    """
    Class to highlight connected indexer row
    """

    def __init__(self, table_model, application):
        """
        Initialize HighlightIndexerDelegate instance

        :param table_model: TableModel of
        :param application:
        """
        super().__init__()
        self.table_model = table_model
        self.application = application

    def paint(self, painter, option, index):
        # get current url/row indexer
        current_indexer_url = self.application.indexers.get_current_url()
        indexer = self.table_model.indexers[index.row()]
        # check connection...
        if indexer.url == current_indexer_url:
            color = (
                QColor("lightgreen")
                if self.application.connections.indexer.is_connected()
                else QColor("lightcoral")
            )
            painter.fillRect(option.rect, color)

        # paint rectangle
        super().paint(painter, option, index)


class ServersWidget(QWidget, Ui_ServersWidget):
    """
    ServersWidget class
    """

    def __init__(
        self,
        application: Application,
        mutex: QMutex,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Init ServersWidget instance

        :param application: Application instance
        :param mutex: QMutex instance
        :param parent: MainWindow instance
        """
        super().__init__(parent=parent)
        self.setupUi(self)

        self.application = application
        self.mutex = mutex
        self._ = self.application.translator.gettext
        self.selected_node: Optional[Node] = None
        self.selected_indexer: Optional[Indexer] = None

        self.nodes_table_model = NodesTableModel(self.application)
        self.nodesTableView.setModel(self.nodes_table_model)
        self.nodesTableView.resizeColumnsToContents()
        self.nodesTableView.resizeRowsToContents()
        self.nodesTableView.customContextMenuRequested.connect(
            self.on_node_context_menu
        )
        self.nodesTableView.setItemDelegate(
            HighlightNodeDelegate(self.nodes_table_model, self.application)
        )
        pref_sort_column = self.application.repository.preferences.get(
            NODES_TABLE_SORT_COLUMN_PREFERENCES_KEY
        )
        if pref_sort_column is None:
            sort_column = 0
        else:
            sort_column = int(pref_sort_column)

        pref_sort_order = self.application.repository.preferences.get(
            NODES_TABLE_SORT_ORDER_PREFERENCES_KEY
        )
        if pref_sort_order is None:
            sort_order = int(Qt.SortOrder.AscendingOrder)
        else:
            sort_order = int(pref_sort_order)
        self.nodesTableView.sortByColumn(sort_column, sort_order)

        self.indexers_table_model = IndexersTableModel(self.application)
        self.indexersTableView.setModel(self.indexers_table_model)
        self.indexersTableView.resizeColumnsToContents()
        self.indexersTableView.resizeRowsToContents()
        self.indexersTableView.customContextMenuRequested.connect(
            self.on_indexer_context_menu
        )
        self.indexersTableView.setItemDelegate(
            HighlightIndexerDelegate(self.indexers_table_model, self.application)
        )
        pref_sort_column = self.application.repository.preferences.get(
            INDEXERS_TABLE_SORT_COLUMN_PREFERENCES_KEY
        )
        if pref_sort_column is None:
            sort_column = 0
        else:
            sort_column = int(pref_sort_column)

        pref_sort_order = self.application.repository.preferences.get(
            INDEXERS_TABLE_SORT_ORDER_PREFERENCES_KEY
        )
        if pref_sort_order is None:
            sort_order = int(Qt.SortOrder.AscendingOrder)
        else:
            sort_order = int(pref_sort_order)
        self.indexersTableView.sortByColumn(sort_column, sort_order)

        # events
        self.addNodeButton.clicked.connect(self._on_add_node_button_clicked)
        self.addIndexerButton.clicked.connect(self._on_add_indexer_button_clicked)
        self.nodesTableView.doubleClicked.connect(self.on_node_table_double_click)
        self.indexersTableView.doubleClicked.connect(self.on_indexer_table_double_click)

        # subscribe to application events
        self.application.event_dispatcher.add_event_listener(
            CurrencyEvent.EVENT_TYPE_CHANGED, self._on_currency_event
        )
        self.application.event_dispatcher.add_event_listener(
            NodesEvent.EVENT_TYPE_LIST_CHANGED, self._on_node_list_changed_event
        )
        self.application.event_dispatcher.add_event_listener(
            IndexersEvent.EVENT_TYPE_LIST_CHANGED, self._on_indexer_list_changed_event
        )
        self.application.event_dispatcher.add_event_listener(
            ConnectionsEvent.EVENT_TYPE_NODE_CONNECTED,
            lambda x: self.nodesTableView.viewport().update(),
        )
        self.application.event_dispatcher.add_event_listener(
            ConnectionsEvent.EVENT_TYPE_NODE_DISCONNECTED,
            lambda x: self.nodesTableView.viewport().update(),
        )
        self.application.event_dispatcher.add_event_listener(
            ConnectionsEvent.EVENT_TYPE_INDEXER_CONNECTED,
            lambda x: self.indexersTableView.viewport().update(),
        )
        self.application.event_dispatcher.add_event_listener(
            ConnectionsEvent.EVENT_TYPE_INDEXER_DISCONNECTED,
            lambda x: self.indexersTableView.viewport().update(),
        )

        ##############################
        # ASYNC METHODS
        ##############################
        # Create a QWorker object
        self.toggle_node_connection_async_qworker = AsyncQWorker(
            self.toggle_node_connection,
            self.mutex,
        )
        self.toggle_node_connection_async_qworker.finished.connect(
            self._on_finished_toggle_node_connection
        )
        self.toggle_indexer_connection_async_qworker = AsyncQWorker(
            self.toggle_indexer_connection,
            self.mutex,
        )
        self.toggle_indexer_connection_async_qworker.finished.connect(
            self._on_finished_toggle_indexer_connection
        )

    def _on_add_node_button_clicked(self):
        """
        Trigger when user click on add node button

        :return:
        """
        NodeAddWindow(self.application, self.mutex, self).exec_()

    def _on_add_indexer_button_clicked(self):
        """
        Trigger when user click on add indexer button

        :return:
        """
        IndexerAddWindow(self.application, self).exec_()

    def _on_currency_event(self, _):
        """
        When a currency event is triggered

        :param _: CurrencyEvent instance
        :return:
        """
        # update model
        self.nodesTableView.model().init_data()
        self.indexersTableView.model().init_data()

        # resize view
        self.nodesTableView.resizeColumnsToContents()
        self.nodesTableView.resizeRowsToContents()
        self.indexersTableView.resizeColumnsToContents()
        self.indexersTableView.resizeRowsToContents()

    def _on_node_list_changed_event(self, _):
        """
        When the node list has changed

        :param _: NodesEvent instance
        :return:
        """
        # update model
        self.nodesTableView.model().init_data()
        # resize view
        self.nodesTableView.resizeColumnsToContents()
        self.nodesTableView.resizeRowsToContents()

    def _on_indexer_list_changed_event(self, _):
        """
        When the indexer list has changed

        :param _: IndexersEvent instance
        :return:
        """
        # update model
        self.indexersTableView.model().init_data()
        # resize view
        self.indexersTableView.resizeColumnsToContents()
        self.indexersTableView.resizeRowsToContents()

    def on_node_context_menu(self, position: QPoint):
        """
        When right button on node table view

        :param position: QPoint instance
        :return:
        """
        index = self.nodesTableView.indexAt(position)
        if index.isValid():
            # get selected node
            row = index.row()
            node = self.nodes_table_model.nodes[row]
            # display popup menu at click position
            NodePopupMenu(self.application, node).exec_(
                self.nodesTableView.mapToGlobal(position)
            )

    def on_indexer_context_menu(self, position: QPoint):
        """
        When right button on indexer table view

        :param position: QPoint instance
        :return:
        """
        index = self.indexersTableView.indexAt(position)
        if index.isValid():
            # get selected node
            row = index.row()
            indexer = self.indexers_table_model.indexers[row]
            # display popup menu at click position
            IndexerPopupMenu(self.application, indexer).exec_(
                self.indexersTableView.mapToGlobal(position)
            )

    def on_node_table_double_click(self, index):
        """
        Triggered when user double-click on a row of node table view
        """
        row = index.row()
        # check index...
        if 0 <= row < len(self.nodes_table_model.nodes):
            self.selected_node = self.nodes_table_model.nodes[row]
            self.toggle_node_connection_async_qworker.start()

    def toggle_node_connection(self):
        """
        Toggle node connection

        :return:
        """
        if self.selected_node is None:
            return
        # current url connected
        current_node_url = self.application.nodes.get_current_url()

        # check connection...
        if (
            self.selected_node.url == current_node_url
            and self.application.connections.node.is_connected()
        ):
            self.application.connections.node.disconnect()
        else:
            if self.selected_node.url != current_node_url:
                self.application.nodes.set_current_url(self.selected_node.url)

            self.application.connections.node.connect(self.selected_node)
            if self.application.connections.node.is_connected():
                node_currency = self.application.currencies.network.get_instance()
                if (
                    self.application.currencies.get_current().genesis_hash is not None
                    and node_currency.genesis_hash
                    != self.application.currencies.get_current().genesis_hash
                ):
                    self.application.connections.node.disconnect()
                    logging.error("Node currency is different! Force Disconnect!")

    def _on_finished_toggle_node_connection(self):
        """
        Triggered when toggle_node_connection is finished

        :return:
        """
        if self.application.connections.node.is_connected():
            self.application.event_dispatcher.dispatch_event(
                ConnectionsEvent(ConnectionsEvent.EVENT_TYPE_NODE_CONNECTED)
            )
        else:
            self.application.event_dispatcher.dispatch_event(
                ConnectionsEvent(ConnectionsEvent.EVENT_TYPE_NODE_DISCONNECTED)
            )

    def on_indexer_table_double_click(self, index):
        """
        Triggered when user double-click on a row of indexer table view
        """
        row = index.row()
        # check index...
        if 0 <= row < len(self.indexers_table_model.indexers):
            self.selected_indexer = self.indexers_table_model.indexers[row]
            self.toggle_indexer_connection_async_qworker.start()

    def toggle_indexer_connection(self):
        """
        Toggle indexer connection

        :return:
        """
        if self.selected_indexer is None:
            return
        # current url connected
        current_indexer_url = self.application.indexers.get_current_url()

        # check connection...
        if (
            self.selected_indexer.url == current_indexer_url
            and self.application.connections.indexer.is_connected()
        ):
            self.application.connections.indexer.disconnect()
        else:
            if self.selected_indexer.url != current_indexer_url:
                self.application.indexers.set_current_url(self.selected_indexer.url)

            self.application.connections.indexer.connect(self.selected_indexer)
            if self.application.connections.indexer.is_connected():
                indexer_genesis_hash = (
                    self.application.indexers.network_get_genesis_hash()
                )
                if (
                    self.application.currencies.get_current().genesis_hash is not None
                    and indexer_genesis_hash
                    != self.application.currencies.get_current().genesis_hash
                ):
                    self.application.connections.indexer.disconnect()
                    logging.error("Indexer currency is different! Force Disconnect!")

    def _on_finished_toggle_indexer_connection(self):
        """
        Triggered when toggle_indexer_connection is finished

        :return:
        """
        if self.application.connections.indexer.is_connected():
            self.application.event_dispatcher.dispatch_event(
                ConnectionsEvent(ConnectionsEvent.EVENT_TYPE_INDEXER_CONNECTED)
            )
        else:
            self.application.event_dispatcher.dispatch_event(
                ConnectionsEvent(ConnectionsEvent.EVENT_TYPE_INDEXER_DISCONNECTED)
            )


if __name__ == "__main__":
    qapp = QApplication(sys.argv)

    application_ = Application(DATA_PATH)

    main_window = QMainWindow()
    main_window.show()

    main_window.setCentralWidget(ServersWidget(application_, QMutex(), main_window))

    sys.exit(qapp.exec_())
