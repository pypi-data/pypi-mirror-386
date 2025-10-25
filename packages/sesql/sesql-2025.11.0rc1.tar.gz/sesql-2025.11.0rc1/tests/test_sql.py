# File: tests/test_sql.py
import pytest
from unittest.mock import MagicMock

from seSql.dbc.Exceptions import SQLQueryException, SQLConnectionException
from seSql.sql import sql

DB_CONFIG = {
    "server": "test_server",
    "port": 1433,
    "user": "test_user",
    "password": "test_password",
    "trust": "yes",
    "db": "test_db",
    "mars": "no",
}


def test_execute_procedure_success(mocker):
    # Mocking the SQL object and its methods
    mock_connection = mocker.Mock()
    mock_connection.query.return_value = [{"key": "value"}]

    oSql = sql()
    mocker.patch.object(oSql, "_sql__cnxn", mock_connection)

    procedure_name = "sp_TestProcedure"
    parameters = {"param1": "value1", "param2": 123}

    result = oSql.execute_procedure(procedure_name=procedure_name, parameters=parameters, stats=False)

    mock_connection.query.assert_called_once_with("EXEC sp_TestProcedure @param1='value1', @param2=123", stats=False)
    assert result == [{"key": "value"}]


def test_execute_procedure_with_exception(mocker):
    # Mocking the SQL object and its methods
    mock_connection = mocker.Mock()
    mock_connection.query.side_effect = Exception("Simulated Query Exception")

    oSql = sql()
    mocker.patch.object(oSql, "_sql__cnxn", mock_connection)

    procedure_name = "sp_TestProcedure"
    parameters = {"param1": "value1", "param2": 123}

    with pytest.raises(SQLQueryException) as exc_info:
        oSql.execute_procedure(procedure_name=procedure_name, parameters=parameters, stats=False)

    assert "Simulated Query Exception" in str(exc_info.value)


def test_execute_procedure_no_parameters(mocker):
    # Mocking the SQL object and its methods
    mock_connection = mocker.Mock()
    mock_connection.query.return_value = [{"result": "success"}]

    oSql = sql()
    mocker.patch.object(oSql, "_sql__cnxn", mock_connection)

    procedure_name = "sp_TestNoParams"

    result = oSql.execute_procedure(procedure_name=procedure_name, stats=True)

    mock_connection.query.assert_called_once_with("EXEC sp_TestNoParams", stats=True)
    assert result == [{"result": "success"}]


def test_close_successful():
    db = sql()
    db._sql__cnxn = MagicMock()  # Mocking the connection object
    db.close()
    db._sql__cnxn.close.assert_called_once()


def test_close_exception():
    db = sql()
    db._sql__cnxn = None
    with pytest.raises(SQLConnectionException, match=".*"):
        db.close()
