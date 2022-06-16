from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from . import db
from .models import Image, Label, Edition, Prediction
from .utils import get_patient, get_patient_image_count, get_patient_image_index, get_image, \
    get_labelled_patients_count_by_user, get_has_large_and_small_patients, update_user_rank, \
    get_prediction, get_ia_accuracy

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
@login_required
def home():
    has_large_patients, has_small_patients = get_has_large_and_small_patients()
    if current_user.edition:
        return redirect(url_for('main.labeling'))
    update_user_rank(current_user)
    total_patients = db.session.query(Image.patient_id).group_by(Image.patient_id).count()
    total_files = Image.query.count()
    labelled_patients = db.session.query(Label.patient_id).group_by(Label.patient_id).count()
    labelled_files = Label.query.count()
    user_labelled_files = len(current_user.labels)
    user_labelled_patients = get_labelled_patients_count_by_user()
    ia_accuracy = get_ia_accuracy()
    return render_template('home.html', name=current_user.dname, total=total_patients,
                           progression_files=labelled_files, user_progression_files=user_labelled_files,
                           progression=labelled_patients, user_progression=user_labelled_patients,
                           has_large_patients=has_large_patients, has_small_patients=has_small_patients,
                           ia_accuracy=ia_accuracy, total_files=total_files)


@main.route('/labeling')
@login_required
def labeling():
    if not current_user.edition:
        return redirect(url_for('main.home'))
    image_index = get_patient_image_index(current_user.edition.patient_id)
    file = get_image(current_user.edition.patient_id, image_index)
    file_previous = None if image_index <= 1 else get_image(current_user.edition.patient_id, image_index - 1)
    file_next = None if image_index >= current_user.edition.images_count else \
        get_image(current_user.edition.patient_id, image_index + 1)
    prediction = get_prediction(current_user.edition.patient_id, image_index)
    return render_template('labeling.html', patient_id=current_user.edition.patient_id, image_index=image_index,
                           file=file, file_previous=file_previous, file_next=file_next, prediction=prediction)


@main.route('/labeling/<int:image_index>', methods=['POST'])
@login_required
def labeling_post(image_index):
    f_label = request.form.get('label')
    label = True if f_label == '1' else (False if f_label == '0' else None)
    if current_user.edition:
        db.session.add(Label(patient_id=current_user.edition.patient_id, image_id=image_index, label=label,
                             user_id=current_user.id))
        db.session.commit()
        if image_index >= current_user.edition.images_count:
            db.session.delete(current_user.edition)
            db.session.commit()
            return redirect(url_for('main.home'))
    return redirect(url_for('main.labeling'))


@main.route('/cancelling/<int:image_index>', methods=['POST'])
@login_required
def cancelling_post(image_index):
    if current_user.edition:
        if image_index > 0:
            label = Label.query.filter(Label.patient_id == current_user.edition.patient_id,
                                       Label.image_id == image_index,
                                       Label.user_id == current_user.id).first()
            if label is not None:
                db.session.delete(label)
        else:
            db.session.delete(current_user.edition)
        db.session.commit()
    return redirect(url_for('main.labeling'))


@main.route('/patient', methods=['POST'])
@login_required
def patient():
    is_small_patient = request.form.get('patient_type') == "1"
    if current_user.edition:
        return redirect(url_for('main.labeling'))
    patient_id = get_patient(is_small_patient)
    current_user.edition = Edition(patient_id=patient_id, user=current_user,
                                   images_count=get_patient_image_count(patient_id))
    db.session.commit()
    return redirect(url_for('main.labeling'))


@main.route('/api/labels')
@login_required
def labels():
    result = dict(labels=[{'file': row.file, 'label': row.label} for row in
                          Label.query.join(Image).add_columns(Label.label, Image.file).all()])
    return result


@main.route('/api/test')
def test():
    result = dict(labels=[{'diagnostic': row.diagnostic, 'label': row.label} for row in
                          Label.query.join(Prediction).add_columns(Prediction.diagnostic, Label.label).all()])
    return result
