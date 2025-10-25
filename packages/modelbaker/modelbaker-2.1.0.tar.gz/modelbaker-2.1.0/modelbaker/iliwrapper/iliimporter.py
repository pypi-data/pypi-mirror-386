"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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
from .ili2dbconfig import (
    Ili2DbCommandConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
)
from .iliexecutable import IliExecutable


class Importer(IliExecutable):
    def __init__(self, dataImport=False, parent=None):
        self.__data_import = dataImport
        super().__init__(parent)

    def _create_config(self) -> Ili2DbCommandConfiguration:
        if self.__data_import:
            configuration = ImportDataConfiguration()
        else:
            configuration = SchemaImportConfiguration()

        return configuration
