# -*- coding: utf-8 -*-
import StringIO
from collections import deque
from odoo.tools import config
from datetime import datetime, timedelta, date
from odoo import models, fields, api
import os
import uuid



try:
        import xlwt
except ImportError:
    xlwt = None

class ServiceExportExcel(models.Model):
    
    _name = 'service.export.excel'
    
    @api.model
    def make_file(self, vals=False, file_name = False):
        if not vals or vals == []:
            return False
        else:
            workbook = xlwt.Workbook(encoding='UTF-8')
            # header_bold = xlwt.easyxf("font: bold on; pattern: pattern solid, fore_colour gray25;")
            header_plain = xlwt.easyxf("align: vert centre, horz center, wrap yes;")
            col_plain = xlwt.easyxf("align: vert centre, horz center, wrap yes;")
            worksheet = workbook.add_sheet('Master Data')

            worksheet.write_merge(0, 1, 0, 0, 'STT', header_plain)
            worksheet.write_merge(0, 1, 1, 1, 'MÃ KHÁCH HÀNG', header_plain)
            worksheet.write_merge(0, 1, 2, 2, 'HỌ VÀ TÊN', header_plain)
            worksheet.write_merge(0, 1, 3, 3, 'ĐIỆN THOẠI', header_plain)
            worksheet.write_merge(0, 1, 4, 4, 'MÔ TẢ', header_plain)
            worksheet.write_merge(0, 1, 5, 5, 'NĂM SINH', header_plain )
            worksheet.write_merge(0, 1, 6, 6, 'GIỚI TÍNH', header_plain )
            worksheet.write_merge(0, 1, 7, 7, 'CHIỀU CAO', header_plain)
            worksheet.write_merge(0, 1, 8, 8, 'CÂN NẶNG', header_plain)
            worksheet.write_merge(0, 1, 9, 9, 'BMI', header_plain)
            worksheet.write_merge(0, 1, 10, 10, 'TÌNH TRẠNG', header_plain)

            worksheet.write_merge(0, 0, 11, 27, 'NỘI KHOA', header_plain)
            worksheet.write_merge(1, 1, 11, 11, 'Tuần Hoàn',  header_plain)
            worksheet.write_merge(1, 1, 12, 12, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 13, 13, 'Hô Hấp',  header_plain )
            worksheet.write_merge(1, 1, 14, 14, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 15, 15, 'Tiêu Hoá',  header_plain )
            worksheet.write_merge(1, 1, 16, 16, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 17, 17, 'Thận - Tiết Niệu - Sinh Dục',  header_plain )
            worksheet.write_merge(1, 1, 18, 18, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 19, 19, 'Cơ xương khớp', header_plain  )
            worksheet.write_merge(1, 1, 20, 20, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 21, 21, 'Thần Kinh', header_plain  )
            worksheet.write_merge(1, 1, 22, 22, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 23, 23, 'Tâm Thần', header_plain  )
            worksheet.write_merge(1, 1, 24, 24, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 25, 25, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 26, 26, 'Phân Loại', header_plain)
            worksheet.write_merge(1, 1, 27, 27, 'Bác Sĩ Nội Khoa', header_plain)

            worksheet.write_merge(0, 0, 28, 30, 'NGOẠI KHOA', header_plain  )
            worksheet.write_merge(1, 1, 28, 28, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 29, 29, 'Phân loại ', header_plain)
            worksheet.write_merge(1, 1, 30, 30, 'Bác sĩ Ngoại Khoa', header_plain)

            worksheet.write_merge(0, 0, 31, 33, 'SẢN PHỤ KHOA', header_plain  )
            worksheet.write_merge(1, 1, 31, 31, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 32, 32, 'Phân loại ', header_plain)
            worksheet.write_merge(1, 1, 33, 33, 'Bác sĩ sản phụ khoa', header_plain)

            worksheet.write_merge(0, 0, 34, 36, 'MẮT', header_plain  )
            worksheet.write_merge(1, 1, 34, 34, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 35, 35, 'Phân loại ', header_plain)
            worksheet.write_merge(1, 1, 36, 36, 'Bác Sĩ Mắt', header_plain)

            worksheet.write_merge(0, 0, 37, 39, 'TAI MŨI HỌNG', header_plain  )
            worksheet.write_merge(1, 1, 37, 37, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 38, 38, 'Phân loại ', header_plain)
            worksheet.write_merge(1, 1, 39, 39, 'Bác Sĩ Tai Mũi Họng', header_plain)

            worksheet.write_merge(0, 0, 40, 42, 'RĂNG HÀM MẶT', header_plain  )
            worksheet.write_merge(1, 1, 40, 40, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 41, 41, 'Phân loại ', header_plain)
            worksheet.write_merge(1, 1, 42, 42, 'Bác Sĩ Răng Hàm Mặt', header_plain)

            worksheet.write_merge(0, 0, 43, 45, 'DA LIỄU', header_plain  )
            worksheet.write_merge(1, 1, 43, 43, 'Kết Luận', header_plain)
            worksheet.write_merge(1, 1, 44, 44, 'Phân loại', header_plain)
            worksheet.write_merge(1, 1, 45, 45, 'Bác Sĩ Da Liễu', header_plain)

            worksheet.write_merge(0, 1, 46, 46, 'Xét Nghiệm', header_plain  )

            worksheet.write_merge(0, 0, 47, 49, 'Cận Lâm Sàng', header_plain)
            worksheet.write_merge(1, 1, 47, 47, 'X-Quang', header_plain  )
            worksheet.write_merge(1, 1, 48, 48, 'Siêu Âm', header_plain  )
            worksheet.write_merge(1, 1, 49, 49, 'Điện Tim', header_plain  )

            worksheet.write_merge(0, 1, 50, 50, 'Kết Luận', header_plain  )
            worksheet.write_merge(0, 1, 51, 51, 'Phân Loại', header_plain)
            worksheet.write_merge(0, 1, 52, 52, 'Đề Nghị', header_plain  )
            worksheet.write_merge(0, 1, 53, 53, 'BÁC SĨ', header_plain)

            for count in range(1, 11):
                worksheet.col(count).width = 5000

            for count in range(11, 54):
                worksheet.col(count).width = 8000

            row = 2
            col = 1
            index = 1
            for datas in vals:
                worksheet.write(row, 0, index, col_plain)
                for data in datas:
                    worksheet.write(row, col, data, col_plain)
                    col += 1
                index += 1
                row += 1
                col = 1
            today = date.today()
            filepath = self.get_tmp_path('%s-%s-export-master-data.xls' % (today.strftime('%y-%m-%d'), uuid.uuid4(),))
            workbook.save(filepath)
            att_id = self.create_odoo_attachment(filepath, file_name)
            return att_id

    @api.model
    def create_odoo_attachment(self, excel_path, filename = False):
        excel_data = ''
        res_model = False
        res_id = False
        with open(excel_path, 'r') as file:  # Use file to refer to the file object
            data = file.read()
            excel_data += data
        if not filename:
            filename = 'report.xls'
        try:
            res_model = self.env.context['params']['model']
            res_id = self.env.context['params']['id']
        except:
            pass

        attachment = self.env.get('ir.attachment').create({
            'name': filename,
            'res_name': filename,
            'type': 'binary',
            'datas_fname': filename,
            'datas': excel_data.encode('base64'),
            'mimetype': 'application/vnd.ms-excel',
            'company_id': self.env.user.company_id.id,
            'res_model': res_model,
            'res_id': res_id,
        })
        return attachment.id

    @api.model
    def get_tmp_path(self, filename):
        return os.path.join(config['data_dir'], 'filestore', self.env.cr.dbname, filename)
