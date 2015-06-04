# -*- coding: utf-8 -*-

import pymongo
import quickexcel
import os

filename = os.path.join(os.getcwd(), 'tiku.xlsx')
app = quickexcel.ExApp()
wb = app.getworkbook(filename)
app.visible = True

difficulty = {u'简单' : 1, u'容易' : 1, u'中等' : 2, u'困难' : 3}
trueoffalse = {u'正确' : [0], u'对' : [0], u'错误' : [1], u'错' : [1]}

client = pymongo.MongoClient()
db = client.exam

def parseChoiceAnswer(chars):
    result = []
    for c in chars:
        try:
            result.append(int(c) - 1)
        except:
            pass
    return result

def _getChoiceQuestions(excelsheetname, questiontag):
    ws = wb.getworksheet(excelsheetname)
    result = []
    i = 2
    t = ws.gettext('a%s' % i)
    t = t and t.strip()
    while t:
        try:
            tar = {}
            tar['type'] = questiontag
            tar['domain'] = ws.gettext('b%s' % i)
            tar['diff'] = difficulty[ws.gettext('c%s' % i)]
            tar['question'] = ws.gettext('d%s' % i)
            tar['choice'] = []
            for c in 'efghi':
                choice = ws.gettext('%s%s' % (c,i))
                choice = choice and choice.strip()
                if choice:
                    tar['choice'].append(choice)
            tar['answer'] = parseChoiceAnswer(ws.gettext('j%s' % i))
            tar['people'] = ws.gettext('k%s' % i)
            result.append(tar)
        except Exception as ex:
            print i
            print ex
        finally:
            i += 1
            t = ws.gettext('a%s' % i)
            t = t and t.strip()
    return result

def getSingleChoiceQuestions():
    return _getChoiceQuestions(u'单选', u'单选')

def getMultipleChoiceQuestions():
    return _getChoiceQuestions(u'多选', u'多选')

def getTureOrFalseQuestions():
    ws = wb.getworksheet(u'判断题')
    result = []
    i = 2
    t = ws.gettext('a%s' % i)
    t = t and t.strip()
    while t:
        try:
            tar = {}
            tar['type'] = u'判断'
            tar['domain'] = ws.gettext('a%s' % i)
            tar['diff'] = difficulty[ws.gettext('b%s' % i)]
            tar['question'] = ws.gettext('c%s' % i)
            tar['choice'] = [u'对', u'错']
            tar['answer'] = trueoffalse[ws.gettext('d%s' % i)]
            tar['people'] = ws.gettext('e%s' % i)
            result.append(tar)
        except Exception as ex:
            print i
            print ex
        finally:
            i += 1
            t = ws.gettext('a%s' % i)
            t = t and t.strip()
    return result

def saveToDb():
    app.visible = False
    db.item.insert(getSingleChoiceQuestions())
    print '单选题保存成功'
    db.item.insert(getMultipleChoiceQuestions())
    print '多选题保存成功'
    db.item.insert(getTureOrFalseQuestions())
    print '判断题保存成功'
    app.visible = True
