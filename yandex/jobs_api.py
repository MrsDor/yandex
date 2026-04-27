import flask
from flask import jsonify, make_response

blueprint = flask.Blueprint(
    'jobs_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/jobs')
def get_jobs():
    from . import db_session
    from .jobs import Jobs
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).all()
    return jsonify(
        {
            'jobs': [item.to_dict(only=('id', 'job', 'team_leader', 'work_size')) for item in jobs]
        }
    )


@blueprint.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_one_job(job_id):
    from . import db_session
    from .jobs import Jobs
    db_sess = db_session.create_session()
    job = db_sess.get(Jobs, job_id)
    if not job:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'job': job.to_dict(only=(
                'id', 'job', 'team_leader', 'work_size', 'collaborators', 'is_finished'
            ))
        }
    )


@blueprint.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@blueprint.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)
