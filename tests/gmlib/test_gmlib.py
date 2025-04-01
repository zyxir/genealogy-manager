from gmlib import (
    Card,
    GenerationIndexDefinition,
    MoveNode,
    NewLayer,
    NewRightmostNode,
    SetAsChild,
    Tree,
    TreeEdit,
)


class TestTree:
    def test_edits(self):
        """原子编辑测试。"""
        # 构建树，判断树形状是否符合预期
        tree = Tree()
        edits: list[TreeEdit] = [
            NewLayer(0),
            NewLayer(1),
            NewRightmostNode(0, tree.obtain_id(), Card(name="c")),
            NewRightmostNode(1, tree.obtain_id(), Card(name="b")),
            NewLayer(1),
            NewRightmostNode(1, tree.obtain_id(), Card(name="a")),
            NewLayer(3),
            NewRightmostNode(3, tree.obtain_id(), Card(name="f")),
            NewRightmostNode(3, tree.obtain_id(), Card(name="e")),
            MoveNode(tree._last_id, 1, 0),
            NewRightmostNode(1, tree.obtain_id(), Card(name="d")),
        ]
        c, b, a, f, e, d = 0, 1, 2, 3, 4, 5
        edits += [
            SetAsChild(c, a),
            SetAsChild(c, d),
            SetAsChild(a, b),
            SetAsChild(b, e),
            SetAsChild(b, f),
        ]
        tree.apply_edits(edits)
        assert tree.str_repr() == "c(a,d);a(b),d;b(e,f);e,f;"
        # 逆向一部分操作，判断树形状是否符合预期
        reversed_edits = [edit.reverse() for edit in reversed(edits[4:])]
        tree.apply_edits(reversed_edits)
        assert tree.str_repr() == "c;b;"

    def test_str_repr(self):
        """字符串表示测试。"""
        str_in = "a(b,c,d);b(e,f),c,d(g);e,f(),g()"
        str_out = "a(b,c,d);b(e,f),c,d(g);e,f,g;"
        tree = Tree.from_str_repr(str_in)
        assert tree.str_repr() == str_out

    def test_gi(self):
        """世数计算测试。"""
        str_repr = "a(b,c,d);b(e,f),c(),d(g);e(),f(h),g();h()"
        tree = Tree.from_str_repr(str_repr)
        tree.settings.gi.defs.append(
            GenerationIndexDefinition(name="太古世数", offset=-10)
        )
        b, h = 1, 7
        assert tree.compute_gi(b) == [2, -8]
        tree.set_gi(h, 17)
        assert tree.compute_gi(b) == [15, 5]
        tree.set_gi(h, 6, 1)
        assert tree.compute_gi(b) == [14, 4]
