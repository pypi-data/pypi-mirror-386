import os
import s3fs

from ..auth import ROCS_DEFAULT_STORAGE_ENDPOINT
from ..auth.client import get_eocube_sign

access_key = os.environ.get("AWS_ACCESS_KEY_ID")
secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
session_token = os.environ.get("AWS_SESSION_TOKEN")
endpoint = os.environ.get("AWS_S3_ENDPOINT", ROCS_DEFAULT_STORAGE_ENDPOINT)

if not endpoint.startswith("https://") or endpoint.startswith("http://"):
    endpoint = f"https://{endpoint}"

fs = s3fs.S3FileSystem(
    anon=False,
    key=access_key,
    secret=secret_key,
    token=session_token,
    endpoint_url=endpoint,
    asynchronous=False,
)

_sign = get_eocube_sign(fs)


def setup_notebook():
    import nest_asyncio

    nest_asyncio.apply()


def sign_in_place(entry):
    _sign(entry)


def setup_personal_cluster(num_workers=None):
    """Setup a personal cluster for the EOCube.Ro

    :param num_workers: Number of workers to use.
    """
    from dask_gateway import GatewayCluster
    from dask_gateway import Gateway

    gw = Gateway()
    clusters = gw.list_clusters()
    if not clusters:
        gateway = GatewayCluster()
    elif len(clusters) > 1:
        raise Exception("To many clusters")
    else:
        gateway = gw.connect(clusters[0].name)
    if num_workers is not None:
        gateway.scale(num_workers)
    client = gateway.get_client()
    return gateway, client
