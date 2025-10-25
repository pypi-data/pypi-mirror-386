"""
Copyright 2025 TESCAN 3DIM, s.r.o.
All rights reserved
"""

from loguru import logger
from compox.algorithm_utils.AlgorithmDeployer import AlgorithmDeployer
from compox.algorithm_utils.AlgorithmManager import AlgorithmManager
from compox.components.db_connection_builder import build_database_connection
from compox.database_connection import BaseConnection


def deploy_algorithm_from_folder(root_path: str, database_connection: BaseConnection.BaseConnection) -> None:
    """
    Store algorithm into database.

    Parameters
    ----------
    root_path : str
        Algorithm
    database_connection : BaseConnection.BaseConnection
        The database connection object.

    Returns
    -------
    None
    """
    print("root_path")
    algorithm_deployer = AlgorithmDeployer(root_path)
    algorithm_manager = AlgorithmManager(
        database_connection=database_connection
    )

    try:
        algorithm_manager.delete_algorithms(
            name=algorithm_deployer.algorithm_name,
            major_version=algorithm_deployer.algorithm_major_version,
            minor_version=algorithm_deployer.algorithm_minor_version,
        )
    except Exception as _:
        logger.error(
            f"Could not delete algorithm {algorithm_deployer.algorithm_name} "
            f"{algorithm_deployer.algorithm_major_version}."
            f"{algorithm_deployer.algorithm_minor_version}"
        )

    algorithm_deployer.store_algorithm(database_connection=database_connection)


def remove_algorithm_from_folder(root_path, database_connection):
    """
    Helper function that looks at an algorithm folder and removes the algorithm
    from the database if it exists.
    """
    algorithm_deployer = AlgorithmDeployer(root_path)
    algorithm_manager = AlgorithmManager(
        database_connection=database_connection
    )

    try:
        algorithm_manager.delete_algorithms(
            name=algorithm_deployer.algorithm_name,
            major_version=algorithm_deployer.algorithm_major_version,
            minor_version=algorithm_deployer.algorithm_minor_version,
        )
        logger.info(
            f"Deleted algorithm {algorithm_deployer.algorithm_name} "
            f"{algorithm_deployer.algorithm_major_version}."
            f"{algorithm_deployer.algorithm_minor_version}"
        )
    except Exception as _:
        logger.error(
            f"Could not delete algorithm {algorithm_deployer.algorithm_name} "
            f"{algorithm_deployer.algorithm_major_version}."
            f"{algorithm_deployer.algorithm_minor_version}"
        )
