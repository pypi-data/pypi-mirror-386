from .base import BaseEngine

class DeltaRs(BaseEngine):
    """
    Delta-Rs Engine
    """

    def __init__(self):
        """
        Initialize the Delta-rs Engine Configs
        """
        from deltalake.writer import write_deltalake
        from deltalake import DeltaTable
        self.write_deltalake = write_deltalake
        self.DeltaTable = DeltaTable
        