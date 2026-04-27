from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    title = request.args.get('title', 'Марсианская миссия')
    return render_template('base.html', title=title)

@app.route('/image_mars')
def image_mars():
    return render_template('image_mars.html', title='Привет, Марс!')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')