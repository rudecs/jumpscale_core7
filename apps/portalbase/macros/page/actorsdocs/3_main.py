def main(j, args, params, tags, tasklet):
    page = args.page
    actors = args.tags.tagGet('actors', '')

    page.addCSS('/jslib/old/swagger/css/hightlight.default.css')
    page.addCSS('/jslib/old/swagger/css/screen.css')

    page.addJS('/jslib/old/swagger/lib/jquery-1.8.0.min.js')
    page.addJS('/jslib/old/swagger/lib/jquery.slideto.min.js')
    page.addJS('/jslib/old/swagger/lib/jquery.wiggle.min.js')
    page.addJS('/jslib/old/swagger/lib/jquery.ba-bbq.min.js')
    page.addJS('/jslib/old/swagger/lib/handlebars-1.0.rc.1.js')
    page.addJS('/jslib/old/swagger/lib/underscore-min.js')
    page.addJS('/jslib/old/swagger/lib/backbone-min.js')
    page.addJS('/jslib/old/swagger/lib/swagger.js')
    page.addJS('/jslib/old/swagger/swagger-ui.js')
    page.addJS('/jslib/old/swagger/lib/highlight.7.3.pack.js')

    head = """
    <title>Swagger UI</title>
    <script type="text/javascript">
    $(function () {
        window.swaggerUi = new SwaggerUi({
                discoveryUrl:"/restmachine/system/docgenerator/prepareCatalog?actors=%s&format=jsonraw",
                dom_id:"swagger-ui-container",
                supportHeaderParams: false,
                supportedSubmitMethods: ['get', 'post', 'put'],
                onComplete: function(swaggerApi, swaggerUi){
                    if(console) {
                        console.log("Loaded SwaggerUI")
                        console.log(swaggerApi);
                        console.log(swaggerUi);
                    }
                  $('pre code').each(function(i, e) {hljs.highlightBlock(e)});
                },
                onFailure: function(data) {
                    if(console) {
                        console.log("Unable to Load SwaggerUI");
                        console.log(data);
                    }
                },
                docExpansion: "none"
            });

            window.swaggerUi.load();
        });

    </script>
    """ % actors

    body = """
    <div id="message-bar" class="swagger-ui-wrap">
        &nbsp;
    </div>

    <div id="swagger-ui-container" class="swagger-ui-wrap">

    </div>
    """

    page.addHTMLHeader(head)
    page.addHTMLBody(body)

    params.result = page
    return params


def match(j, args, params, tags, tasklet):
    return True
