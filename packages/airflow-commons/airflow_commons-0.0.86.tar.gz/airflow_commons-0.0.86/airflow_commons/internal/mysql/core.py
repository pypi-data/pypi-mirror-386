import sqlalchemy
from airflow_commons.logger import get_logger
from sqlalchemy import text, column
from sqlalchemy import update as sql_update
from sqlalchemy.dialects.mysql import insert


logger = get_logger("MySqlCore")


def get_table_metadata(table_name: str, engine_connection: sqlalchemy.engine.Engine):
    """
    Gets the metadata of given table
    :param table_name: table name to get metadata
    :param engine_connection: database engine connection
    :return: sqlalchemy table.
    """
    return sqlalchemy.Table(
        table_name,
        sqlalchemy.MetaData(),
        autoload=True,
        autoload_with=engine_connection,
    )


def upsert(values: dict, session, table_name: str, update_column_names: list = None):
    """
    :param values: values to write into database
    :param session: session context manager
    :param table_name: database table name to write
    :param update_column_names: columns to be updated, default is all columns except the primary key
    :return:
    """
    table_metadata = get_table_metadata(
        table_name=table_name, engine_connection=session.bind
    )
    update_cols = {}
    insert_statement = insert(table_metadata).values(values)

    if update_column_names is None:
        update_column_names = [col.name for col in insert_statement.table.columns]

    for col_name in update_column_names:
        if col_name not in table_metadata.primary_key:
            update_cols.update({col_name: insert_statement.inserted[col_name]})
    upsert_statement = insert_statement.on_duplicate_key_update(**update_cols)
    try:
        session.execute(upsert_statement)
    except Exception as e:
        logger.error(f"An exception occurred while upsert: {e}")
        raise


def update(table_name: str, values: list, Session):
    """
    :param table_name: database table name to write
    :param values: list of values as dictionary with the optional where statetment as a text
    :param Session: session object
    """
    with Session.begin() as session:
        table_metadata = get_table_metadata(
            table_name=table_name, engine_connection=session.bind
        )
        try:
            for statement in values:
                try:
                    where_clause = text(statement["where"])
                except KeyError:
                    where_clause = text("1=1")

                values_formatted = {}
                [
                    values_formatted.update({column(item["column"]): item["value"]})
                    for item in statement["values"]
                ]
                session.execute(
                    sql_update(
                        table_metadata,
                        values=values_formatted,
                        whereclause=where_clause,
                    )
                )
            session.commit()

        except Exception as e:
            logger.error(
                f"An exeption {e} occured, session rollbacked. Noting is changed."
            )
            session.rollback()
            raise e

        logger.debug("Row columns are updated successfully.")
