print(
    """
You have installed `llm_sim_eval` from the PyPI repository.
`llm_sim_eval` is only available as a privately hosted package.
Please uninstall this package and reinstall it from the private repository.
If you believe you should have access to the private repository, please contact the redis.ai support.
"""
)


class InvalidPackageError(Exception):
    pass


raise InvalidPackageError(
    "llm_sim_eval is only available as a privately hosted package."
)
