import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/img'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отбор астронавтов</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1 class="text-center mt-4">Загрузка фотографии</h1>
        <p class="text-center subtitle">для участия в миссии</p>
        <div class="form-box mx-auto">
            <form method="post" enctype="multipart/form-data">
                <p>Приложите фотографию</p>
                <input type="file" name="file" class="mb-3" accept="image/*">
                {% if filename %}
                    <div class="photo-preview">
                        <img src="{{ url_for('static', filename='img/' + filename) }}" alt="Фото">
                    </div>
                {% endif %}
                <br>
                <button type="submit" class="btn btn-primary mt-3">Отправить</button>
            </form>
        </div>
    </div>
</body>
</html>'''


@app.route('/')
def index():
    return redirect(url_for('load_photo'))


@app.route('/load_photo', methods=['GET', 'POST'])
def load_photo():
    filename = None

    uploads = os.listdir(app.config['UPLOAD_FOLDER'])
    images = [f for f in uploads if allowed_file(f)]
    if images:
        filename = sorted(images)[-1]

    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('load_photo'))

    return render_template_string(TEMPLATE, filename=filename)


if __name__ == '__main__':
    app.run(port=8080)
