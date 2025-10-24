
from .adapter_base import AdapterBase
from acex.core.models import Node, NodeResponse


class NodeAdapter(AdapterBase):

    def create(self, node: Node): 
        if hasattr(self.plugin, "create"):
            return getattr(self.plugin, "create")(node)

    def get(self, id: str) -> NodeResponse: 
        if hasattr(self.plugin, "get"):
            return getattr(self.plugin, "get")(id)

    def query(self) -> list[Node]: 
        if hasattr(self.plugin, "query"):
            return getattr(self.plugin, "query")()

    def update(self, id: str, node: Node): 
        if hasattr(self.plugin, "update"):
            return getattr(self.plugin, "update")(id, node)

    def delete(self, id: str): 
        if hasattr(self.plugin, "delete"):
            return getattr(self.plugin, "delete")(id)
