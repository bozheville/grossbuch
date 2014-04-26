__author__ = 'bozh'
import pymongo

db = pymongo.MongoClient("mongodb://localhost").tuugotv
db.debitstat.remove()
transactions = db.transactions.find({'type': {'$in': ['debit', 'payout']}})
items = {'by_day': {}, 'by_month': {}, 'by_year': {}}
for item in transactions:
    date = item['date'].split('.')
    date[2] = int(date[2])
    date[1] = int(date[1])
    date[0] = int(date[0])
    amount = int(item['amount'])
    if item['type'] != 'debit':
         amount *= -1
    _id = {
        'd': date[0],
        'm': date[1],
        'y': date[2]
    }
    user = item['name'].replace('.', '_dot_')
    update = {
        '$inc': {
            'debit.'+user: amount,
            'debit._total': amount
        }
    }
    db.debitstat.update({'_id': _id}, update, True)
