"""
A customized client for Knot, a clustered aggregation mechanism designed for
federated unlearning.
"""

import logging

import unlearning_iid

from plato.clients import simple
from plato.clients.strategies import DefaultLifecycleStrategy
from plato.config import Config


class KnotLifecycleStrategy(DefaultLifecycleStrategy):
    """Lifecycle strategy injecting Knot's unlearning behaviour."""

    _STATE_KEY = "knot"

    @staticmethod
    def _state(context):
        return context.state.setdefault(KnotLifecycleStrategy._STATE_KEY, {})

    def process_server_response(self, context, server_response):
        super().process_server_response(context, server_response)

        client_pool = Config().clients.clients_requesting_deletion
        if (
            context.client_id not in client_pool
            or "rollback_round" not in server_response
        ):
            return

        logging.info(
            "[%s] Unlearning sampler deployed: %s%% of the samples were deleted.",
            context,
            Config().clients.deleted_data_ratio * 100,
        )

        reload_allowed = (
            not hasattr(Config().data, "reload_data") or Config().data.reload_data
        )
        if reload_allowed:
            logging.info("[%s] Loading the dataset.", context)
            context.datasource = None
            if context.owner is not None:
                context.owner.datasource = None

        state = self._state(context)
        state["use_unlearning_sampler"] = True

    def configure(self, context):
        super().configure(context)

        state = self._state(context)
        if not state.pop("use_unlearning_sampler", False):
            return

        sampler = unlearning_iid.Sampler(context.datasource, context.client_id, False)
        context.sampler = sampler
        if context.owner is not None:
            context.owner.sampler = sampler


def create_client(
    *,
    model=None,
    datasource=None,
    algorithm=None,
    trainer=None,
    callbacks=None,
    trainer_callbacks=None,
):
    """Build a Knot client wired with its custom lifecycle strategy."""
    client = simple.Client(
        model=model,
        datasource=datasource,
        algorithm=algorithm,
        trainer=trainer,
        callbacks=callbacks,
        trainer_callbacks=trainer_callbacks,
    )

    client._configure_composable(
        lifecycle_strategy=KnotLifecycleStrategy(),
        payload_strategy=client.payload_strategy,
        training_strategy=client.training_strategy,
        reporting_strategy=client.reporting_strategy,
        communication_strategy=client.communication_strategy,
    )

    return client


# Maintain compatibility for imports expecting a Client callable/class.
Client = create_client
