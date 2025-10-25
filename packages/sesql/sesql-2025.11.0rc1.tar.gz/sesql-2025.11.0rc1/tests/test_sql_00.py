# from unittest.mock import MagicMock
#
# import pytest
# from seSql.dbc.Exceptions import SQLConnectionException
# from seSql.sql import sql
#
#
# def test_close_successful():
#     db = sql()
#     db._sql__cnxn = MagicMock()  # Mocking the connection object
#     db.close()
#     db._sql__cnxn.close.assert_called_once()
#
#
# def test_close_exception():
#     db = sql()
#     db._sql__cnxn = None
#     with pytest.raises(SQLConnectionException, match=".*"):
#         db.close()
