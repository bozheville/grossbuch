import cgi
import bottle
from bottle import route, error, post, get, run, static_file, abort, redirect, response, request, template
import pymongo
import Bank


@bottle.route('/getinfo')
def getinfo():
    r = {}
    r['summary'] = bank.getSummary()
    r['users'] = bank.getUsers()
    r['transactions'] = bank.getTransactions()
    response.content_type = 'application/json'
    return r


@bottle.route('/toggleUser/<uid>/<disabled>')
def toggleUser(uid=0, disabled=0):
    bank.toggleUser(uid, disabled)


@bottle.route('/newTransaction/<uid>/<type>/<amount>')
def newTransaction(uid=0, type='', amount=0):
    bank.newTransaction(uid, type, amount)
    return getinfo()


@bottle.route('/exchange/<user>/<from_amount>/<exchange_type>/<to_amount>')
def exchange(user='', from_amount=0, exchange_type='', to_amount=0):
    bank.Exchange(user, from_amount, exchange_type, to_amount)
    return getinfo()


@bottle.route('/cancelTransaction/')
def cancelTransaction():
    bank.cancelTransaction()
    return getinfo()

@bottle.route('/getDebitStat')
@bottle.route('/getDebitStat/<user>')
def getDebitStat(user='_total'):
    r = bank.getDebitStat(user)
    response.content_type = 'application/json'
    return r

database = pymongo.MongoClient("mongodb://localhost").tuugotv
bank = Bank.Bank(database)

bottle.run(host='localhost', port=33131, reloader=True)