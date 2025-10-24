# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from hra_api_client.api.ds_graph_api import DsGraphApi
    from hra_api_client.api.hra_kg_api import HraKgApi
    from hra_api_client.api.hra_pop_api import HraPopApi
    from hra_api_client.api.v1_api import V1Api
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from hra_api_client.api.ds_graph_api import DsGraphApi
from hra_api_client.api.hra_kg_api import HraKgApi
from hra_api_client.api.hra_pop_api import HraPopApi
from hra_api_client.api.v1_api import V1Api

""",
            name=__name__,
            doc=__doc__,
        )
    )
