from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)

# class Bitstonker():
#     def render_vars():
#         stonk=stonk
#         graph=graph
#         graph_display=graph_display
#         usd_start_price=usd_start_price
#         btc_start_price=btc_start_price
#         usd_end_price=usd_end_price
#         btc_end_price=btc_end_price
#         usd_roi=usd_roi
#         usd_roi_pct=usd_roi_pct
#         btc_roi=btc_roi
#         btc_roi_pct=btc_roi_pct
#         dollar_display=dollar_display
