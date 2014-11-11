
def main(j, args, params, tags, tasklet):

    page = args.page

    page.addBootstrap()

    head = """
<title>Login</title>
<style type='text/css'>
body {padding-top: 60px; padding-bottom: 40px;}</style>
<style type="text/css">
  body {
    padding-top: 40px;
    padding-bottom: 40px;
    background-color: #f5f5f5;
  }
  .form-signin {
    max-width: 300px;
    padding: 19px 29px 29px;
    margin: 0 auto 20px;
    background-color: #fff;
    border: 1px solid #e5e5e5;
    -webkit-border-radius: 5px;
       -moz-border-radius: 5px;
            border-radius: 5px;
    -webkit-box-shadow: 0 1px 2px rgba(0,0,0,.05);
       -moz-box-shadow: 0 1px 2px rgba(0,0,0,.05);
            box-shadow: 0 1px 2px rgba(0,0,0,.05);
  }
  .form-signin .form-signin-heading,
  .form-signin .checkbox {
    margin-bottom: 10px;
  }
  .form-signin input[type="text"],
  .form-signin input[type="password"] {
    font-size: 16px;
    height: auto;
    margin-bottom: 15px;
    padding: 7px 9px;
  }
</style>
	"""

    body = """
<div class="container">
      <form id="loginform" class="form-signin" method="post" action="/$$path$$querystr">
        <h2 class="form-signin-heading">Please sign in</h2>
        <input type="text" class="input-block-level"  name="user_login_" placeholder="Username">
        <input type="password" class="input-block-level" name="passwd" placeholder="Password">
        <button class="btn btn-large btn-primary" type="submit">Sign in</button>
      </form>
 </div> <!-- /container -->
	"""
    if args.tags.tagExists("jumptopath"):
        jumpto = args.tags.tagGet("jumptopath")
    else:
        jumpto = args.requestContext.path
        if jumpto.find("wiki") == 0:
            jumpto = jumpto[5:].strip("/")

    querystr = args.requestContext.env['QUERY_STRING']

    session = args.requestContext.env['beaker.session']
    session["querystr"] = querystr
    session.save()

    # if jumpto=="$$path":
        # path unknown
        # jumpto=""

    page.addBootstrap()
    page.addHTMLHeader(head)
    page.body += body
    page.body = page.body.replace("$$path", jumpto)
    if querystr:
        querystr = "?%s" % querystr
    page.body = page.body.replace("$$querystr", querystr)

    params.result = page
    return params


def match(j, args, params, tags, tasklet):
    return True
