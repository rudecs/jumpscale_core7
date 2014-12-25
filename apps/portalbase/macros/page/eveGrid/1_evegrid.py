
def main(j, args, params, tags, tasklet):
	page = args.page

	pars = (line.split('=') for line in args.cmdstr.strip().splitlines())
	pars = dict((p[0].strip(), p[1].strip()) for p in pars)
	eveGrid = {
		'specJsonPath': pars.get('spec.json.path', '/docs/spec.json'),
		'schemaURL': pars.get('schema.url', ''),
		'entityName': pars.get('entity.name', '')
	}

	# Add our static resources only once to the page
	if '/jslib/jquery/jqueryDataTable/css/eve-grid.css' not in str(page):
		page.addCSS('/jslib/bootstrap/css/bootstrap.css')
		page.addCSS('/jslib/jquery/jqueryDataTable/css/dataTables.bootstrap.css')
		page.addCSS('/jslib/jquery/jqueryDataTable/css/bootstrap-theme.min.css')
		page.addCSS('/jslib/jquery/jqueryDataTable/css/eve-grid.css')

		page.addJS('/jslib/jquery/jqueryDataTable/js/jquery.dataTables.js')
		page.addJS('/jslib/angular/angular1-3-0.min.js')
		page.addJS('/jslib/bootstrap/js/bootstrap.min.js')
		page.addJS('/jslib/underscore/underscore-min.js')
		page.addJS('/jslib/jquery/jqueryDataTable/js/dataTables.bootstrap.js')
		page.addJS('/jslib/jquery/jqueryDataTable/js/eve-grid.js')
		
	page.addMessage('''
		<div class="container">
	        <div id="{entityName}-container" eve-grid eve-url="{schemaURL}" eve-entity="{entityName}" eve-spec-path="{specJsonPath}">
	       	</div>
    	</div>
	 '''.format(**eveGrid))

	params.result = page
	return params


def match(j, args, params, tags, tasklet):
    return True
