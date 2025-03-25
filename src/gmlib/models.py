"""家谱树数据结构。"""

import re
from dataclasses import dataclass
from typing import Any, Optional, Self, Tuple


@dataclass
class Card:
    """一个家族成员的名片。"""

    # 姓名
    name: str = "未知"
    # 出生年
    birth_year: Optional[int] = None
    # 死亡年
    death_year: Optional[int] = None
    # 生平介绍
    biography: str = ""
    # 照片 URI
    photo_uri: str = ""


@dataclass
class GenerationIndexDefinition:
    """一个“世数”定义。"""

    # 该世数的名称
    name: str
    # 相对于标准世数的偏移量
    offset: int


class Draw:
    """用于计算节点在图形化显示中的位置。"""

    # 横坐标
    x: float
    # 子树移位
    mod: float
    # 左轮廓
    lcontour: list[float]
    # 右轮廓
    rcontour: list[float]

    def __init__(self):
        self.x = 0
        self.mod = 0
        self.lcontour = []
        self.rcontour = []


class Node:
    """一个家谱树节点。"""

    # 对应家族成员信息
    card: Card
    # 图形化显示所用参数
    draw: Draw
    # 父节点（可选）
    parent: Optional[Self]
    # 子节点列表
    children: list[Self]

    def __init__(self, card: Card):
        """新建一个节点。"""
        self.card = card
        self.draw = Draw()
        self.parent = None
        self.children = []


class HierachyError(Exception):
    """家谱树层级错误。"""

    pass


class Tree:
    """一棵家谱树。"""

    # 由多层节点组成的二维列表，由 i 和 j 索引
    layers: list[list[Node]]

    # 世数设定，由一系列世数定义组成，其中零号为默认世数
    gi_setting: list[GenerationIndexDefinition]

    # 基础世数，即第零层对应的默认世数
    gi_base: int

    def __init__(self):
        self.layers = []
        self.gi_setting = [GenerationIndexDefinition(name="世数", offset=0)]
        self.gi_base = 1
        self.canvas = (0, 0)

    def __iter__(self):
        for layer in self.layers:
            for node in layer:
                yield node

    def find_ij(self, node: Node) -> Tuple[int, int]:
        """获取节点的二维索引 (i, j)。不在树中则报错。"""
        for i, layer in enumerate(self.layers):
            for j, n in enumerate(layer):
                if n is node:
                    return (i, j)
        raise HierachyError("node not in tree")

    def find_j(self, i: int, node: Node) -> int:
        """已知 i，找节点的 j。不在树中则报错。"""
        for j, n in enumerate(self.layers[i]):
            if n is node:
                return j
        raise HierachyError("node not in layer")

    def find_node(self, name: str) -> Node:
        """找到特定名字的节点。"""
        for layer in self.layers:
            for n in layer:
                if n.card.name == name:
                    return n
        raise HierachyError("node not in tree")

    def new_node_at_y(self, card: Card, i: int) -> Node:
        """在固定 i 处新建节点。

        深度可以是 -1 或(最大深度+1)，表示扩展深度。
        """
        new_node = Node(card)
        # 空树只能插入到第 0 层
        if len(self.layers) == 0:
            if i != 0:
                raise HierachyError("first node must be at depth 0")
            self.layers.append([new_node])
        # i 为 -1 表示向上新增层
        elif i == -1:
            self.layers = [[new_node]] + self.layers
        # i 为层数表示向下新增层
        elif i == len(self.layers):
            self.layers = self.layers + [[new_node]]
        # i 不能小于 -1 或大于层数
        elif i < -1 or i > len(self.layers):
            raise HierachyError(f"invalid y {i}, valid range: [-1, {len(self.layers)}]")
        # 其余情况表示向现有行插入
        else:
            self.layers[i].append(new_node)
        return new_node

    def new_node_as_child(self, card: Card, parent: Node) -> Node:
        """插入新节点，作为 `parent` 之子节点。"""
        child = Node(card)
        pi, pj = self.find_ij(parent)
        # 若父节点位于最后一层，子节点添加到新的一层即可
        if pi == len(self.layers) - 1:
            self.layers = self.layers + [[child]]
        # 否则，从父节点开始向左找到第一个有子节点的节点，子节点应添加到它的最右子节点的右边
        else:
            j = pj
            while j >= 0 and len(self.layers[pi][j].children) == 0:
                j = j - 1
            if j < 0:
                cj = 0
            else:
                ref_child = self.layers[pi][j].children[-1]
                ref_cj = self.find_j(pi + 1, ref_child)
                cj = ref_cj + 1
            self.layers[pi + 1].insert(cj, child)
        # 设置父子关系
        parent.children.append(child)
        child.parent = parent
        return child

    def new_node_as_parent(self, card: Card, child: Node) -> Node:
        """插入新节点，作为 `child` 之父节点。"""
        parent = Node(card)
        ci, cj = self.find_ij(child)
        # 若子节点位于第一层，父节点添加到新的一层即可
        if ci == 0:
            self.layers = [[parent]] + self.layers
        # 否则，从子节点向左找到第一个有父节点的节点，父节点应添加到它的右边
        else:
            j = cj
            while j >= 0 and self.layers[ci][j].parent is None:
                j = j - 1
            if j < 0:
                pj = 0
            else:
                ref_parent = self.layers[ci][j].parent
                if ref_parent is None:
                    pj = 0
                else:
                    ref_pj = self.find_j(ci - 1, ref_parent)
                    pj = ref_pj + 1
            self.layers[ci - 1].insert(pj, parent)
        # 设置父子关系
        parent.children.append(child)
        child.parent = parent
        return parent

    def set_as_child(self, parent: Node, child: Node):
        """设置父子关系。"""
        # 若子节点已有父亲，报错
        if child.parent is not None:
            raise HierachyError("child already has a father")
        # 若层数关系不对，报错
        pi, pj = self.find_ij(parent)
        ci, _ = self.find_ij(child)
        if pi + 1 != ci:
            raise HierachyError("parent and child not in adjacent layers")
        # 从父节点开始向左找到第一个有子节点的节点，子节点应被移动到它的最右子节点的右边
        self.layers[ci].remove(child)
        j = pj
        while j >= 0 and len(self.layers[pi][j].children) == 0:
            j = j - 1
        if j < 0:
            cj = 0
        else:
            ref_child = self.layers[pi][j].children[-1]
            ref_cj = self.find_j(pi + 1, ref_child)
            cj = ref_cj + 1
        self.layers[pi + 1].insert(cj, child)
        # 设置父子关系
        parent.children.append(child)
        child.parent = parent

    def remove_from_children(self, parent: Node, child: Node):
        """移除父子关系。"""
        # 若没有父子关系，报错
        if child.parent is not parent:
            raise HierachyError("no existing parent-child relationship")
        # 移除关系，但默认不改变子节点位置
        parent.children.remove(child)
        child.parent = None

    def remove_node(self, node: Node):
        """移除节点，及所有相关关系。"""
        i, _ = self.find_ij(node)
        if node.parent is not None:
            node.parent.children.remove(node)
        for child in node.children:
            child.parent = None
        self.layers[i].remove(node)
        # 如果节点在第一层/最后一层，还要移除所有空层
        if i == 0:
            while len(self.layers[0]) == 0:
                self.layers = self.layers[1:]
        elif i == len(self.layers) - 1:
            while len(self.layers[-1]) == 0:
                self.layers = self.layers[:-1]
        del node

    def str_repr(self) -> str:
        """获得该树的字符串表示，主要用于测试树的形状。

        在字符串表示中，每个节点用其 `card.name` 表示，并在紧随其后的括号中填写
        所有子节点的 `card.name`，用 "," 分隔。若无子节点，可以省去括号（此处的
        输出默认省去）。节点定义之间用 "," 分隔，并使用 ";" 表示进入下一行。节点
        名字中不要包含这些特殊符号。
        """
        layer_strs = []
        for layer in self.layers:
            node_strs = []
            for node in layer:
                if len(node.children) != 0:
                    child_names = [child.card.name for child in node.children]
                    children_str = ",".join(child_names)
                    node_strs.append(f"{node.card.name}({children_str})")
                else:
                    node_strs.append(node.card.name)
            layer_strs.append(",".join(node_strs))
        return ";".join(layer_strs)

    @classmethod
    def from_str_repr(cls, str_repr: str) -> Self:
        """从字符串表示创建树。"""
        tree = cls()
        # 拆成每个节点的字符串表示
        name_layers: list[list[str]] = []
        child_layers: list[list[list[str]]] = []
        for layer_str in str_repr.split(";"):
            name_layer: list[str] = []
            child_layer: list[list[str]] = []
            pattern = r"""
              (?P<name>[^\(\),]+)
              (?:
              \(
                (?P<children>[^\)]*)
              \)
              )?
              (?:,|$)
            """
            for match in re.finditer(pattern, layer_str, re.VERBOSE):
                name_layer.append(match.group("name"))
                if match.group("children"):
                    child_layer.append(match.group("children").split(","))
                else:
                    child_layer.append([])
            name_layers.append(name_layer)
            child_layers.append(child_layer)
        # 注册所有节点，并建立名字-节点字典
        nodes: dict[str, Node] = {}
        for i, name_layer in enumerate(name_layers):
            for name in name_layer:
                node = tree.new_node_at_y(Card(name=name), i)
                nodes[name] = node
        # 建立父子关系
        for i in range(len(tree.layers)):
            layer = tree.layers[i]
            for j in range(len(layer)):
                node = layer[j]
                for child_name in child_layers[i][j]:
                    layer[j].children.append(nodes[child_name])
                    nodes[child_name].parent = layer[j]
        return tree

    def set_gi(self, node: Node, gi: int, gi_index: int = 0):
        """设置节点的某世数，以此更新整个家谱树的基础世数。"""
        node_i, _ = self.find_ij(node)
        offset = self.gi_setting[gi_index].offset
        self.gi_base = gi - offset - node_i

    def compute_gi(self, node: Node, gi_index: int = 0):
        """计算节点的某世数。"""
        node_i, _ = self.find_ij(node)
        offset = self.gi_setting[gi_index].offset
        return self.gi_base + node_i + offset

    def _update_contour(self, node: Node):
        """更新节点的 Reingold-Tilford 轮廓。

        会复用子节点的计算结果。
        """
        head: list[float] = [node.draw.x]
        if len(node.children) == 0:
            node.draw.lcontour = head.copy()
            node.draw.rcontour = head.copy()
        else:
            lsub_lcon = node.children[0].draw.lcontour
            lsub_rcon = node.children[0].draw.rcontour
            rsub_lcon = node.children[-1].draw.lcontour
            rsub_rcon = node.children[-1].draw.rcontour
            node.draw.lcontour = head + lsub_lcon + rsub_lcon[len(lsub_lcon) :]
            node.draw.rcontour = head + rsub_rcon + lsub_rcon[len(rsub_rcon) :]

    def _compare_and_move(self, lnode: Node, rnode: Node):
        """比较左右两子树的轮廓，并以此计算右子树位移量。"""
        # 根据最小距离计算位移量
        min_dist = min(
            [rc - lc for lc, rc in zip(lnode.draw.rcontour, rnode.draw.lcontour)]
        )
        rnode.draw.mod = 1 - min_dist if min_dist < 1 else 0
        # 更新右节点的 contour 以方便后续比较
        for i in range(len(rnode.draw.lcontour)):
            rnode.draw.lcontour[i] = rnode.draw.lcontour[i] + rnode.draw.mod
        for i in range(len(rnode.draw.rcontour)):
            rnode.draw.rcontour[i] = rnode.draw.rcontour[i] + rnode.draw.mod

    def update_xs(self):
        """更新所有节点的绘图坐标。

        坐标排列的原理与 Reingold-Tilford 算法类似，但不是照搬，因为我们的族谱树
        不一定是完整的树，可能有多棵树。
        """
        # 至少要有一层节点才需要排序
        if len(self.layers) < 1:
            return

        # 为最后一层节点设置初始 x 值与轮廓
        for j, node in enumerate(self.layers[-1]):
            node.draw.x = j + 0.5
            self._update_contour(node)

        def move():
            """逐层进行重叠判断，设置 mod，并以此修改 x。"""
            # 逐层比较轮廓，并设置 mod。
            for i in reversed(range(len(self.layers) - 1)):
                layer = self.layers[i]
                for node in layer:
                    if len(node.children) > 0:
                        child_xs = [
                            child.draw.x + child.draw.mod for child in node.children
                        ]
                        node.draw.x = sum(child_xs) / len(child_xs)
                    self._update_contour(node)
                lj, rj = 0, 1
                while rj < len(layer):
                    self._compare_and_move(layer[lj], layer[rj])
                    lj, rj = lj + 1, rj + 1

            # 根据 mod 递归修改所有 x，并清空 mod
            for i, layer in enumerate(self.layers):
                for node in layer:
                    node.draw.x = node.draw.x + node.draw.mod
                    for child in node.children:
                        child.draw.mod = child.draw.mod + node.draw.mod
                    node.draw.mod = 0

        def stacking() -> bool:
            for layer in self.layers:
                lj, rj = 0, 1
                while rj < len(layer):
                    if layer[lj].draw.x > layer[rj].draw.x - 1:
                        return True
                    lj, rj = lj + 1, rj + 1
            return False

        # 进行一次 move。若仍有重叠，则再次 move，直到无重叠为止。
        move()
        while stacking():
            move()


    def preview_layout(self):
        """用 Matplotlib 预览家谱树布局。"""
        import matplotlib.pyplot as plt
        import numpy as np

        plt.rcParams["font.family"] = "Source Han Sans CN"
        _, ax = plt.subplots()
        NODE_SPACING = 10
        LAYER_HEIGHT = 10

        # 计算显示范围
        x_min = (min([node.draw.x for node in self]) - 2) * NODE_SPACING
        x_max = (max([node.draw.x for node in self]) + 1) * NODE_SPACING
        plt.xlim(x_min, x_max)
        plt.ylim(-len(self.layers) * LAYER_HEIGHT, 0)

        # 绘制所有世数
        gi_props: dict[str, Any] = {
            "transform": ax.transData,
            "fontsize": 14,
            "verticalalignment": "center",
            "horizontalalignment": "center",
        }
        for i in range(len(self.layers)):
            x = x_min + NODE_SPACING
            y = -LAYER_HEIGHT * (i + 0.5)
            gi = i + self.gi_base
            plt.text(x, y, str(gi), **gi_props)

        # 绘制所有边框与文字
        text_props: dict[str, Any] = {
            "transform": ax.transData,
            "fontsize": 14,
            "verticalalignment": "center",
            "horizontalalignment": "center",
            "bbox": {
                "boxstyle": "square",
                "facecolor": "white",
                "edgecolor": "black",
            },
            "zorder": 1,
        }
        for i, layer in enumerate(self.layers):
            y = -LAYER_HEIGHT * (i + 0.5)
            for node in layer:
                x = node.draw.x * NODE_SPACING
                txt = node.card.name
                plt.text(x, y, txt, **text_props)

        # 绘制所有连线
        line_props: dict[str, Any] = {
            "color": "C0",
            "zorder": 0,
        }
        for i, layer in enumerate(self.layers):
            if i == len(self.layers) - 1:
                continue
            for node in layer:
                if len(node.children) > 0:
                    child_xs = np.array([child.draw.x for child in node.children])
                    plt.vlines(
                        node.draw.x * NODE_SPACING,
                        -LAYER_HEIGHT * (i + 0.5),
                        -LAYER_HEIGHT * (i + 1),
                        **line_props,
                    )
                    plt.hlines(
                        -LAYER_HEIGHT * (i + 1),
                        child_xs[0] * NODE_SPACING,
                        child_xs[-1] * NODE_SPACING,
                        **line_props,
                    )
                    plt.vlines(
                        child_xs * NODE_SPACING,
                        -LAYER_HEIGHT * (i + 1),
                        -LAYER_HEIGHT * (i + 1.5),
                        **line_props,
                    )

        # 其它设置
        plt.axis("off")
        plt.title("家谱树预览")
        plt.show()
