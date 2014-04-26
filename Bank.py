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
            if tr['type'] == 'SellUSD':
                tr['amount'] = str(tr['usd']) + ' USD to ' + str(tr['amount']) + ' UAH'
            if tr['type'] == 'BuyUSD':
                tr['amount'] = str(tr['amount']) + ' UAH to ' + str(tr['usd']) + ' USD'
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

    def __logTransaction(self, uid, type, amount, usd=0):
        user = self.db.users.find_one({'_id': uid})
        log = {}
        log['date'] = time.strftime("%d.%m.%Y")
        log['amount'] = amount
        log['usd'] = usd
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
        self.db.summary.update({'_id': 'in_credit'}, {'$set': {'amount': int(r['credit'])}})
        self.db.summary.update({'_id': 'externalLoan'}, {'$set': {'amount': -int(r['externalLoan'])}})

    def __countTotal(self):
        summary = self.getSummary()
        total = summary['in_bank'] + summary['in_credit'] - summary['externalLoan']
        self.db.summary.update({'_id': 'total'}, {'$set': {'amount': total}})
        return total

    def Exchange(self, user, amount_from, exchange_type, amount_to, do_not_log=False):
        action = ''
        usdamount = 0
        if exchange_type == 'uah2usd':
            usdamount = int(amount_to)
            uahamount = int(amount_from)
            self.db.summary.update({'_id': 'usd'}, {'$inc': {'amount': int(usdamount)}}, True)
            self.db.summary.update({'_id': 'total'}, {'$inc': {'amount': -int(uahamount)}}, True)
            self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': -int(uahamount)}}, True)
            action = 'BuyUSD'
        elif exchange_type == 'usd2uah':
            usdamount = int(amount_from)
            uahamount = int(amount_to)
            self.db.summary.update({'_id': 'usd'}, {'$inc': {'amount': -int(usdamount)}}, True)
            self.db.summary.update({'_id': 'total'}, {'$inc': {'amount': int(uahamount)}}, True)
            self.db.summary.update({'_id': 'in_bank'}, {'$inc': {'amount': int(uahamount)}}, True)
            action = 'SellUSD'
        if not do_not_log:
            self.__logTransaction(user, action, uahamount, usdamount)

    def cancelTransaction(self):
        lastTransaction = self.db.transactions.find().sort('ts', -1).limit(1)
        for tr in lastTransaction:
            if tr['type'] == 'debit':
                self.__newTransactionPayout(tr['name'], tr['amount'])
            elif tr['type'] == 'payout':
                self.__newTransactionDebit(tr['name'], tr['amount'])
            elif tr['type'] == 'credit':
                self.__newTransactionRepayment(tr['name'], tr['amount'])
            elif tr['type'] == 'repayment':
                self.__newTransactionCredit(tr['name'], tr['amount'])
            elif tr['type'] == 'SellUSD':
                self.Exchange(tr['name'], tr['amount'], 'uah2usd', tr['usd'], True)
            elif tr['type'] == 'BuyUSD':
                self.Exchange(tr['name'], tr['usd'], 'usd2uah', tr['amount'], True)
            else:
                return False
            self.db.transactions.remove({'_id': tr['_id']})

    def getDebitStat(self, user):
        user = user.replace('.', '_dot_')
        pipeline = [
            {'$group': {
                '_id': {
                    'm': '$_id.m',
                    'y': '$_id.y'
                },
                'debit': {'$sum': '$debit.'+user}
            }}
            , {'$sort': {
                '_id.y': 1
                , '_id.m': 1
            }}
            , {'$project': {
                '_id': {
                    '$concat': [
                        {'$substr': ['$_id.m', 0, 2]}
                        , '.'
                        , {'$substr': ['$_id.y', 0, 4]}
                    ]
                },
                'debit': 1
            }},
        ]
        stat = self.db.debitstat.aggregate(pipeline)
        return stat