"""Public, account-free friendly team randomizer.

V1.6.91: intentionally contains no database, storage or realtime access.
All randomisation happens in the browser from a small static dataset.
"""


def register_routes(context):
    globals().update(context)

    @app.route('/friendly')
    def friendly_public():
        return render_template('friendly_public.html')
