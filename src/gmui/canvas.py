"""家谱树显示区域。"""

from typing import ClassVar, Optional, Tuple

from gmlib import Card, GenerationIndexDefinition, Tree
from PySide6.QtCore import QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QPen, Qt
from PySide6.QtWidgets import (
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
    QMenu,
)

from gmui.app import AppColors, AppFonts, Debuggable


class Box(QGraphicsItemGroup, Debuggable):
    """代表家谱树节点的方块。

    继承 QObject 方可使用信号。
    """

    # 宽度
    WIDTH: ClassVar[int] = 30
    # 高度
    HEIGHT: ClassVar[int] = 60
    # 普通填充
    NORMAL_BRUSH: ClassVar[QBrush] = QBrush(AppColors.FILL)
    # 鼠标悬浮填充
    HOVER_BRUSH: ClassVar[QBrush] = QBrush(AppColors.HOVER)
    # 普通边框
    NORMAL_PEN: ClassVar[QPen] = QPen(AppColors.LINE, 1)
    # 高亮边框
    HIGHLIGHTED_PEN: ClassVar[QPen] = QPen(AppColors.FOCUS, 3)

    # 对应的节点 ID
    id: int
    # 高亮状态
    highlighted: bool
    # 所在的画布
    canvas: "Canvas"

    def __init__(self, x: float, y: float, id: int, canvas: "Canvas"):
        super().__init__()
        self.id = id
        self.highlighted = False
        self.canvas = canvas
        self._debug_yx = (-1, -1)

        # 矩形边框
        self._rect = QGraphicsRectItem(
            QRectF(-Box.WIDTH / 2, -Box.HEIGHT / 2, Box.WIDTH, Box.HEIGHT)
        )
        self._rect.setBrush(Box.NORMAL_BRUSH)
        self._rect.setPen(Box.NORMAL_PEN)

        # 文字
        self._text = QGraphicsTextItem()
        self._text.setFont(AppFonts.name_font())
        option = self._text.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text.document().setDefaultTextOption(option)

        # 整体设置位置
        self.addToGroup(self._rect)
        self.addToGroup(self._text)
        self.setPos(x, y)

        # 接受鼠标悬停事件
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, _: QGraphicsSceneHoverEvent):
        self._rect.setBrush(Box.HOVER_BRUSH)
        self.canvas.status_tip_requested.emit(self.get_debug_str())

    def hoverLeaveEvent(self, _: QGraphicsSceneHoverEvent):
        self._rect.setBrush(Box.NORMAL_BRUSH)
        self.canvas.status_tip_canceled.emit()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.canvas.highlight_box(self.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.canvas.show_box_menu(self.id, event.screenPos())

    def get_debug_str(self) -> str:
        parts = [f"id = {self.id}"]
        if "yx" in self._debug_info:
            parts.append("yx = {}".format(self._debug_info["yx"]))
        return ", ".join(parts)

    def highlight(self):
        """进入高亮状态。"""
        self.highlighted = True
        self._rect.setPen(Box.HIGHLIGHTED_PEN)

    def dehighlight(self):
        """取消高亮状态。"""
        self.highlighted = False
        self._rect.setPen(Box.NORMAL_PEN)

    def update_info(self, card: Card):
        """更新节点信息。

        用作 `core.Core.card_updated` 之槽。
        """
        # 让每个汉字占一行（暂不考虑汉字外的情况）
        self._text.setHtml("<br>".join(card.name))
        # 更新位置让文字位于方块中央
        bounding_rect = self._text.boundingRect()
        self._text.setPos(-bounding_rect.width() / 2, -bounding_rect.height() / 2)


class Stripe(QGraphicsRectItem):
    """背景条。"""

    # y 索引
    index_y: int
    # 名称，用于菜单
    name: str

    def __init__(
        self,
        index_y: int,
        rect: QRectF,
        color: QColor,
        name: str,
        canvas: "Canvas",
    ):
        super().__init__(rect)
        self.index_y = index_y
        self.name = name
        self.canvas = canvas
        self.setPen(Qt.PenStyle.NoPen)
        self.setZValue(1)
        self.setBrush(QBrush(color))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.canvas.show_stripe_menu(self, event.screenPos())


class Canvas(QGraphicsScene):
    """画布。"""

    # 方块横向间距
    BOX_SPACING: ClassVar[float] = Box.WIDTH * 1.5
    # 层距
    LAYER_SPACING: ClassVar[float] = Box.HEIGHT * 2

    # 设置状态信息信号（文本）
    status_tip_requested = Signal(str)
    # 取消状态信息信号
    status_tip_canceled = Signal()
    # 方块被高亮信号 (ID)
    box_highlighted = Signal(int)
    # 新建节点信号（y）
    new_box_requested = Signal(int)
    # 新建子嗣信号（ID）
    new_child_requested = Signal(int)

    # 节点 ID-方块映射
    boxes: dict[int, Box]
    # 所有连线的列表
    lines: list[QGraphicsLineItem]
    # 所有背景条的列表
    stripes: list[QGraphicsRectItem]
    # 当前高亮的方块
    highlighted_box: Optional[Box]

    def __init__(self):
        super().__init__()
        self.boxes = {}
        self.lines = []
        self.stripes = []
        self.highlighted_box = None

    def _to_canvas_x(self, painting_x: float) -> float:
        canvas_x = painting_x * Canvas.BOX_SPACING
        return canvas_x

    def _to_canvas_y(self, index_y: float) -> float:
        canvas_y = index_y * Canvas.LAYER_SPACING
        return canvas_y

    def _to_canvas_xy(self, painting_x: float, index_y: float) -> Tuple[float, float]:
        """将家谱树坐标转换为画布上的坐标。

        `painting_x` 是使用 `Tree.compute_painting_xs()` 算出的绘图横坐标，
        `index_y` 是节点的纵向索引。
        """
        canvas_x = painting_x * Canvas.BOX_SPACING
        canvas_y = index_y * Canvas.LAYER_SPACING
        return (canvas_x, canvas_y)

    def sync_tree(self, tree: Tree):
        """根据家谱树更新图形。"""

        # 移除所有连线和背景条
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for stripe in self.stripes:
            self.removeItem(stripe)
        self.stripes = []

        # 计算家谱树各节点之绘图坐标
        xs = tree.compute_painting_xs()

        # 删去不再使用的方块
        tree_ids = tree.ids()
        box_ids = self.boxes.keys()
        box_ids_to_delete: list[int] = []
        for id, box in self.boxes.items():
            if id not in tree_ids:
                self.removeItem(box)
                box_ids_to_delete.append(id)
        for id in box_ids_to_delete:
            del self.boxes[id]

        # 增加新方块
        for id in tree_ids:
            if id not in box_ids:
                index_y, index_x = tree.get_node_yx(id)
                x, y = self._to_canvas_xy(xs[id], index_y)
                box = Box(x, y, id, self)
                box.setZValue(3)
                box.update_info(tree.get_node_card(id))
                self.boxes[id] = box
                self.addItem(box)

        # 移动所有现有方块，并绘制连线
        for id, box in self.boxes.items():
            painting_x = xs[id]
            index_y, index_x = tree.get_node_yx(id)
            parent_id = tree.get_node_parent_id(id)
            child_ids = tree.get_node_child_ids(id)
            # 移动方块的位置
            x, y = self._to_canvas_xy(painting_x, index_y)
            box.setPos(x, y)
            box.set_debug_info(yx=(index_y, index_x))
            # 绘制向上的竖线
            if parent_id >= 0:
                x1, y1 = self._to_canvas_xy(painting_x, index_y)
                x2, y2 = self._to_canvas_xy(painting_x, index_y - 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)
            # 绘制向下的竖线
            if child_ids:
                x1, y1 = self._to_canvas_xy(painting_x, index_y)
                x2, y2 = self._to_canvas_xy(painting_x, index_y + 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)
            # 绘制横向的线
            if len(child_ids) > 1:
                lmost_id, rmost_id = child_ids[0], child_ids[-1]
                x1, y1 = self._to_canvas_xy(xs[lmost_id], index_y + 0.5)
                x2, y2 = self._to_canvas_xy(xs[rmost_id], index_y + 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)

        # 创建各层背景条
        min_x, max_x = min(xs.values()), max(xs.values())
        mid_x = (min_x + max_x) / 2
        for index_y in range(-1, tree.nlayers() + 1):
            x, y = self._to_canvas_xy(min_x - 1, index_y - 0.5)
            w, h = self._to_canvas_xy(max_x - min_x + 2, 1)
            color = AppColors.BG2 if index_y % 2 == 0 else AppColors.BG1
            rect = QRectF(x, y, w, h)
            default_gi = tree.compute_layer_gi(index_y)[0]
            default_gi_name = tree.settings.gi.defs[0].name
            stripe_name = self.tr("第 {} 世").format(default_gi)
            if default_gi_name != GenerationIndexDefinition.DEFAULT_NAME:
                stripe_name += self.tr("（{}）").format(default_gi_name)
            stripe = Stripe(index_y, rect, color, stripe_name, self)
            self.stripes.append(stripe)
            self.addItem(stripe)

        # 控制画布大小大于方块所占宽度
        width_required = self._to_canvas_x(max_x - min_x + 2)
        rect = self.sceneRect()
        if rect.width() < width_required:
            topleft = QPointF(self._to_canvas_x(mid_x) - width_required / 2, rect.top())
            bottomright = QPointF(
                self._to_canvas_x(mid_x) + width_required / 2, rect.bottom()
            )
            self.setSceneRect(QRectF(topleft, bottomright))

    def highlight_box(self, id: int):
        """高亮方块，并发射相关信号。"""
        box = self.boxes[id]
        # 高亮该方块
        if self.highlighted_box is not None:
            self.highlighted_box.dehighlight()
        self.highlighted_box = box
        box.highlight()
        # 发送方块被高亮信号，通知其他模块协作
        self.box_highlighted.emit(box.id)

    def dehighlight_boxes(self):
        """取消高亮任何方块。"""
        if self.highlighted_box is not None:
            self.highlighted_box.dehighlight()
        self.highlighted_box = None

    def update_box_info(self, id: int, card: Card):
        """更新指定 ID 方块的信息。"""
        self.boxes[id].update_info(card)

    def show_box_menu(self, id: int, screenPos: QPoint):
        """显示某方块的右键菜单。"""
        menu = QMenu()

        highlight_act = QAction(self.tr("选中"), self)
        highlight_act.triggered.connect(lambda: self.highlight_box(id))
        menu.addAction(highlight_act)

        new_child_act = QAction(self.tr("新建子嗣"), self)
        new_child_act.triggered.connect(lambda: self.new_child_requested.emit(id))
        menu.addAction(new_child_act)

        menu.exec(screenPos)

    def show_stripe_menu(self, stripe: Stripe, screenPos: QPoint):
        """显示背景条右键菜单。"""
        menu = QMenu()
        menu.addSeparator().setText(stripe.name)

        new_node_act = QAction(self.tr("在这一世新建人员"), self)
        new_node_act.triggered.connect(
            lambda: self.new_box_requested.emit(stripe.index_y)
        )
        menu.addAction(new_node_act)

        menu.exec(screenPos)


class CanvasView(QGraphicsView):
    """画布控件，展示完整画布的一部分。"""

    # 对应的画布
    canvas: Canvas

    def __init__(self):
        super().__init__()
        self.canvas = Canvas()
        self.setScene(self.canvas)
