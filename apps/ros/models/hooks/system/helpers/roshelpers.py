from flask import current_app

def increment(key):
    counter = current_app.data.driver.db.counter
    seq = counter.find_one({'_id': key}) 
    if seq == None:
        seq= {"_id": key, "seq": 1}
        counter.save(seq)
    else: 
        counter.update({'_id': key},{"$inc": {"seq": 1}})
        seq = counter.find_one({'_id': key})
    return seq["seq"]