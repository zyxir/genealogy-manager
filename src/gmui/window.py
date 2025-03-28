"""Qt 应用程序定义。"""

from typing import ClassVar

from gmlib.models import Tree
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
)

from gmui.about_dialog import AboutDialog
from gmui.canvas import Canvas
from gmui.config import get_recent_files
from gmui.error import error_dialog
from gmui.info_dock import InfoDock


class Window(QMainWindow):
    """家谱通主窗口。"""

    # 默认窗口大小
    DEFAULT_SIZE: ClassVar[QSize] = QSize(1000, 618)

    # 家谱树
    tree: Tree

    def __init__(self):
        super().__init__()

        str_repr = ""
        str_repr += "a(b,c),g(h);b(d),c(e,f),h(i),l(m,n),r;"
        str_repr += "d(j,k),e,f,i,s,m(o),n(p,q);j,k(t),o,p,q,u(v);"
        str_repr += "t,v(w);w(x,y);x,y"
        self.tree = Tree.from_str_repr(str_repr)

        self._setup_menu()

        self.canvas = Canvas()
        self.canvas.sync_tree(self.tree)
        self.setCentralWidget(self.canvas)

        self.info_panel = InfoDock()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.info_panel)

        # 连接信号
        self.canvas.view_node.connect(self.info_panel.view_node)

        self.resize(self.DEFAULT_SIZE)
        self.move(self.screen().geometry().center() - self.frameGeometry().center())
        self.setWindowTitle(self.tr("家谱通"))

    def open_file(self):
        """打开家谱文件。"""
        fpath, _ = QFileDialog.getOpenFileName(
            self, self.tr("选择家谱文件"), self.tr("JSON files (*.json)")
        )
        try:
            self.tree = Tree.load_json(fpath)
        except Exception as e:
            error_dialog("无法打开文件", str(e))

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
        open_act.triggered.connect(self.open_file)
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

        # 关于
        about_menu = self.menuBar().addMenu(self.tr("关于 (&A)"))

        # 关于-关于家谱通
        about_act = QAction(
            QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout), self.tr("关于家谱通"), self
        )
        about_act.triggered.connect(lambda: AboutDialog().exec())
        about_menu.addAction(about_act)
