"""
/***************************************************************************
    begin                :    25/09/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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

import datetime
import logging
import os
import shutil
import tempfile

import psycopg2
import psycopg2.extras
import pyodbc
from qgis import utils
from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.db_factory.pg_command_config_manager import PgCommandConfigManager
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import ilidataimporter_config, iliimporter_config, testdata_path

start_app()


class TestImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_import_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, "ilimodels/CIAF_LADM"
        )
        dataImporter.configuration.ilimodels = "CIAF_LADM"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path("xtf/test_ciaf_ladm.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        config_manager = PgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        # Check expected data is there in the database schema
        conn = psycopg2.connect(uri)

        # Expected predio data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
                SELECT tipo, st_asText(geometria), st_srid(geometria), t_id
                FROM {}.predio
            """.format(
                importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert (
            record[1]
            == "POLYGON((1000257.426 1002020.376,1000437.688 1002196.495,1000275.472 1002428.19,1000072.25 1002291.539,1000158.572 1002164.914,1000159.942 1002163.128,1000257.426 1002020.376))"
        )
        assert record[2] == 3116
        predio_id = record[3]

        # Expected persona data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
                SELECT documento_numero, nombre, t_id
                FROM {}.persona
            """.format(
                importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0] == "1234354656"
        assert record[1] == "Pepito Perez"
        persona_id = record[2]

        # Expected derecho data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
                SELECT tipo, interesado, unidad
                FROM {}.derecho
            """.format(
                importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[1] == persona_id  # FK persona
        assert record[2] == predio_id  # FK predio

    def test_import_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_import_gpkg.gpkg"
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, "ilimodels/CIAF_LADM"
        )
        dataImporter.configuration.ilimodels = "CIAF_LADM"
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path("xtf/test_ciaf_ladm.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Check expected data is there in the database schema
        conn = utils.spatialite_connect(importer.configuration.dbfile)
        cursor = conn.cursor()
        count = 0

        # Expected predio data
        predio_id = None
        cursor.execute("SELECT tipo, st_srid(geometria), t_id FROM predio")
        for record in cursor:
            count += 1
            assert record[1] == 3116
            predio_id = record[2]

        # Expected persona data
        persona_id = None
        cursor.execute("select documento_numero, nombre, t_id from persona")
        for record in cursor:
            count += 1
            assert record[0] == "1234354656"
            assert record[1] == "Pepito Perez"
            persona_id = record[2]

        # Expected derecho data
        cursor.execute("select tipo, interesado, unidad from derecho")
        for record in cursor:
            count += 1
            assert record[1] == persona_id
            assert record[2] == predio_id

        assert count == 3
        cursor.close()
        conn.close()

    def test_import_mssql(self):

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, "ilimodels/CIAF_LADM"
        )
        dataImporter.configuration.ilimodels = "CIAF_LADM"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path("xtf/test_ciaf_ladm.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # TODO Check importer.configuration.uri
        uri = "DSN={dsn};DATABASE={db};UID={uid};PWD={pwd}".format(
            dsn="testsqlserver",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        # Check expected data is there in the database schema
        conn = pyodbc.connect(uri)

        # Expected predio data
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT ut.iliCode as tipo, geometria.STAsText(), geometria.STSrid, p.t_id
                FROM {schema}.Predio as p INNER JOIN {schema}.LA_BAUnitTipo as ut on p.tipo=ut.T_Id
            """.format(
                schema=importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0] == "Unidad_Derecho"
        assert (
            record[1]
            == "POLYGON ((1000257.426 1002020.376, 1000437.688 1002196.495, 1000275.472 1002428.19, 1000072.25 1002291.539, 1000158.572 1002164.914, 1000159.942 1002163.128, 1000257.426 1002020.376))"
        )
        assert record[2] == 3116
        predio_id = record[3]

        # Expected persona data
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT documento_numero, nombre, t_id
                FROM {}.persona
            """.format(
                importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0] == "1234354656"
        assert record[1] == "Pepito Perez"
        persona_id = record[2]

        # Expected derecho data
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT dt.iliCode as tipo, interesado, unidad
                FROM {schema}.derecho as d INNER JOIN {schema}.COL_DerechoTipo as dt
                on dt.T_id=d.tipo
            """.format(
                schema=importer.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0] == "Posesion"
        assert record[1] == persona_id  # FK persona
        assert record[2] == predio_id  # FK predio

    def test_tid_import_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Expected tid handling
        db_connector = db_utils.get_db_connector(importer.configuration)
        assert db_connector.get_tid_handling()

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.with_importtid = True
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Check expected data is there in the database schema
        config_manager = PgCommandConfigManager(dataImporter.configuration)
        uri = config_manager.get_uri()
        conn = psycopg2.connect(uri)

        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT {}
                FROM {}.station
                WHERE aname = 'Oberwinterthur'
            """.format(
                db_connector.tilitid, dataImporter.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0].lower() == "59ba6620-6cbc-452f-91c2-ea2574b47330"

    def test_tid_import_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_basket_gpkg.gpkg"
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Expected tid handling
        db_connector = db_utils.get_db_connector(importer.configuration)
        assert db_connector.get_tid_handling()

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.with_importtid = True
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Check expected data is there in the database schema
        conn = utils.spatialite_connect(importer.configuration.dbfile)

        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT {}
                FROM station
                WHERE aname = 'Oberwinterthur'
            """.format(
                db_connector.tilitid, dataImporter.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0].lower() == "59ba6620-6cbc-452f-91c2-ea2574b47330"

    def test_tid_import_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "baskets_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        assert importer.run() == iliimporter.Importer.SUCCESS

        # Expected tid handling
        db_connector = db_utils.get_db_connector(importer.configuration)
        assert db_connector.get_tid_handling()

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.with_importtid = True
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Check expected data is there in the database schema
        uri = "DSN={dsn};DATABASE={db};UID={uid};PWD={pwd}".format(
            dsn="testsqlserver",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )
        conn = pyodbc.connect(uri)

        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT {}
                FROM {}.station
                WHERE aname = 'Oberwinterthur'
            """.format(
                db_connector.tilitid, dataImporter.configuration.dbschema
            )
        )
        record = next(cursor)
        assert record is not None
        assert record[0].lower() == "59ba6620-6cbc-452f-91c2-ea2574b47330"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
