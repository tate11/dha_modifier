# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#

import datetime
import itertools

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

import xlrd
from xlrd import xlsx

class ServiceReadXlsx(object):
    
    def read_xls_book(self, book, sheet_index=0):
        sheet = book.sheet_by_index(sheet_index)
        # emulate Sheet.get_rows for pre-0.9.4
        for row in itertools.imap(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        unicode(cell.value)
                        if is_float
                        else unicode(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    # emulate xldate_as_datetime for pre-0.9.3
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                elif cell.ctype is xlrd.XL_CELL_ERROR:
                    raise ValueError(
                        _("Error cell found while reading XLS/XLSX file: %s") %
                        xlrd.error_text_from_code.get(
                            cell.value, "unknown error code %s" % cell.value)
                    )
                else:
                    values.append(cell.value)
            if any(x for x in values if x.strip()):
                yield values
    
    def read_xls(self, file, sheet_index=0):
        """ Read file content, using xlrd lib """
        book = xlrd.open_workbook(file_contents=file)
        data = self.read_xls_book(book, sheet_index)
        return data

