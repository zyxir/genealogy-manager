"""Qt 应用程序定义。"""

from typing import ClassVar

from gmlib import Card, Tree
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, Qt
from PySide6.QtWidgets import QMainWindow

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

    # 画布
    canvas: Canvas
    # 信息侧栏
    info_dock: InfoDock

    def __init__(self):
        super().__init__()
        self._tree = Tree()
        self._displayed_id = -1

        # 菜单栏
        self._setup_menu()

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
        self.canvas.box_highlighted.connect(self._canvas_box_highlighted_slot)
        self.info_dock.card_edited.connect(self._info_dock_card_edited_slot)
        self.info_dock.card_closed.connect(self._info_dock_card_closed_slot)

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
        import random
        import lorem
        str_repr = ""
        str_repr += "张甲(张一,张二),张乙(张三);"
        str_repr += "张一(张子),张二(张丑,张寅),张三(张卯),张四(张巳,张午),张五;"
        str_repr += (
            "张子(张泰,张华),张丑,张寅,张卯,张辰,张巳,张午(张嵩),张未(张恒,张衡);"
        )
        str_repr += "张泰,张华(张小),张嵩,张恒,张衡;"
        str_repr += "张小;"
        self._tree = Tree.from_str_repr(str_repr)
        for id in self._tree.ids():
            card = self._tree.get_node_card(id)
            if random.random() < 0.7:
                card.birth_year = random.randint(1000, 2000)
            if random.random() < 0.7:
                card.death_year = random.randint(1050, 2050)
            card.bio = lorem.paragraph()
            self._tree.set_node_card(id, card)
        self.canvas.sync_tree(self._tree)
        self.info_dock.close_card()

    def _canvas_box_highlighted_slot(self, id: int):
        """当画布高亮某方块后，记录其 ID，并在侧栏展示它。"""
        # 记录 ID
        self._displayed_id = id
        # 在侧栏展示它
        card = self._tree.get_node_card(id)
        self.info_dock.display_card(card)

    def _info_dock_card_edited_slot(self, card: Card):
        """当信息侧栏更新了名片后，更新家谱树中的信息与画布中的展示信息。"""
        # 更新家谱树
        self._tree.set_node_card(self._displayed_id, card)
        # 更新画布
        self.canvas.update_box_info(self._displayed_id, card)

    def _info_dock_card_closed_slot(self):
        """当信息侧栏关闭名片时，做相应操作。"""
        # 清空记录的 ID
        self._displayed_id = -1
        # 取消画布中的方块高亮
        self.canvas.dehighlight_boxes()
