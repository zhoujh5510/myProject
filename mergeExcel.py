# -*- coding: utf-8

'''
    @author: 周建华
    function: 将一个文件夹下的所有excel文件都合并成一个excel文件
    date: 2015-12-12
    version 1.0
'''

import sys,os
import xlrd
import xlwt
from datetime import date,datetime
from xlutils.copy import copy


'''
    函数功能： 获取当前路径
    参数： 无
    返回值： current_path,当前路径
'''
def get_current_path():
    cur_path = os.getcwd()
    #print str(current_path) + '\\'
    current_path = str(cur_path) + '\\'
    return current_path


'''
    函数功能: 获取当前脚本的当前路径下的所有文件名
    参数： 无
    返回值： 列表，当前脚本的当前路径下的所有文件名
'''
def cur_file_dir():
    #获取脚本路径
    path = os.getcwd()
    if os.path.isdir(path):
        return os.listdir(path)
    elif os.path.isfile(path):
            return os.listdir(os.path.dirname(path))


'''
    函数功能： 获取当前路径下所有的.xlsx文件名
    参数： 无
    返回值： 列表，当前路径下所有的.xlsx文件名
'''
def get_all_xlsx_FileName():
    fileName = cur_file_dir()
    xlsxFile = []
    
    for li in range(len(fileName)):
        existFileName = fileName[li]
        xlsxFileName = existFileName[-4:]
        if xlsxFileName == 'xlsx':
            #print existFileName
            xlsxFile.append(existFileName)
    return xlsxFile
    




'''
    函数功能:设置单元格格式
    参数: 字体类型，字体大小，是否是黑体
    返回值: 字体样式
'''
def set_style(name,height,bold=False):
    style = xlwt.XFStyle()        #初始化样式

    font = xlwt.Font()            #为样式创建字体
    font.name = name              #字体类型，如:'Times New Roman'
    font.bold = bold
    font.color_index = 4
    font.height = height
    
    #borders = xlwt.Borders()
    #borders.left = 6
    #borders.right = 6
    #borders.top = 6
    #borders.bottom = 6

    style.font = font
    #style.borders = borders

    return style


'''
    函数功能: 读取excel文件中的内容，以list(列表)的形式返回
    参数: 读取的excel文件名
    返回值: excel文件中的内容，list类型
'''
def read_excel(infile):
    #print 'read file now.......'
    #print infile
    workbook = xlrd.open_workbook(infile)
    #print workbook
    #print 'open file successfully......'

    sheet = workbook.sheet_by_index(0)
    nrows = sheet.nrows
    ncols = sheet.ncols
    subtext = []
    text = []

    
    for row in range(nrows):
        for col in range(ncols):
            if(sheet.cell(row,col).ctype != 3):            #将一般的类型加入到text中
                subtext.append(sheet.cell_value(row,col))
                #print sheet.cell_value(row,col)
            else:                     #对日期类型进行处理，再加入到text中
                date_value = xlrd.xldate_as_tuple(sheet.cell_value(row,col),workbook.datemode)
                date_tmp = date(*date_value[:3]).strftime('%Y/%m/%d')
                subtext.append(date_tmp)
                #print date_tmp
        text.append(subtext)
        subtext = []
    return text

    
'''
    函数功能: 将text(列表)中的内容写入到一个新的excel文件中
    参数: text，要写入excel中的列表
    返回值: 无
'''
def write_excel(text):
    wfile = xlwt.Workbook()
    sheet1 = wfile.add_sheet(u'Sheet1',cell_overwrite_ok = True)


    for i in range(len(text)):
        for j in range(len(text[i])):
            sheet1.write(i,j,text[i][j],set_style('Times New Roman',220,True))

    wfile.save('out.xls')




'''
    函数功能: 向已经存在的excel中追加数据,前提是要追加的内容和已经存在的exce中的数据格式要一致
    参数: 要追加的excel文件名，existFileName，要追加的内容text
    返回值: 无
'''
def write_to_exist_excel(existFileName,text):
    oldWb = xlrd.open_workbook(existFileName,formatting_info=True)
    
    sheet = oldWb.sheet_by_index(0)
    nrows = sheet.nrows
    ncols = sheet.ncols


    
    newWb = copy(oldWb)
    newWs = newWb.get_sheet(0)
    addText = text[1:]
    for i in range(len(addText)):
        for j in range(len(addText[i])):
            newWs.write(nrows+i,j,addText[i][j],set_style('Times New Roman',220,True))


    #print "write new values ok"
    newWb.save(existFileName)
    #print "save with same ok"

    
    
'''
    函数功能: 输出列表text中的所有内容
    参数： text，要输出的列表名称
    返回值： 无
'''
def print_text(text):
    for i in range(len(text)):
        for j in range(len(text[i])):
            print text[i][j]


'''
    函数功能： 输出列表text中的所有内容
    输入参数： text
    返回值： 无
'''
def print_signaltext(text):
    for i in range(len(text)):
        print text[i]


def deal_excel():
    current_path = get_current_path()
    all_xlsx_fileName = get_all_xlsx_FileName()
    FirstExcel = all_xlsx_fileName[0]
    otherExcel = all_xlsx_fileName[1:]
    #print_signaltext(otherExcel)
    

    #先将第一个excel中的内容写入到out.xls中
    print "处理文件中............."
    print FirstExcel
    FirstExcelPath = current_path + FirstExcel
    FirstExcelText = read_excel(FirstExcelPath)
    write_excel(FirstExcelText)

    #再将其他的excel中的内容追加到out.xls中
    for other in range(len(otherExcel)):
        print otherExcel[other]
        otherExcelPath = current_path + otherExcel[other]
        otherExcelText = read_excel(otherExcelPath)
        write_to_exist_excel('out.xls',otherExcelText)

    print "将当前目录下的所有excel文件都合并到out.xls文件中了"


if __name__ == '__main__':
    deal_excel()
    






    
