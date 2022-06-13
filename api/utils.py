from .models import User
from flask_login import current_user
from sqlalchemy import func
from .models import Edition, Label, Image, Prediction
from . import db


def check_password(password):
    return password == 'Poumons19!'


def get_user(name):
    return User.query.filter(func.lower(User.name) == func.lower(name)).first()


def build_patient_query():
    q1 = db.session.query(Edition.patient_id)
    q2 = db.session.query(Label.patient_id).group_by(Label.patient_id)
    q3 = q1.union(q2)
    q4 = db.session.query(Image.patient_id).group_by(Image.patient_id).except_(q3)
    q5 = db.session.query(Image.patient_id).filter(Image.patient_id.in_(q4)).group_by(Image.patient_id)
    return q5


def get_patient(is_small_patient):
    query = build_patient_query()
    if is_small_patient:
        patient_id, = query.having(db.func.count(Image.image_id) < 20).first()
    else:
        patient_id, = query.having(db.func.count(Image.image_id) >= 20).first()
    return patient_id


def get_has_large_and_small_patients():
    query = build_patient_query()
    has_large_patients = query.having(db.func.count(Image.image_id) >= 20).count() > 0
    has_small_patients = query.having(db.func.count(Image.image_id) < 20).count() > 0
    return has_large_patients, has_small_patients


def get_patient_image_count(patient_id):
    count, = db.session.query(db.func.count(Image.image_id)).group_by(Image.patient_id). \
        filter(Image.patient_id == patient_id).first()
    return count or 0


def get_patient_image_index(patient_id):
    image_index = db.session.query(db.func.max(Label.image_id)). \
        filter(Label.patient_id == patient_id).scalar()
    return (image_index or 0) + 1


def get_image(patient_id, image_id):
    file = db.session.query(Image.file).filter(Image.patient_id == patient_id, Image.image_id == image_id).scalar()
    return file


def get_labelled_patients_count_by_user():
    return db.session.query(Label.patient_id).filter(Label.user_id == current_user.id).group_by(
        Label.patient_id).count()


def get_rank_label(rank):
    if rank == 1:
        return '1er'
    if rank == 2:
        return '2ème'
    if rank == 3:
        return '3ème'
    return None


def get_rank_color(rank):
    if rank == 1:
        return '#C9B037'
    if rank == 2:
        return '#B4B4B4'
    if rank == 3:
        return '#AD8A56'
    return 'default'


def update_user_rank(user):
    user.rank = None
    user.comp_rank = None
    user.delta_radios = 0
    result = db.session.query(db.func.row_number().over(order_by=db.func.count(Label.image_id).desc()).label('rank'),
                              Label.user_id.label('user_id'),
                              db.func.count(Label.image_id).label('radios')).group_by(Label.user_id).limit(3).all()
    for rank, user_id, radios in result:
        if user_id == user.id:
            current_user.rank = get_rank_label(rank)
            current_user.rank_color = get_rank_color(rank)
            if len(result) > 1:
                comp_index = rank if rank == 1 else rank - 2
                comp_rank, comp_user_id, comp_radios = result[comp_index]
                user.comp_rank = get_rank_label(comp_rank)
                user.comp_rank_color = get_rank_color(comp_rank)
                user.delta_radios = abs(radios - comp_radios)
            break


def get_prediction(patient_id, image_id):
    return Prediction.query.filter_by(patient_id=patient_id, image_id=image_id).first()


def get_ia_accuracy():
    label_count = Label.query.filter(Label.label!=None).count()
    if label_count < 1:
        return 1
    accurate_count = Label.query.join(Prediction).filter(Prediction.diagnostic == Label.label, Label.label != None).count()
    return accurate_count/label_count
