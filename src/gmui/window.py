"""Qt 应用程序定义。"""

import logging
from collections import deque
from typing import ClassVar

from gmlib import Card, Tree, TreeEdit
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, Qt
from PySide6.QtWidgets import QMainWindow, QStatusBar

from gmui.about_dialog import AboutDialog
from gmui.canvas import Canvas, CanvasView
from gmui.config import get_recent_files
from gmui.info_dock import InfoDock


class Window(QMainWindow):
    """家谱通主窗口。"""

    # 默认窗口大小，也是最小大小
    DEFAULT_SIZE: ClassVar[QSize] = QSize(1000, 618)

    # 家谱树
    _tree: Tree
    # 当前展示的节点 ID，负数表示无
    _displayed_id: int
    # 撤消栈
    _undo_stack: deque[list[TreeEdit]]
    # 重做栈
    _redo_stack: deque[list[TreeEdit]]

    # Debug 模式
    _debug: bool

    # 画布
    canvas: Canvas
    # 信息侧栏
    info_dock: InfoDock

    def __init__(self, debug=False):
        super().__init__()
        self._tree = Tree()
        self._displayed_id = -1
        self._undo_stack = deque()
        self._redo_stack = deque()
        self._debug = debug

        # 菜单栏、工具栏、状态条
        self._setup_menu()
        _ = self.statusBar()

        # 主控件：画布
        canvas_view = CanvasView()
        self.canvas = canvas_view.canvas
        self.setCentralWidget(canvas_view)

        # 信息侧栏
        self.info_dock = InfoDock()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock)

        # 窗口大小、位置与标题
        self.resize(self.DEFAULT_SIZE)
        self.setMinimumSize(self.DEFAULT_SIZE)
        self.move(self.screen().geometry().center() - self.frameGeometry().center())
        self.setWindowTitle(self.tr("家谱通"))

        # 连接信号
        self.canvas.status_tip_requested.connect(
            lambda tip: self.statusBar().showMessage(tip)
        )
        self.canvas.status_tip_canceled.connect(lambda: self.statusBar().clearMessage())
        self.canvas.box_highlighted.connect(self._canvas_box_highlighted_slot)
        self.canvas.new_box_requested.connect(self._canvas_new_box_requested_slot)
        self.canvas.new_child_requested.connect(self._canvas_new_child_requested_slot)
        self.info_dock.card_edited.connect(self._info_dock_card_edited_slot)
        self.info_dock.card_closed.connect(self._info_dock_card_closed_slot)
        self.info_dock.card_deleted.connect(self._info_dock_card_deleted_slot)

    def _setup_menu(self):
        """创建与配置菜单。"""
        # 文件
        file_menu = self.menuBar().addMenu(self.tr("文件 (&F)"))

        # 文件-新建
        new_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew), self.tr("新建"), self
        )
        new_act.setShortcuts(QKeySequence.StandardKey.New)
        file_menu.addAction(new_act)

        # 文件-打开
        open_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen), self.tr("打开"), self
        )
        open_act.setShortcuts(QKeySequence.StandardKey.Open)
        file_menu.addAction(open_act)

        # 文件-保存
        save_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave), self.tr("保存"), self
        )
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(save_act)

        # 文件-关闭
        close_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.WindowClose), self.tr("关闭"), self
        )
        file_menu.addAction(close_act)

        # 文件-最近文件
        file_menu.addSeparator().setText(self.tr("最近文件"))
        recent_files = get_recent_files()
        if len(recent_files) > 0:
            for recent_file in recent_files:
                act = QAction(recent_file, self)
                file_menu.addAction(act)
        else:
            act = QAction(self.tr("(无)"), self)
            act.setEnabled(False)
            file_menu.addAction(act)

        # Debug
        debug_menu = self.menuBar().addMenu(self.tr("Debug (&D)"))

        # Debug-加载示例家谱
        load_demo_tree_act = QAction(self.tr("加载示例家谱树"), self)
        load_demo_tree_act.triggered.connect(self.load_demo_tree)
        debug_menu.addAction(load_demo_tree_act)

        # 关于
        about_menu = self.menuBar().addMenu(self.tr("关于 (&A)"))

        # 关于-关于家谱通
        about_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout), self.tr("关于家谱通"), self
        )
        about_act.triggered.connect(lambda: AboutDialog().exec())
        about_menu.addAction(about_act)

    def load_demo_tree(self):
        """加载示例树。"""
        self._tree = Tree.demo_tree()
        self.canvas.sync_tree(self._tree)
        self.info_dock.close_card()

    def _do(self, edits: list[TreeEdit]):
        """执行操作，并将它们记录到撤消栈。"""
        logging.debug("doing edits: %s", edits)
        self._tree.apply_edits(edits)
        self._undo_stack.append(edits)

    def _update_widgets(self):
        """每次撤消/重做后可能需要的更新控件显示。"""
        self.canvas.sync_tree(self._tree)
        if self.info_dock.widget == self.info_dock.card_display:
            card = self._tree.get_node_card(self._displayed_id)
            self.info_dock.display_card(card)

    def _undo(self):
        """撤消。"""
        edits = self._undo_stack.pop()
        reversed_edits = [edit.reverse() for edit in reversed(edits)]
        self._tree.apply_edits(reversed_edits)
        self._redo_stack.append(edits)
        self._update_widgets()

    def _redo(self):
        """重做。"""
        edits = self._redo_stack.pop()
        self._tree.apply_edits(edits)
        self._undo_stack.append(edits)
        self._update_widgets()

    def _canvas_box_highlighted_slot(self, id: int):
        """当画布高亮某方块后，记录其 ID，并在侧栏展示它。"""
        # 记录 ID
        self._displayed_id = id
        # 在侧栏展示它
        card = self._tree.get_node_card(id)
        self.info_dock.display_card(card)

    def _canvas_new_box_requested_slot(self, index_y: int):
        """当画布要求在某层新建节点时，新建节点，并刷新画布。"""
        # 新建节点
        logging.debug("new node requested at y=%d", index_y)
        edits = self._tree.edits_for_new_node(index_y, Card())
        self._do(edits)
        id = self._tree.last_id()
        # 刷新画布
        self.canvas.sync_tree(self._tree)
        # 高亮新建的方块
        self.canvas.highlight_box(id)
        # 在侧栏编辑它
        self.info_dock.edit_card()

    def _canvas_new_child_requested_slot(self, id: int):
        """当画布要求为某节点新建子嗣时，做相应操作。"""
        # 新建子节点
        logging.debug("new child node for id=%d requested", id)
        edits = self._tree.edits_for_new_child(id, Card())
        self._do(edits)
        id = self._tree.last_id()
        # 刷新画布
        self.canvas.sync_tree(self._tree)
        # 高亮新建的方块
        self.canvas.highlight_box(id)
        # 在侧栏编辑它
        self.info_dock.edit_card()

    def _info_dock_card_edited_slot(self, card: Card):
        """当信息侧栏更新了名片后，更新家谱树中的信息与画布中的展示信息。"""
        # 更新家谱树
        edits = self._tree.edits_for_set_card(self._displayed_id, card)
        self._do(edits)
        # 更新画布
        self.canvas.update_box_info(self._displayed_id, card)

    def _info_dock_card_closed_slot(self):
        """当信息侧栏关闭名片时，做相应操作。"""
        # 清空记录的 ID
        self._displayed_id = -1
        # 取消画布中的方块高亮
        self.canvas.dehighlight_boxes()

    def _info_dock_card_deleted_slot(self):
        """当在侧栏中删除节点时，做相应操作。"""
        # 清除画布高亮
        self.canvas.dehighlight_boxes()
        # 除除节点
        edits = self._tree.edits_for_delete_node(self._displayed_id)
        self._do(edits)
        # 更新画布
        self.canvas.sync_tree(self._tree)
        # 清空记录的 ID
        self._displayed_id = -1
