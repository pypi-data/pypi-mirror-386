import pandas as pd
from sqlalchemy import create_engine

from .abstract_executor import AbstractPythonExecutor


class PandasPythonExecutor(AbstractPythonExecutor[pd.DataFrame]):
    library_name = "pandas"
    handled_types = ["PandasDbt"]

    def prepare_bulk_write(self, df: pd.DataFrame, table: str, schema: str) -> str:
        engine = create_engine(self.conn_string)
        df.head(1).to_sql(
            name=table, con=engine, schema=schema, if_exists="replace", index=False
        )
        return df.to_csv(sep="\t", na_rep="\\N", index=False, header=False)
