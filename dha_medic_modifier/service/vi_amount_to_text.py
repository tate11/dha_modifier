# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# ENGLISH
# -------------------------------------------------------------

to_19_vi = ('không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu',
            'bảy', 'tám', 'chín', 'mười', 'mười một', 'mười hai', 'mười ba',
            'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín')
tens_vi = ('hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi')
denom_vi = ('',
            'ngàn', 'triệu', 'tỷ', 'nghìn tỷ')


def _convert_nn_vi(val):
    """ convert a value < 100 to French
    """
    if val < 20:
        return to_19_vi[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_vi)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19_vi[val % 10]
            return dcap


def _convert_nnn_vi(val):
    """ convert a value < 1000 to french

        special cased because it is the level that kicks
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19_vi[rem] + ' trăm'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nn_vi(mod)
    return word


def vietnam_number(val):
    if val < 100:
        return _convert_nn_vi(val)
    if val < 1000:
        return _convert_nnn_vi(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_vi))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn_vi(l) + ' ' + denom_vi[didx]
            if r > 0:
                ret = ret + ', ' + vietnam_number(r)
            return ret


def amount_to_text_vi(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = vietnam_number(abs(int(list[0])))
    end_word = vietnam_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 0) and ' đồng' or ' đồng'
    final_result = start_word + ' ' + units_name + ' ' + end_word + ' ' + cents_name
    return final_result