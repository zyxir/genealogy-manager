"""家谱树数据结构。"""

import re
from dataclasses import dataclass, field
from typing import Iterator, Optional, Self, Tuple, Union


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
    bio: str = ""


class Node:
    """一个家谱树节点。"""

    # 节点的唯一数字 ID
    id: int
    # 对应家族成员信息
    card: Card
    # 父节点 ID（负数表示末知）
    parent_id: int
    # 子节点 ID 列表
    child_ids: list[int]

    def __init__(self, id: int, card: Card):
        """新建一个节点。"""
        self.id = id
        self.card = card
        self.parent_id = -1
        self.child_ids = []


class TreeError(Exception):
    """家谱树相关错误。"""


@dataclass
class GenerationIndexDefinition:
    """一个世数定义。"""

    # 该世数的名称
    name: str
    # 相对于标准世数的偏移量
    offset: int


@dataclass
class GenerationIndexSettings:
    """世数配置。"""

    # 第零层节点对应的默认世数
    base: int = 1
    # 世数定义列表
    defs: list[GenerationIndexDefinition] = field(
        default_factory=lambda: [GenerationIndexDefinition(name="世数", offset=0)]
    )


@dataclass
class TreeSettings:
    """家谱树配置。"""

    # 世数配置
    gi = GenerationIndexSettings()


class TreeEdit:
    """家谱树原子编辑。"""

    def reverse(self) -> "TreeEdit": ...


@dataclass
class NewRightmostNode(TreeEdit):
    """在某层的最右边新建节点。该层必须存在。"""

    y: int
    id: int
    card: Card

    def reverse(self) -> "DeleteRightmostNode":
        return DeleteRightmostNode(self.y, self.id, self.card)


@dataclass
class DeleteRightmostNode(TreeEdit):
    """在某层的最右边删除节点。该层必须存在。"""

    y: int
    id: int
    card: Card

    def reverse(self) -> "NewRightmostNode":
        return NewRightmostNode(self.y, self.id, self.card)


@dataclass
class NewLayer(TreeEdit):
    """新建指定 y 的层。可能移动其他层。"""

    y: int

    def reverse(self) -> "DeleteLayer":
        return DeleteLayer(self.y)


@dataclass
class DeleteLayer(TreeEdit):
    """删除指定 y 的层。可能移动其他层。"""

    y: int

    def reverse(self) -> "NewLayer":
        return NewLayer(self.y)


@dataclass
class SetAsChild(TreeEdit):
    """设置父子关系。"""

    parent_id: int
    child_id: int

    def reverse(self) -> "UnsetAsChild":
        return UnsetAsChild(self.parent_id, self.child_id)


@dataclass
class UnsetAsChild(TreeEdit):
    """取消父子关系。"""

    parent_id: int
    child_id: int

    def reverse(self) -> "SetAsChild":
        return SetAsChild(self.parent_id, self.child_id)


@dataclass
class MoveNode(TreeEdit):
    """在同一层内移动节点。可能改变其他节点索引。"""

    id: int
    old_x: int
    new_x: int

    def reverse(self) -> "MoveNode":
        return MoveNode(self.id, self.new_x, self.old_x)


class TreeEditError(Exception):
    """原子编辑相关错误。"""


class Tree:
    """一棵家谱树。"""

    # 上一个被创建节点的 ID
    _last_id: int
    # 所有节点的哈希表，由数字 ID 索引
    _node_dict: dict[int, Node]
    # 由多层节点组成的二维列表，由 i 和 j 索引，用于记录节点左右位置
    _node_layers: list[list[Node]]
    # 各节点在 _node_layers 中的索引，用于快速反查索引
    _node_indices: dict[int, "_NodeIndex"]
    # 配置
    settings: TreeSettings

    # 节点在树中的索引 (y, x)
    @dataclass
    class _NodeIndex:
        y: int
        x: int

    def __init__(self):
        self._last_id = -1
        self._node_dict = {}
        self._node_layers = []
        self._node_indices = {}
        self.settings = TreeSettings()

    def nlayers(self) -> int:
        """获得层数。"""
        return len(self._node_layers)

    def get_node_yx(self, id: int) -> Tuple[int, int]:
        """获取指定 ID 节点的索引。"""
        index = self._node_indices[id]
        return (index.y, index.x)

    def get_node_card(self, id: int) -> Card:
        """获取指定 ID 节点的名片。"""
        return self._node_dict[id].card

    def set_node_card(self, id: int, card: Card):
        """设置指定 ID 节点的名片。"""
        self._node_dict[id].card = card

    def get_node_parent_id(self, id: int) -> int:
        """获取指定 ID 节点的父节点 ID。"""
        return self._node_dict[id].parent_id

    def get_node_child_ids(self, id: int) -> list[int]:
        """获取指定 ID 节点的所有子节点 ID。"""
        return self._node_dict[id].child_ids

    def ids(self) -> Iterator[int]:
        """所有节点 ID 的迭代器。"""
        return iter(self._node_dict.keys())

    def nodes(self) -> Iterator[Node]:
        """所有节点的迭代器。"""
        return iter(self._node_dict.values())

    def obtain_id(self) -> int:
        """获取一个新节点 ID。"""
        self._last_id += 1
        return self._last_id

    def last_id(self) -> int:
        """获取上一个被创建节点的 ID。"""
        return self._last_id

    def _apply_edit(self, edit: TreeEdit):
        """实施单个原子编辑。"""
        match edit:
            # 添加节点到字典和层，并记录索引
            case NewRightmostNode(y, id, card):
                node = Node(id, card)
                self._node_dict[id] = node
                x = len(self._node_layers[y])
                self._node_layers[y].append(node)
                self._node_indices[id] = self._NodeIndex(y=y, x=x)
            # 从字典和层删除节点，并删除索引
            case DeleteRightmostNode(y, id, card):
                node = self._node_layers[y][-1]
                if node.id != id or node.card != card:
                    raise TreeEditError("node info does not match edit info")
                del self._node_dict[id]
                del self._node_layers[y][-1]
                del self._node_indices[id]
            # 修改节点索引后添加层
            case NewLayer(y):
                for layer in self._node_layers[y:]:
                    for node in layer:
                        id = node.id
                        self._node_indices[id].y += 1
                self._node_layers.insert(y, [])
            # 修改节点索引后删除层
            case DeleteLayer(y):
                for layer in self._node_layers[y + 1 :]:
                    for node in layer:
                        id = node.id
                        self._node_indices[id].y -= 1
                del self._node_layers[y]
            # 添加父子关系，适时报错
            case SetAsChild(parent_id, child_id):
                parent = self._node_dict[parent_id]
                child = self._node_dict[child_id]
                if child_id in parent.child_ids or child.parent_id == parent_id:
                    raise TreeEditError("repeatedly setting as child")
                parent_y = self._node_indices[parent_id].y
                child_y = self._node_indices[child_id].y
                if child_y != parent_y + 1:
                    raise TreeEditError("child y is not parent y plus 1")
                self._node_dict[parent_id].child_ids.append(child_id)
                self._node_dict[child_id].parent_id = parent_id
            # 移除父子关系，适时报错
            case UnsetAsChild(parent_id, child_id):
                parent = self._node_dict[parent_id]
                child = self._node_dict[child_id]
                if child_id not in parent.child_ids or child.parent_id != parent_id:
                    raise TreeEditError("no existing parent-child relationship")
                parent_y = self._node_indices[parent_id].y
                child_y = self._node_indices[child_id].y
                if child_y != parent_y + 1:
                    raise TreeEditError("child y is not parent y plus 1")
                self._node_dict[parent_id].child_ids.remove(child_id)
                self._node_dict[child_id].parent_id = -1
            # 改变受牵连的节点的索引，移除+插入该节点，并修改该节点索引
            case MoveNode(id, old_x, new_x):
                if old_x == new_x:
                    return
                index = self._node_indices[id]
                if index.x != old_x:
                    raise TreeEditError(f"old_x ({old_x}) is not actual x ({index.x})")
                if new_x > old_x:
                    for node in self._node_layers[index.y][old_x + 1 : new_x]:
                        self._node_indices[node.id].x -= 1
                else:
                    for node in self._node_layers[index.y][new_x : old_x - 1]:
                        id = node.id
                        self._node_indices[node.id].x += 1
                del self._node_layers[index.y][old_x]
                self._node_layers[index.y].insert(new_x, self._node_dict[id])
                self._node_indices[id].x = new_x

    def apply_edits(self, edits: Union[TreeEdit, list[TreeEdit]]):
        """实施原子编辑。"""
        if isinstance(edits, TreeEdit):
            self._apply_edit(edits)
        else:
            for edit in edits:
                self._apply_edit(edit)

    def compute_new_child_x(self, id: int) -> int:
        """计算为节点插入子节点的合适 x 索引。"""
        index = self._node_indices[id]
        # 向左找到第一个有子节点的节点，称之为 ref
        ref_x = index.x
        while ref_x >= 0 and not self._node_layers[index.y][ref_x].child_ids:
            ref_x = ref_x - 1
        # 若找不到，则新节点应该被插入到 0 号索引
        if ref_x == -1:
            return 0
        # 若找到了，新节点应该被插入到 ref 的最右子节点之右侧
        else:
            ref_child_ids = self._node_layers[index.y][ref_x].child_ids
            ref_child_xs = [self._node_indices[id].x for id in ref_child_ids]
            return max(ref_child_xs) + 1

    def compute_new_parent_x(self, id: int) -> int:
        """计算为节点插入父节点的合适 x 索引。"""
        index = self._node_indices[id]
        # 向左找到第一个有父节点的节点，称之为 ref
        ref_x = index.x
        while ref_x >= 0 and self._node_layers[index.y][ref_x].parent_id < 0:
            ref_x = ref_x - 1
        # 若找不到，则新节点应该被插入到 0 号索引
        if ref_x == -1:
            return 0
        # 若找到了，新节点应该被插入到 ref 的父节点的右侧
        else:
            ref_parent_id = self._node_layers[index.y][ref_x].parent_id
            ref_parent_x = self._node_indices[ref_parent_id].x
            return ref_parent_x + 1

    def str_repr(self) -> str:
        """获得该树的字符串表示，主要用于测试树的形状。

        在字符串表示中，每个节点用其 `card.name` 表示，并在紧随其后的括号中填写
        所有子节点的 `card.name`，用 "," 分隔。若无子节点，可以省去括号（此处的
        输出默认省去）。节点定义之间用 "," 分隔，每一层均用 ";" 结束。节点名字中
        不要包含这些特殊符号。
        """
        str_repr = ""
        for layer in self._node_layers:
            node_strs = []
            for node in layer:
                node_str = node.card.name
                if node.child_ids:
                    child_names = [
                        self._node_dict[child_id].card.name
                        for child_id in node.child_ids
                    ]
                    children_str = ",".join(child_names)
                    node_str = node_str + "({})".format(children_str)
                node_strs.append(node_str)
            str_repr += ",".join(node_strs) + ";"
        return str_repr

    @classmethod
    def from_str_repr(cls, str_repr: str) -> Self:
        """从字符串表示创建树。"""
        tree = cls()
        # 拆成每个节点的字符串表示
        name_layers: list[list[str]] = []
        child_layers: list[list[list[str]]] = []
        layer_strs = str_repr.split(";")
        if layer_strs[-1] == "":
            layer_strs = layer_strs[:-1]
        for layer_str in layer_strs:
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
        for y, name_layer in enumerate(name_layers):
            tree._node_layers.append([])
            for x, name in enumerate(name_layer):
                id = tree.obtain_id()
                node = Node(id=id, card=Card(name=name))
                tree._node_dict[id] = node
                tree._node_layers[-1].append(node)
                tree._node_indices[id] = cls._NodeIndex(y=y, x=x)
                nodes[name] = node
        # 建立父子关系
        for y in range(len(tree._node_layers)):
            layer = tree._node_layers[y]
            for x in range(len(layer)):
                node = layer[x]
                for child_name in child_layers[y][x]:
                    layer[x].child_ids.append(nodes[child_name].id)
                    nodes[child_name].parent_id = layer[x].id
        return tree

    def set_gi(self, id: int, gi: int, gi_index: int = 0):
        """设置节点的某世数，以此更新整个家谱树的基础世数。"""
        node_y = self._node_indices[id].y
        offset = self.settings.gi.defs[gi_index].offset
        self.settings.gi.base = gi - offset - node_y

    def compute_gi(self, id: int) -> list[int]:
        """计算节点的全部世数。"""
        node_y = self._node_indices[id].y
        gi = [self.settings.gi.base + node_y + d.offset for d in self.settings.gi.defs]
        return gi

    def compute_painting_xs(self) -> dict[int, float]:
        """计算所有节点的绘图横坐标。

        坐标排列的原理与 Reingold-Tilford 算法类似，但不是照搬，因为我们的族谱树
        不一定是完整的树，可能有多棵树。
        """

        # 至少要有一层节点才需要排序
        if len(self._node_layers) < 1:
            return {}

        # 属于不同子树的相邻节点间距（以同子树相邻节点间距为单位 1）
        SUBTREE_SPACING = 1.5

        # 所有节点的 x、mod、左右轮廓（left/right contour）存储
        xs: dict[int, float] = dict([(id, 0) for id in self._node_dict.keys()])
        mods: dict[int, float] = dict([(id, 0) for id in self._node_dict.keys()])
        lcons: dict[int, list[float]] = dict(
            [(id, []) for id in self._node_dict.keys()]
        )
        rcons: dict[int, list[float]] = dict(
            [(id, []) for id in self._node_dict.keys()]
        )

        def update_contour(id: int):
            """更新节点的 Reingold-Tilford 轮廓。"""
            head: list[float] = [xs[id]]
            child_ids = self._node_dict[id].child_ids
            if not child_ids:
                lcons[id] = head.copy()
                rcons[id] = head.copy()
            else:
                lsub_lcon = lcons[child_ids[0]]
                lsub_rcon = rcons[child_ids[0]]
                rsub_lcon = lcons[child_ids[-1]]
                rsub_rcon = rcons[child_ids[-1]]
                lcons[id] = head + lsub_lcon + rsub_lcon[len(lsub_lcon) :]
                rcons[id] = head + rsub_rcon + lsub_rcon[len(rsub_rcon) :]

        def compare_and_mod(lid: int, rid: int):
            """比较左右两子树的轮廓，并以此更新右子树的 mod。"""
            lnode, rnode = self._node_dict[lid], self._node_dict[rid]
            spacing = (
                SUBTREE_SPACING
                if lnode.parent_id != rnode.parent_id
                or (lnode.parent_id < 0 and rnode.parent_id < 0)
                else 1
            )
            min_dist = min([rc - lc for lc, rc in zip(rcons[lid], lcons[rid])])
            mods[rid] = spacing - min_dist if min_dist < spacing else 0

            # 更新右节点的左右轮廓以方便后续比较
            for i in range(len(lcons[rid])):
                lcons[rid][i] += mods[rid]
            for i in range(len(rcons[rid])):
                rcons[rid][i] += mods[rid]

        def move():
            """逐层进行重叠判断，设置 mod，并以此修改 x。"""
            # 逐层比较轮廓，并设置 mod。
            for i in reversed(range(len(self._node_layers) - 1)):
                layer = self._node_layers[i]
                # 计算该层所有节点的轮廓
                for node in layer:
                    if node.child_ids:
                        child_modded_xs = [
                            xs[child_id] + mods[child_id] for child_id in node.child_ids
                        ]
                        xs[node.id] = sum(child_modded_xs) / len(child_modded_xs)
                    update_contour(node.id)
                # 两两比较，并更新 mod
                lx, rx = 0, 1
                while rx < len(layer):
                    compare_and_mod(layer[lx].id, layer[rx].id)
                    lx, rx = lx + 1, rx + 1

            # 根据 mod 递归修改所有 x，并清空 mod
            for i, layer in enumerate(self._node_layers):
                for node in layer:
                    xs[node.id] += mods[node.id]
                    for child_id in node.child_ids:
                        mods[child_id] += mods[node.id]
                    mods[node.id] = 0

        def stacking() -> bool:
            """判断当前节点位置布局是否有重叠。"""
            for layer in self._node_layers:
                lx, rx = 0, 1
                while rx < len(layer):
                    lnode, rnode = layer[lx], layer[rx]
                    spacing = (
                        SUBTREE_SPACING
                        if lnode.parent_id != rnode.parent_id
                        or (lnode.parent_id < 0 and rnode.parent_id < 0)
                        else 1
                    )
                    if xs[layer[lx].id] > xs[layer[rx].id] - spacing:
                        return True
                    lx, rx = lx + 1, rx + 1
            return False

        # 为最后一层节点设置初始 x 值与轮廓
        for index_x, node in enumerate(self._node_layers[-1]):
            xs[node.id] = index_x + 0.5
            update_contour(node.id)

        # 进行一次 move。若仍有重叠，则再次 move，直到无重叠为止。
        move()
        while stacking():
            move()
        return xs
