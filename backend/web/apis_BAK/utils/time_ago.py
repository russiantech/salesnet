from datetime import datetime

def timeAgo(time):
    #difference = datetime.now() - time
    if not time:
        return 'of recent' 
    difference = datetime.timestamp(datetime.now()) - datetime.timestamp(time) 

    if (difference < 1 ):
        return f' less than a second ago'
    
    condition = {
        'year'  : (12 * 30 * 24 * 60 * 60),
        'month' : (30 * 24 * 60 * 60),
        'week'  : (7 * 24 * 60 * 60),
        'day'   : (24 * 60 * 60),
        'hour'  : (60 * 60),
        'minute': (60),
        'second': (1)
    }

    for k, v in condition.items():
        d = (difference / v)

        if (d >= 1):
            t = round(d)
            return f' '+ str(t) +' '+ k + 's ago' if (t > 1) else 'just now'