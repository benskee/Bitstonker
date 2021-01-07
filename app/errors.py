from flask import render_template
from app import app

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error_page.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error_page.html'), 500