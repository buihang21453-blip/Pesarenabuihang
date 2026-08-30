"""Tournament module routes.

V1.4.22 introduces only the isolated tournament shell.  No tournament data is
mocked and no ranking/match tables are reused by this module yet.
"""


def register_routes(context):
    globals().update(context)

    @app.get('/tournaments')
    @login_required
    def tournaments():
        return render_template('tournaments.html')
