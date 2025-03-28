"""测试树预览功能。"""

from gmlib.models import Tree


if __name__ == "__main__":
    str_repr = ""
    str_repr += "a(b,c),g(h);b(d),c(e,f),h(i),l(m,n),r;"
    str_repr += "d(j,k),e,f,i,s,m(o),n(p,q);j,k(t),o,p,q,u(v);"
    str_repr += "t,v(w);w(x,y);x,y"
    tree = Tree.from_str_repr(str_repr)
    tree.update_xs()
    tree.preview_layout()
