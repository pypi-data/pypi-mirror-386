import pytest
import conftest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.cx5 import Cx5
from infragraph.dgx import Dgx
from infragraph.server import Server
from infragraph.switch import Switch


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize(
    "device",
    [
        Server(),
        Switch(),
        Cx5(),
        Dgx(),
    ],
)
async def test_devices(count, device):
    """From an infragraph device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    # create the graph
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure)

    # validations
    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
