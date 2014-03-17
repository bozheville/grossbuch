__author__ = 'bozh'
import sys
import re
import time

class Bank:
    def __init__(self, db):
        self.db = db

    def getSummary(self):
        summary = self.db.summary.find()
        r = {}
        for row in summary:
            r[row['_id']] = row['amount']
        return r

    def getUsers(self):
        users = self.db.users.find().sort('name', 1)
        r = []
        for user in users:
            r.append(user)
        return r

    def getTransactions(self):
        transactions = self.db.transactions.find().sort('ts', -1)
        r = []
        for tr in transactions:
            del tr['_id']
            r.append(tr)
        return r

    def toggleUser(self, uid, disabled):
        self.db.users.update({'_id': uid}, {'$set': {'disabled': bool(int(disabled))}})

    def newTransaction(self, uid, type, amount):
        if re.match(r'^[0-9]+$', amount):
            if type == 'debit':
                self.__newTransactionDebit(uid, amount)
            elif type == 'payout':
                self.__newTransactionPayout(uid, amount)
            elif type == 'credit':
                self.__newTransactionCredit(uid, amount)
            elif type == 'repayment':
                self.__newTransactionRepayment(uid, amount)
            else:
                return False
            self.__countLoans()
            self.__countTotal()
            self.__logTransaction(uid, type, amount)

    def __newTransactionPayout(self, uid, amount):
        self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': -int(amount)}})
        self.db.users.update({'_id': uid}, {'$inc': {'debit': -int(amount)}})

    def __newTransactionDebit(self, uid, amount):
        self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': int(amount)}})
        self.db.users.update({'_id': uid}, {'$inc': {'debit': int(amount)}})

    def __newTransactionCredit(self, uid, amount):
        self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': -int(amount)}})
        self.db.summary.update({'_id': 'in_credit'}, {'$inc': {'amount': int(amount)}})
        self.db.users.update({'_id': uid}, {'$inc': {'credit': int(amount)}})

    def __newTransactionRepayment(self, uid, amount):
        self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': int(amount)}})
        self.db.summary.update({'_id': 'in_credit'}, {'$inc': {'amount': -int(amount)}})
        self.db.users.update({'_id': uid}, {'$inc': {'credit': -int(amount)}})

    def __logTransaction(self, uid, type, amount):
        user = self.db.users.find_one({'_id': uid})
        log = {}
        log['date'] = time.strftime("%d.%m.%Y")
        log['amount'] = amount
        log['type'] = type
        log['name'] = uid
        log['fullname'] = user['name']
        log['ts'] = int(time.time())
        log['summary'] = self.getSummary()
        self.db.transactions.insert(log)

    def __countLoans(self):
        pipeline = [{'$group': {
            '_id': 'r',
            'credit': {'$sum': {
                '$cond':[
                    {'$gt': ['$credit', 0]},
                    '$credit',
                    0
                ]
            }},
            'externalLoan': {'$sum': {
                '$cond':[
                    {'$lt': ['$credit', 0]},
                    '$credit',
                    0
                ]
            }}
        }}]
        r = self.db.users.aggregate(pipeline)
        r = r['result'].pop(0)
        self.db.summary.update({'_id':'in_credit'}, {'$set': {'amount': int(r['credit'])}})
        self.db.summary.update({'_id':'externalLoan'}, {'$set': {'amount': -int(r['externalLoan'])}})


    def __countTotal(self):
        summary = self.getSummary()
        total = summary['in_bank'] + summary['in_credit'] - summary['externalLoan']
        self.db.summary.update({'_id': 'total'}, {'$set': {'amount': total}})
        return total