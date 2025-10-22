"""
A customized client for federated unlearning.

Federated unlearning allows clients to proactively erase their data from a trained model. The model
will be retrained from scratch during the unlearning process.

If the AdaHessian optimizer is used, it will reflect what the following paper proposed:

Liu et al., "The Right to be Forgotten in Federated Learning: An Efficient Realization with Rapid
Retraining," in Proc. INFOCOM, 2022.

Reference: https://arxiv.org/abs/2203.07320
"""

import logging

import unlearning_iid
from lib_mia import mia_client

from plato.clients.strategies import DefaultLifecycleStrategy
from plato.config import Config


class FedUnlearningLifecycleStrategy(DefaultLifecycleStrategy):
    """Lifecycle strategy tracking rollback rounds for unlearning."""

    def process_server_response(self, context, server_response):
        super().process_server_response(context, server_response)

        owner = context.owner
        if owner is None:
            return

        client_id = context.client_id
        previous_round = owner.previous_round.get(client_id, 0)
        client_pool = Config().clients.clients_requesting_deletion

        if client_id in client_pool and context.current_round <= previous_round:
            if client_id not in owner.unlearning_clients:
                owner.unlearning_clients.append(client_id)

        owner.previous_round[client_id] = context.current_round

    def configure(self, context):
        super().configure(context)

        owner = context.owner
        if owner is None:
            return

        owner.sampler = context.sampler
        owner.testset_sampler = getattr(context, "testset_sampler", None)

        if owner.client_id in owner.unlearning_clients:
            logging.info(
                "[%s] Unlearning sampler deployed: %s%% of the samples were deleted.",
                owner,
                Config().clients.deleted_data_ratio * 100,
            )

            sampler = unlearning_iid.Sampler(
                context.datasource, context.client_id, testing=False
            )
            context.sampler = sampler
            owner.sampler = sampler


def create_client(
    *,
    model=None,
    datasource=None,
    algorithm=None,
    trainer=None,
    callbacks=None,
):
    """Build a federated unlearning client with rollback tracking."""
    client = mia_client.create_client(
        model=model,
        datasource=datasource,
        algorithm=algorithm,
        trainer=trainer,
        callbacks=callbacks,
    )

    client.previous_round = {}
    client.unlearning_clients = []

    client._configure_composable(
        lifecycle_strategy=FedUnlearningLifecycleStrategy(),
        payload_strategy=client.payload_strategy,
        training_strategy=client.training_strategy,
        reporting_strategy=client.reporting_strategy,
        communication_strategy=client.communication_strategy,
    )

    return client


# Maintain compatibility for imports expecting a Client callable/class.
Client = create_client
