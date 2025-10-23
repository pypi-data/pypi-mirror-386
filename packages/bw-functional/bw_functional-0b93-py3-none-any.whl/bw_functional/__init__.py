__all__ = (
    "allocation_strategies",
    "generic_allocation",
    "Process",
    "Product",
    "MFExchange",
    "MFExchanges",
    "FunctionalSQLiteDatabase",
    "property_allocation",
    "convert_sqlite_to_functional_sqlite",
    "convert_functional_sqlite_to_sqlite",
    "update",
)

from importlib import metadata
# import os
from logging import getLogger

from bw2data import labels
from bw2data.subclass_mapping import DATABASE_BACKEND_MAPPING, NODE_PROCESS_CLASS_MAPPING

from .allocation import allocation_strategies, generic_allocation, property_allocation
from .database import FunctionalSQLiteDatabase
from .node_classes import Process, Product
from .edge_classes import MFExchange, MFExchanges
from .convert import convert_sqlite_to_functional_sqlite, convert_functional_sqlite_to_sqlite
from .update import update, latest

log = getLogger(__name__)

DATABASE_BACKEND_MAPPING["functional_sqlite"] = FunctionalSQLiteDatabase
NODE_PROCESS_CLASS_MAPPING["functional_sqlite"] = FunctionalSQLiteDatabase.node_class


if "waste" not in labels.node_types:
    labels.lci_node_types.append("waste")
if "nonfunctional" not in labels.node_types:
    labels.other_node_types.append("nonfunctional")

# make sure allocation happens on parameter changes
def _init_signals():
    from bw2data.signals import on_activity_parameter_recalculate, project_changed

    on_activity_parameter_recalculate.connect(_check_parameterized_exchange_for_allocation)
    project_changed.connect(_check_and_update)

def _check_parameterized_exchange_for_allocation(_, name):
    import bw2data as bd
    from bw2data.parameters import ParameterizedExchange
    from bw2data.backends import ExchangeDataset

    databases = [k for k, v in bd.databases.items() if v["backend"] == "functional_sqlite"]

    p_exchanges = ParameterizedExchange.select().where(ParameterizedExchange.group==name)
    exc_ids = [p_exc.exchange for p_exc in p_exchanges]
    exchanges = ExchangeDataset.select(ExchangeDataset.output_database, ExchangeDataset.output_code).where(
        (ExchangeDataset.id.in_(exc_ids)) &
        (ExchangeDataset.type == "production") &
        (ExchangeDataset.output_database.in_(databases))
    )
    process_keys = set(exchanges.tuples())

    for key in process_keys:
        process = bd.get_activity(key)
        if not isinstance(process, Process):
            log.warning(f"Process {key} is not an instance of Process, skipping allocation check.")
            continue
        process.allocate()

def _check_and_update(dataset):
    if dataset.data is None:
        dataset.data = {}
        dataset.save()

    current = dataset.data.get("bw_functional_version")

    if current != latest:
        log.info(f"Updating {dataset.name} to latest bw_functional datastructure version {latest}")
        dataset.data["bw_functional_version"] = update(current)
        dataset.save()

    return

_init_signals()
