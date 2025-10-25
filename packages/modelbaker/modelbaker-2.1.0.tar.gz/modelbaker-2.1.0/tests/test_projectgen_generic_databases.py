"""
/***************************************************************************
                              -------------------
        begin                : 28/03/18
        git sha              : :%H$
        copyright            : (C) 2018 by Jorge Useche
        email                : naturalmentejorge@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import shutil
import tempfile

import psycopg2
import psycopg2.extras
import pyodbc
from qgis.core import QgsProject
from qgis.testing import start_app, unittest

from modelbaker.dataobjects.project import Project
from modelbaker.dbconnector.db_connector import DBConnectorError
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import get_pg_connection_string, iliimporter_config, testdata_path

start_app()


class TestProjectGenGenericDatabases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def setUp(self):
        "Run before each test"
        QgsProject.instance().clear()

    def test_empty_postgres_db(self):
        generator = None
        try:
            generator = Generator(
                DbIliMode.ili2pg,
                "dbname=not_exists_database user=docker password=docker host={db_host}".format(
                    db_host=os.environ["PGHOST"]
                ),
                "smart1",
                "",
            )
        except (DBConnectorError, FileNotFoundError):
            # DBConnectorError: FATAL:  database "not_exists_database" does not exist
            assert generator is None

    def test_empty_mssql_db(self):
        generator = None
        configuration = iliimporter_config(DbIliMode.ili2mssql)
        try:
            uri = (
                "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
                    drv="{ODBC Driver 17 for SQL Server}",
                    server=configuration.dbhost,
                    db="not_exists_database",
                    uid=configuration.dbusr,
                    pwd=configuration.dbpwd,
                )
            )
            generator = Generator(DbIliMode.ili2mssql, uri, "smart1", "")
        except DBConnectorError as e:
            base_exception = e.base_exception
            sqlstate = base_exception.args[0]
            # pyodbc.ProgrammingError + error code 42000:
            # Cannot open database "not_exists_database" requested by the login. The login failed
            assert int(sqlstate) == 42000
            assert generator is None

    def test_postgres_db_without_schema(self):
        generator = Generator(DbIliMode.ili2pg, get_pg_connection_string(), "smart1")
        assert generator is not None
        assert len(generator.layers()) == 0

    def test_mssql_db_without_schema(self):
        configuration = iliimporter_config(DbIliMode.ili2mssql)
        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=configuration.dbhost,
            db=configuration.database,
            uid=configuration.dbusr,
            pwd=configuration.dbpwd,
        )

        generator = Generator(DbIliMode.ili2mssql, uri, "smart1")
        assert generator is not None
        assert len(generator.layers()) == 0

    def test_postgres_db_with_empty_schema(self):
        uri = get_pg_connection_string()
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("CREATE SCHEMA IF NOT EXISTS empty_schema;")

        try:
            generator = Generator(DbIliMode.ili2pg, uri, "smart1", "empty_schema")
            assert len(generator.layers()) == 0
        finally:
            cur.execute("DROP SCHEMA empty_schema CASCADE;")

    def test_mssql_db_with_empty_schema(self):
        configuration = iliimporter_config(DbIliMode.ili2mssql)

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=configuration.dbhost,
            db=configuration.database,
            uid=configuration.dbusr,
            pwd=configuration.dbpwd,
        )

        conn = pyodbc.connect(uri)
        cur = conn.cursor()

        try:
            cur.execute("CREATE SCHEMA empty_schema;")
            cur.commit()
        except pyodbc.ProgrammingError as e:
            sqlstate = e.args[0]
            # pyodbc.ProgrammingError + error code 42S01:
            # schema exist
            assert sqlstate == "42S01"

        try:
            generator = Generator(DbIliMode.ili2mssql, uri, "smart1", "empty_schema")
            assert len(generator.layers()) == 0
        finally:
            cur.execute("DROP SCHEMA empty_schema")
            cur.commit()

    def test_postgis_db_with_non_empty_and_no_interlis_schema_with_spatial_tables(self):
        uri = get_pg_connection_string()
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("CREATE SCHEMA IF NOT EXISTS no_interlis_schema_spatial;")
        try:
            cur.execute(
                """
                CREATE TABLE no_interlis_schema_spatial.point (
                    id serial NOT NULL,
                    name text,
                    geometry geometry(POINT, 4326) NOT NULL,
                    CONSTRAINT point_id_pkey PRIMARY KEY (id)
                );
                CREATE TABLE no_interlis_schema_spatial.region (
                    id serial NOT NULL,
                    name text,
                    geometry geometry(POLYGON, 4326) NOT NULL,
                    id_point integer,
                    CONSTRAINT region_id_pkey PRIMARY KEY (id)
                );
            """
            )
            cur.execute(
                """
                ALTER TABLE no_interlis_schema_spatial.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                REFERENCES no_interlis_schema_spatial.point (id) MATCH FULL
                ON DELETE SET NULL ON UPDATE CASCADE;
            """
            )
            conn.commit()

            generator = Generator(
                DbIliMode.ili2pg, uri, "smart1", "no_interlis_schema_spatial"
            )
            layers = generator.layers()

            assert len(layers) == 2
            relations, _ = generator.relations(layers)
            assert len(relations) == 1

            for layer in layers:
                assert layer.geometry_column is not None
        finally:
            cur.execute("DROP SCHEMA no_interlis_schema_spatial CASCADE;")
            conn.commit()
            cur.close()

    def test_mssql_db_with_non_empty_and_no_interlis_schema_with_spatial_tables(self):
        schema_name = "no_interlis_schema_spatial"

        configuration = iliimporter_config(DbIliMode.ili2mssql)
        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=configuration.dbhost,
            db=configuration.database,
            uid=configuration.dbusr,
            pwd=configuration.dbpwd,
        )

        conn = pyodbc.connect(uri)
        cur = conn.cursor()

        try:
            cur.execute("CREATE SCHEMA {};".format(schema_name))
            cur.commit()
        except pyodbc.ProgrammingError as e:
            sqlstate = e.args[0]
            # pyodbc.ProgrammingError + error code 42S01:
            # schema exist
            assert sqlstate == "42S01"

        try:
            cur.execute(
                """
                CREATE TABLE {schema_name}.point (
                    id INT PRIMARY KEY,
                    name text,
                    geometry GEOMETRY NOT NULL
                );

                CREATE TABLE {schema_name}.region (
                    id INT PRIMARY KEY,
                    name text,
                    geometry GEOMETRY NOT NULL,
                    id_point integer
                );
            """.format(
                    schema_name=schema_name
                )
            )
            cur.execute(
                """
                ALTER TABLE {schema_name}.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                REFERENCES {schema_name}.point;
            """.format(
                    schema_name=schema_name
                )
            )
            conn.commit()

            generator = Generator(DbIliMode.ili2mssql, uri, "smart1", schema_name)
            layers = generator.layers()

            assert len(layers) == 2
            relations, _ = generator.relations(layers)
            assert len(relations) == 1

            for layer in layers:
                assert layer.geometry_column is not None
            generator._db_connector.conn.close()
        finally:
            cur.execute(
                """
            drop table {schema_name}.region;
                drop table {schema_name}.point;
                drop schema {schema_name};""".format(
                    schema_name=schema_name
                )
            )
            conn.commit()
            cur.close()

    def test_postgis_db_with_non_empty_and_no_interlis_schema_with_non_spatial_tables(
        self,
    ):
        uri = get_pg_connection_string()
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("CREATE SCHEMA IF NOT EXISTS no_interlis_schema;")
        try:
            cur.execute(
                """
                CREATE TABLE no_interlis_schema.point (
                    id serial NOT NULL,
                    name text,
                    CONSTRAINT point_id_pkey PRIMARY KEY (id)
                );
                CREATE TABLE no_interlis_schema.region (
                    id serial NOT NULL,
                    name text,
                    id_point integer,
                    CONSTRAINT region_id_pkey PRIMARY KEY (id)
                );
            """
            )
            cur.execute(
                """
                ALTER TABLE no_interlis_schema.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                REFERENCES no_interlis_schema.point (id) MATCH FULL
                ON DELETE SET NULL ON UPDATE CASCADE;
            """
            )
            conn.commit()

            generator = Generator(DbIliMode.ili2pg, uri, "smart1", "no_interlis_schema")
            layers = generator.layers()

            assert len(layers) == 2
            relations, _ = generator.relations(layers)
            assert len(relations) == 1

            for layer in layers:
                assert layer.geometry_column is None
        finally:
            cur.execute("DROP SCHEMA no_interlis_schema CASCADE;")
            conn.commit()
            cur.close()

    def test_mssql_db_with_non_empty_and_no_interlis_schema_with_non_spatial_tables(
        self,
    ):
        schema_name = "no_interlis_schema"

        configuration = iliimporter_config(DbIliMode.ili2mssql)
        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=configuration.dbhost,
            db=configuration.database,
            uid=configuration.dbusr,
            pwd=configuration.dbpwd,
        )

        conn = pyodbc.connect(uri)
        cur = conn.cursor()

        try:
            cur.execute("CREATE SCHEMA {};".format(schema_name))
            cur.commit()
        except pyodbc.ProgrammingError as e:
            sqlstate = e.args[0]
            # pyodbc.ProgrammingError + error code 42S01:
            # schema exist
            assert sqlstate == "42S01"

        try:
            cur.execute(
                """
                    CREATE TABLE {schema_name}.point (
                        id INT PRIMARY KEY,
                        name text
                    );

                    CREATE TABLE {schema_name}.region (
                        id INT PRIMARY KEY,
                        name text,
                        id_point integer
                    );
                """.format(
                    schema_name=schema_name
                )
            )
            cur.execute(
                """
                    ALTER TABLE {schema_name}.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                    REFERENCES {schema_name}.point;
                """.format(
                    schema_name=schema_name
                )
            )
            conn.commit()

            generator = Generator(DbIliMode.ili2mssql, uri, "smart1", schema_name)
            layers = generator.layers()

            assert len(layers) == 2
            relations, _ = generator.relations(layers)
            assert len(relations) == 1

            for layer in layers:
                assert layer.geometry_column is None
        finally:
            cur.execute(
                """
                drop table {schema_name}.region;
                    drop table {schema_name}.point;
                    drop schema {schema_name};""".format(
                    schema_name=schema_name
                )
            )
            conn.commit()
            cur.close()

    def test_empty_geopackage_db(self):
        generator = Generator(
            DbIliMode.ili2gpkg, testdata_path("geopackage/test_empty.gpkg"), "smart2"
        )
        assert len(generator.layers()) == 0

    def test_non_empty_ogr_geopackage_db(self):
        generator = Generator(
            DbIliMode.ili2gpkg,
            testdata_path("geopackage/test_ogr_empty.gpkg"),
            "smart2",
        )
        assert len(generator.layers()) == 0

    def test_non_empty_geopackage_db(self):
        generator = Generator(
            DbIliMode.ili2gpkg,
            testdata_path("geopackage/test_relations.gpkg"),
            "smart2",
        )
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert len(qgis_project.mapLayers()) == 2
        assert len(qgis_project.relationManager().relations()) == 1

        for layer in available_layers:
            assert layer.geometry_column is not None

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
