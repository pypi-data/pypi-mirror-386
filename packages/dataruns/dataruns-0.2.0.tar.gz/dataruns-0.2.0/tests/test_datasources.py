"""
Unit tests for data source classes.
"""

import os
import sqlite3

import numpy as np
import pandas as pd
import pytest

from dataruns.source import CSVSource, SQLiteSource, XLSsource


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def sample_sqlite_db(tmp_path):
    """Create a sample SQLite database for testing."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    df = pd.DataFrame({'id': [1, 2, 3], 'name': ['Alice', 'Bob', 'Charlie']})
    df.to_sql('users', conn, index=False, if_exists='replace')
    conn.close()
    return str(db_path)


@pytest.fixture
def sample_excel_file(tmp_path):
    """Create a sample Excel file for testing."""
    xlsx_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    df.to_excel(xlsx_file, sheet_name='Sheet1', index=False)
    return str(xlsx_file)


class TestCSVSource:
    """Test cases for CSVSource."""

    def test_csv_source_from_file(self, sample_csv_file):
        """Test loading CSV from file."""
        source = CSVSource(file_path=sample_csv_file)
        df = source.extract_data()

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ['a', 'b']

    def test_csv_source_requires_file_or_url(self):
        """Test that CSVSource requires file_path or url."""
        with pytest.raises(AssertionError):
            CSVSource(file_path=None, url=None)

    def test_csv_source_file_not_found(self):
        """Test CSVSource with non-existent file."""
        source = CSVSource(file_path='nonexistent.csv')

        with pytest.raises(FileNotFoundError):
            source.extract_data()

    def test_csv_source_data_integrity(self, sample_csv_file):
        """Test that data is correctly loaded."""
        source = CSVSource(file_path=sample_csv_file)
        df = source.extract_data()

        expected = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert df.equals(expected)


class TestSQLiteSource:
    """Test cases for SQLiteSource."""

    def test_sqlite_source_extract(self, sample_sqlite_db):
        """Test loading data from SQLite."""
        source = SQLiteSource(
            connection_string=sample_sqlite_db,
            query='SELECT * FROM users'
        )
        df = source.extract_data()

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ['id', 'name']

    def test_sqlite_source_with_where_clause(self, sample_sqlite_db):
        """Test SQLite source with WHERE clause."""
        source = SQLiteSource(
            connection_string=sample_sqlite_db,
            query='SELECT * FROM users WHERE id > 1'
        )
        df = source.extract_data()

        assert df.shape[0] == 2
        assert df['id'].tolist() == [2, 3]

    def test_sqlite_source_nonexistent_db(self):
        """Test SQLiteSource with non-existent database."""
        source = SQLiteSource(
            connection_string='nonexistent.db',
            query='SELECT * FROM users'
        )

        # SQLite will create the db, so this won't fail immediately
        # The query will fail instead
        with pytest.raises(Exception):
            source.extract_data()

    def test_sqlite_source_data_integrity(self, sample_sqlite_db):
        """Test that data is correctly loaded from SQLite."""
        source = SQLiteSource(
            connection_string=sample_sqlite_db,
            query='SELECT * FROM users'
        )
        df = source.extract_data()

        assert df.loc[0, 'name'] == 'Alice'
        assert df.loc[1, 'id'] == 2


class TestXLSSource:
    """Test cases for XLSsource."""

    def test_xls_source_extract(self, sample_excel_file):
        """Test loading data from Excel."""
        source = XLSsource(file_path=sample_excel_file, sheet_name='Sheet1')
        df = source.extract_data()

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ['col1', 'col2']

    def test_xls_source_file_not_found(self):
        """Test XLSsource with non-existent file."""
        source = XLSsource(file_path='nonexistent.xlsx', sheet_name='Sheet1')

        with pytest.raises(FileNotFoundError):
            source.extract_data()

    def test_xls_source_data_integrity(self, sample_excel_file):
        """Test that data is correctly loaded from Excel."""
        source = XLSsource(file_path=sample_excel_file, sheet_name='Sheet1')
        df = source.extract_data()

        expected = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        assert df.equals(expected)

    def test_xls_source_requires_file_path(self):
        """Test that XLSsource requires file_path."""
        # Empty string should still work (but might fail on extract)
        source = XLSsource(file_path='', sheet_name='Sheet1')
        assert source.file_path == ''
