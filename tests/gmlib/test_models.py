import os
import tempfile

import pytest

from gmlib.models import Card, GenerationIndexDefinition, HierachyError, Tree


class TestTree:
    def test_construct(self):
        """综合性树创建测试。"""
        # 构建树，测试相关异常，判断树形状是否符合预期
        tree = Tree()
        with pytest.raises(HierachyError, match="first node must be at depth 0"):
            tree.new_node_at_y(Card(), 1)
        a = tree.new_node_at_y(Card(name="a"), 0)
        b = tree.new_node_as_child(Card(name="b"), a)
        c = tree.new_node_as_parent(Card(name="c"), a)
        d = tree.new_node_at_y(Card(name="d"), 1)
        tree.set_as_child(c, d)
        with pytest.raises(HierachyError, match="child already has a father"):
            tree.set_as_child(d, b)
        e = tree.new_node_at_y(Card(name="e"), 3)
        f = tree.new_node_at_y(Card(name="f"), 3)
        tree.set_as_child(b, e)
        tree.set_as_child(b, f)
        assert tree.str_repr() == "c(a,d);a(b),d;b(e,f);e,f"
        # 删去节点，判断树形状是否符合预期
        tree.remove_node(b)
        assert tree.str_repr() == "c(a,d);a,d;;e,f"
        tree.remove_node(e)
        tree.remove_node(f)
        assert tree.str_repr() == "c(a,d);a,d"

    def test_from_str_repr(self):
        """字符串表示测试。"""
        str_in = "a(b,c,d);b(e,f),c,d(g);e,f(),g()"
        str_out = "a(b,c,d);b(e,f),c,d(g);e,f,g"
        tree = Tree.from_str_repr(str_in)
        assert tree.str_repr() == str_out

    def test_gi(self):
        """世数计算测试。"""
        str_repr = "a(b,c,d);b(e,f),c(),d(g);e(),f(h),g();h()"
        tree = Tree.from_str_repr(str_repr)
        tree.gi_settings.defs.append(
            GenerationIndexDefinition(name="太古世数", offset=-10)
        )
        b = tree.find_node("b")
        h = tree.find_node("h")
        assert tree.compute_gi(b) == 2
        assert tree.compute_gi(b, 1) == -8
        tree.set_gi(h, 17)
        assert tree.compute_gi(b) == 15
        tree.set_gi(h, 6, 1)
        assert tree.compute_gi(b) == 14

    def test_json(self):
        """JSON 导出/读取测试。"""
        str_repr = "a(b,c,d);b(e,f),c(),d(g);e(),f(h),g();h()"
        tree = Tree.from_str_repr(str_repr)
        tree.find_node("c").card.biography = "复杂的 bio"
        with tempfile.TemporaryDirectory() as tempdir:
            fpath = os.path.join(tempdir, "test.json")
            tree.save_json(fpath)
            new_tree = Tree.load_json(fpath)
            assert tree.str_repr() == new_tree.str_repr()
            assert tree.find_node("c").card.biography == "复杂的 bio"
