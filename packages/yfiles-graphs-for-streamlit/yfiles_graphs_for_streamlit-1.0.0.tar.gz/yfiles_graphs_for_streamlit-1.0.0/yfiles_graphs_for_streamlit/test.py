from graph_importer import import_
from networkx import florentine_families_graph

g = florentine_families_graph()

things = import_(g)

print(things)