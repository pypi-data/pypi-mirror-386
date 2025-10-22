"""
A federated learning training session using Tempo.
"""

import tempo_client
import tempo_edge
import tempo_server


def main():
    """A Plato federated learning training session using the Tempo algorithm."""
    server = tempo_server.Server()
    client = tempo_client.create_client()
    edge_server = tempo_server.Server
    edge_client = tempo_edge.create_client
    server.run(client, edge_server, edge_client)


if __name__ == "__main__":
    main()
