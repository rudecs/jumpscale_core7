[actor] @dbtype:fs
	"""
	this is an example actor
	"""    
    method:addInfo
		"""		
        can be multi line
		"""
		var:info str,,dotnotation of info e.g. 'water.white.level.sb 10'  (as used in graphite)
		result:bool    

    method:getInfoWithHeaders
		"""		
		"""
        var:id str,,id in dot noation e.g. 'water.white.level.sb'  (can be multiple use comma as separation)
        var:start int,,epoch
        var:stop int,,epoch
        var:maxvalues int,360,nr of values you want to return
        result:list(list)  #first row are headers, 2nd row is epoch of measurement, 3e & next rows are the values

    method:getInfo5MinFromTo
        """     
        will not return more than 1 month of info
        """
        var:id str,,id in dot noation e.g. 'water.white.level.sb'
        var:start int,,epoch
        var:stop int,,epoch
        result:dict() #key=epoch, value is the value of the measurement

    method:getInfo1hFromTo
        """     
        will not return more than 12 months of info, resolution = 1h
        """
        var:id str,,id in dot noation e.g. 'water.white.level.sb'
        var:start int,,epoch
        var:stop int,,epoch
        result:dict() #key=epoch, value is the value of the measurement

    method:getInfo5Min
        """     
        return raw info (resolution is 5min)
        """
        var:id str,,id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        var:start int,0,epoch; 0 means all
        var:stop int,0,epoch; 0 means all
        result:list(list) #with the raw info

    method:getInfo1h
        """     
        return raw info (resolution is 1h)
        """
        var:id str,,id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        var:start int,0,epoch; 0 means all
        var:stop int,0,epoch; 0 means all
        result:list(list) #with the raw info

    method:reset
        """     
        reset all stats
        """
        result:bool

        



