
[rootmodel:infotable] #@index
    """
    lists the stats we are keeping
    """
    prop:guid str,,is only one object with guid "infotable"
    prop:infotable dict(str),,key ids used in system (dotnotation always in lcase)

##NOT NEEDED will implement on history level
# [rootmodel:stats] #@index
#     """
#     current info for a certain variable, keeps last info & avg over 1h, avg over 1 day, avg over week
#     """
#     prop:guid str,,is unique name (in dot notation)
#     prop:last int,,last measurement
#     prop:h_1 int,,last half hour kept
#     prop:h_1_nr int,,amounts of measurements logged for last half hour
#     prop:h_2 int,,half hour before last kept (last-1)
#     prop:h_1_nr int,,amounts of measurements logged for last-1 half hour
#     prop:d_1 int,,last half day kept (adds the averaged hours)
#     prop:d_1_nr int,,amounts of measurements logged for last half day
#     prop:d_2 int,,half day before last kept (last-1)
#     prop:d_1_nr int,,amounts of measurements logged for last-1 half day
#     prop:w_1 int,,last half week kept (adds the averaged day)
#     prop:w_1_nr int,,amounts of measurements logged for last half week
#     prop:w_2 int,,half week before last kept (last-1)
#     prop:w_1_nr int,,amounts of measurements logged for last-1 half week


[rootmodel:history] #@index
    """
    history of e.g. level of tank (do per 5 min & per 1h for longer periods)
    keep history for 1 month  per 5 min (31 values=fixed, will always keep for last 31 days even if month shorter)
    keep history for 12 months=year per 1h (52 values=fixed)
    """
    prop:guid str,,is unique name (in dot notation)
    prop:month_5min dict(float),, dict of measurements per 5 min, keep 31 days +1 h : 8929 items in dict   
    prop:year_hour dict(list),, dict of measurements per hour (per hour keep [nritems,total,min,max]), keep 12 months +1 day: 8761 items in dict 
