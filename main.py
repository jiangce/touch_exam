# -*- coding:utf-8 -*-

from contextlib import closing
from flask import Flask, g, session, redirect, render_template, url_for, request
from bson.objectid import ObjectId
import pymongo
import random
import config
import json

app = Flask(__name__)
app.config.from_object('config')


def connectMongo():
    return pymongo.MongoClient(host=app.config['DATABASE_HOST'],
                               port=app.config['DATABASE_PORT'])


@app.before_request
def before_request():
    g.mongoclient = connectMongo()
    g.exam = g.mongoclient.exam


@app.teardown_request
def teardown_request(exception):
    g.mongoclient.close()


@app.route('/newuser/<username>/<password>')
def createuser(username, password):
    newuser = {'name': username, 'pass': password, 'logincount': 0, 'error': {}}
    user = g.exam.user.find_one({'name': username})
    if user:
        g.exam.user.update({'name': username}, newuser)
    else:
        g.exam.user.insert(newuser)
    return 'ok'


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return render_template('hello.html')
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username').lower().strip()
        password = request.form.get('password')
        user = g.exam.user.find_one({'name': username})
        if user and user['pass'] == password:
            session['user'] = user['name']
            user['logincount'] += 1
            g.exam.user.update({'name': user['name']}, user)
            return 'success'
        return 'failed'


@app.route('/')
def hello():
    if not session.get('user'):
        return redirect('login')
    return render_template('hello.html')


@app.route('/getquestion/', methods=['POST'])
def getQuestion():
    if not session.get('user'):
        return redirect('login')
    condition = generateCondition()
    return mongoToJson(randomQuestion(condition))


def removeUserRangeQuestion(user, qid):
    if not user or not user.get('range'):
        return
    if qid in user['range']:
        user['range'].remove(qid)


@app.route('/commitcorrect/', methods=['POST'])
def commitCorrect():
    if not session.get('user'):
        return redirect('login')
    user = g.exam.user.find_one({'name': session['user']})
    ids = request.form.get('correctid')
    removeUserRangeQuestion(user, ids)
    if user and ids:
        errs = user.get('error', {})
        count = errs.get(ids)
        if count:
            count -= 1
            if count == 0:
                del errs[ids]
            else:
                errs[ids] = count
            user['error'] = errs
            g.exam.user.update({'name': user['name']}, user)
    return 'ok'


@app.route('/commitwrong/', methods=['POST'])
def commitWrong():
    if not session.get('user'):
        return redirect('login')
    user = g.exam.user.find_one({'name': session['user']})
    ids = request.form.get('wrongid')
    removeUserRangeQuestion(user, ids)
    if user and ids:
        errs = user.get('error', {})
        errs[ids] = errs.get(ids, 0) + 5
        user['error'] = errs
        g.exam.user.update({'name': user['name']}, user)
    return 'ok'


def generateCondition():
    d = {'on': True, 'off': False}
    result = {}
    hassingle = d[request.form.get('hassingle', 'on')]
    hasmultiple = d[request.form.get('hasmultiple', 'on')]
    hastorf = d[request.form.get('hastorf', 'on')]
    easy = d[request.form.get('easy', 'on')]
    normal = d[request.form.get('normal', 'on')]
    hard = d[request.form.get('hard', 'on')]
    onlywrong = d[request.form.get('onlywrong', 'off')]
    if not (hassingle and hasmultiple and hastorf):
        types = []
        if hassingle:
            types.append(u'单选')
        if hasmultiple:
            types.append(u'多选')
        if hastorf:
            types.append(u'判断')
        result['type'] = {'$in': types}
    if not (easy and normal and hard):
        diff = []
        if easy:
            diff.append(1)
        if normal:
            diff.append(2)
        if hard:
            diff.append(3)
        result['diff'] = {'$in': diff}
    user = g.exam.user.find_one({'name': session['user']})
    if onlywrong:
        if user and user.get('error'):
            result['_id'] = {'$in': map(ObjectId, user['error'].keys())}
    else:
        initUserExercieseRange(user)
        result['_id'] = {'$in': map(ObjectId, user['range'])}
    print result
    return result


def initUserExercieseRange(user):
    if not user or user.get('range'):
        return
    cu = g.exam.item.find(None, {'_id': 1})
    user['range'] = map(lambda i: str(i['_id']), cu)
    g.exam.user.update({'name': user['name']}, user)
    print user.get('range')


def randomQuestion(cdt=None):
    count = g.exam.item.find(cdt).count()
    if count == 0:
        return None
    index = random.randint(0, count - 1)
    return g.exam.item.find(cdt).skip(index).next()


def mongoToJson(obj):
    if not obj:
        return ''
    if obj.get('_id'):
        obj['_id'] = str(obj['_id'])
    return json.dumps(obj)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
