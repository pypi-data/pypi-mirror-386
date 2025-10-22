"""
A federated learning training session using FedSaw.

"""

import fedsaw_client
import fedsaw_edge
import fedsaw_server


def main():
    """A Plato federated learning training session using the FedSaw algorithm."""
    client = fedsaw_client.create_client()
    server = fedsaw_server.Server()
    edge_server = fedsaw_server.Server
    edge_client = fedsaw_edge.create_client
    server.run(client, edge_server, edge_client)


if __name__ == "__main__":
    main()
