import subprocess, tempfile, os
from graphviz import Digraph, Graph


formats=["svg","ps","eps","xdot","json","cmapx","png","pdf","jpg","gif","webp"]
digraph="digraph{a->b}"
def ok(fmt):
    with tempfile.NamedTemporaryFile(delete=False) as f: out=f.name+"."+fmt
    r=subprocess.run(["dot",f"-T{fmt}","-o",out],input=digraph,text=True,capture_output=True)
    return (r.returncode==0, r.stderr.strip(), out)
for fmt in formats:
    success, err, path = ok(fmt)
    print(f"{fmt:5s}: {'OK' if success else 'UNSUPPORTED'}", ("" if success else f"({err[:120]})"))

d=tempfile.mkdtemp(prefix="gv_")

g=Digraph("test", graph_attr={"rankdir":"LR"})
g.edge("A","B"); g.node("C",shape="box")
p1=g.render(filename="digraph", directory=d, format="svg", cleanup=True)

h=Graph("undirected"); h.edges([("A","B"),("A","C")])
p2=h.render(filename="graph", directory=d, format="svg", cleanup=True)

print(p1); print(p2)

engines=["dot","neato","sfdp","fdp","twopi","circo"]
for e in engines:
    try:
        g=Graph("G", engine=e)
        g.edges([("a","b"),("b","c"),("c","d"),("d","a")])
        data=g.pipe(format="svg")
        print(e, "OK" if data else "EMPTY")
    except Exception as ex:
        print(e,"ERROR",type(ex).__name__,str(ex)[:200])

