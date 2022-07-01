# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError,UserError
from datetime import date, timedelta
from odoo.addons import decimal_precision as dp
from dateutil.relativedelta import relativedelta
import json
import xlsxwriter
from io import BytesIO
import base64
import string  
from collections import Counter

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    valuation_adjustment_lines = fields.One2many(
        'stock.valuation.adjustment.lines', 'cost_id', 'Valuation Adjustments',
        states={'done': [('readonly', True)]})

    def get_additional_landed_cost(self,product_id,quantity):
        lis=[]
        tit=[]
        for i in self.valuation_adjustment_lines:
            if i.product_id.id == product_id and i.quantity == quantity:
                dct={
                    'additional_landed_cost':i.additional_landed_cost,
                    }
                lis.append(dct)
                tit.append(i.cost_line_id.name)
        return lis, tit

    def product_info(self):
        lis=[]
        control=[]                
        for i in self.valuation_adjustment_lines:
            if i.product_id.id not in control or i.quantity not in control:
                control.append(i.product_id.id)
                control.append(i.quantity)
                cos,cant = self.get_additional_landed_cost(i.product_id.id,i.quantity)
                dct={
                    'pro_name':i.product_id.display_name,
                    'add':lis,
                    'weight':i.weight,
                    'volume':i.volume,
                    'quantity':i.quantity,
                    'measurement':i.product_id.product_tmpl_id.uom_id.name,
                    'cost':cos,
                    'former_cost_per_unit':i.former_cost/i.quantity,
                    'former_cost':i.former_cost,
                    }
                lis.append(dct)           
        return lis, cant

    def fix_date(self,date):
        date = date + relativedelta(hours=5)
        return date.strftime("%d/%m/%Y") if date else ''


    def import_info(self):
        lis=[]
        for i in self.import_ids:
            lis=[{'name':_('Folder'), 'value':i.name},
                {'name':_('Type'), 'value':i.type_import.name},
                {'name':_('Customs Regime'), 'value':i.customs_regime},
                {'name':_('B/L #'), 'value':i.bl or ''},
                {'name':_('DAI #'), 'value':i.dai or ''},
                {'name':_('Container'), 'value':i.container or ''},
                {'name':_('Shipping Date'), 'value':self.fix_date(i.boarding_date) or ''},
                {'name':_('Estimated Arrival Date'), 'value':self.fix_date(i.estimated_date) or ''},
                {'name':_('Entry Warehouse Date'), 'value':self.fix_date(i.admission_date) or ''},
                {'name':_('Input Warehouse'), 'value':i.cellar},
                {'name':_('Amount Total landing cost'), 'value':self.amount_total}]
        return lis
           
   
    def report(self):
        file_data =  BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        import_info=self.import_info()
        product, tit= self.product_info()      
        name = _('Report Landed Cost')
        self.xslx_body(workbook,product,tit,name,import_info)
        workbook.close()
        file_data.seek(0)
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': name + ' ' + self.import_ids.name,
            'store_fname': name + ' ' + self.import_ids.name,
            'type': 'binary',
            #'datas_fname': name+'.xlsx',
        })
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(attachment.id)
        return{
        "type": "ir.actions.act_url",
        "url": url,
        "target": "new",
        }

    def xslx_body(self,workbook,product,tit,name,import_info):

        #Ejem. 2 = B
        def num2col(n):
            string = ""

            while n > 0 :
                n, remainder = divmod(n - 1, 26)
                string = chr(65 + remainder) + string

            return string

        title_header_row_style = workbook.add_format({
            'align': 'center',
            'bold':True,
            'border':1,
            'font_color':'#FFFFFF',
            'bg_color':'#5C8BF4'})

        title_total_row_style = workbook.add_format({
            'align': 'center',
            'bold':True,
            'border':0})

        title_style = workbook.add_format({
            'bold':True,
            'font_size':16,
            'border':0})

        title_style.set_center_across()

        currency_format = workbook.add_format({
            'num_format': '[$$-409]#,##0.00',
            'border':1 })

        currency_format_din = workbook.add_format({
            'num_format': '[$$-409]#,##0.00',
            'border':1,
            'bg_color':'#E4DFEC'})            

        sub_currency_format = workbook.add_format({
            'num_format': '[$$-409]#,##0.00',
            'border':0,
            'bold':True})

        body_right = workbook.add_format({
            'align': 'right', 
            'border':1 })

        body_left = workbook.add_format({
            'align': 'left', 
            'border':1 })

        header_label_style = workbook.add_format({
            'align': 'left', 
            'bold':True, 
            'border':0 })

        header_content_style = workbook.add_format({
            'align': 'left', 
            'border':0 })

        header_content_num_style = workbook.add_format({
            'align': 'left', 
            'num_format': '[$$-409]#,##0.00',
            'border':0 })    

        sheet = workbook.add_worksheet(name)
        sheet.merge_range('A2:F2', name.upper(), title_style)
          
        colspan = 0  #Columna desde donde empieza a imprimir el reporte 0 = A
              
        lis_tit = (_('Product'),_('Weight'),_('Volumen'),_('Quantity'),_('Unit Measure'),_('Previous Cost(Per unit)'),_('Previous Cost'))
        tit_f = (_('Final Product Cost(Per unit)'),_('New Cost'))
        join = lis_tit + tuple(tit) + tit_f

        #Imprime el header
        for fila, imp in enumerate(import_info):
            sheet.write(fila + 3, colspan, imp['name'] + ':', header_label_style)
            #Cambiar el estilo al campo Amount Total landing cost
            if fila == 10:
                style = header_content_num_style
            else:
                style = header_content_style
            sheet.write(fila + 3, colspan + 1, imp['value'], style)

        fila = fila + 6
        fila1 = fila

        #Imprime la fila de cabecera
        for sec, j in enumerate(join):
            sheet.set_column('{0}:{0}'.format(num2col(sec + 1)), len(j) + 4)
            sheet.write(fila, sec, j.upper(), title_header_row_style) # sec inicia con 0, imprime desde la columna A
  
        sheet.set_column('A:A', 50)
        sheet.set_column('B:B', 20)
        
        for p in product:
            fila+=1
            var=0
            sheet.write(fila,colspan, p['pro_name'],body_left)
            sheet.write(fila,colspan + 1, p['weight'],body_right)
            sheet.write(fila,colspan + 2, p['volume'],body_right)
            sheet.write(fila,colspan + 3, p['quantity'],body_right)
            sheet.write(fila,colspan + 4, p['measurement'],body_right)
            sheet.write(fila,colspan + 5, p['former_cost_per_unit'],currency_format)
            sheet.write(fila,colspan + 6, p['former_cost'],currency_format)

            #Imprime el total del costo anterior
            form = '=sum(' + num2col(colspan + 7) + str(fila + 1) + ':' + num2col(colspan + 7) + str(fila1 + 2) + ')'
            sheet.write(fila + 1, colspan + 6, form, sub_currency_format)

            colspan1 = 7 #Columna desde que empieza a imprimir la secciòn dinámica de los costos

            #Imprime la sección dinámica relacionada con los n gastos que se están distribuyendo.
            for i in p['cost']:   
                sheet.write(fila, colspan1, i['additional_landed_cost'], currency_format_din)

                form1 = '=sum(' + num2col(colspan1 + 1) + str(fila + 1) + ':' + num2col(colspan1 + 1) + str(fila1 + 2) + ')'
                sheet.write(fila + 1, colspan1, form1, sub_currency_format)

                var += i['additional_landed_cost']
                colspan1 += 1

            #lastdinamiccol =  colspan1   
                
            sheet.write(fila,colspan1, p['quantity'] != 0 and ((p['former_cost']+var) / p['quantity']) or 0.0,currency_format)
            sheet.write(fila,colspan1 + 1, p['former_cost'] + var, currency_format)

            #Imprime el total de la última columna
            form = '=sum(' + num2col(colspan1 + 2) + str(fila + 1) + ':' + num2col(colspan1 + 2) + str(fila1 + 2) + ')'
            sheet.write(fila + 1, colspan1 + 1, form, sub_currency_format)


            sheet.write(fila + 1, colspan, 'Total', title_total_row_style)           
