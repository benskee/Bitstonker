from flask import render_template
from app import app

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def not_found_error(error):
    return render_template('index.html'), 500