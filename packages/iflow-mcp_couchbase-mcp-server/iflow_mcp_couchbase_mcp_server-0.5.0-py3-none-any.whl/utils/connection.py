import logging
import os
from datetime import timedelta

from couchbase.auth import CertificateAuthenticator, PasswordAuthenticator
from couchbase.cluster import Bucket, Cluster
from couchbase.options import ClusterOptions

from .constants import MCP_SERVER_NAME

logger = logging.getLogger(f"{MCP_SERVER_NAME}.utils.connection")


def connect_to_couchbase_cluster(
    connection_string: str,
    username: str,
    password: str,
    ca_cert_path: str | None = None,
    client_cert_path: str | None = None,
    client_key_path: str | None = None,
) -> Cluster:
    """Connect to Couchbase cluster and return the cluster object if successful.
    The connection can be established using the client certificate and key or the username and password. Optionally, the CA root certificate path can also be provided.
    Either of the path to the client certificate and key or the username and password should be provided.
    If the client certificate and key are provided, the username and password are not used.
    If both the client certificate and key and the username and password are provided, the client certificate is used for authentication.
    If the connection fails, it will raise an exception.
    """

    try:
        logger.info("Connecting to Couchbase cluster...")
        if client_cert_path and client_key_path:
            logger.info("Connecting to Couchbase cluster with client certificate...")
            if not os.path.exists(client_cert_path) or not os.path.exists(
                client_key_path
            ):
                raise FileNotFoundError(
                    f"Client certificate files not found at {os.path.basename(client_cert_path)} or {os.path.basename(client_key_path)}."
                )

            auth = CertificateAuthenticator(
                cert_path=client_cert_path,
                key_path=client_key_path,
                trust_store_path=ca_cert_path,
            )
        else:
            logger.info("Connecting to Couchbase cluster with password...")
            auth = PasswordAuthenticator(username, password, cert_path=ca_cert_path)
        options = ClusterOptions(auth)
        options.apply_profile("wan_development")

        cluster = Cluster(connection_string, options)  # type: ignore
        cluster.wait_until_ready(timedelta(seconds=5))

        logger.info("Successfully connected to Couchbase cluster")
        return cluster
    except Exception as e:
        logger.error(f"Failed to connect to Couchbase: {e}")
        raise


def connect_to_bucket(cluster: Cluster, bucket_name: str) -> Bucket:
    """Connect to a bucket and return the bucket object if successful.
    If the operation fails, it will raise an exception.
    """
    try:
        bucket = cluster.bucket(bucket_name)
        return bucket
    except Exception as e:
        logger.error(f"Failed to connect to bucket: {e}")
        raise
