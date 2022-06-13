from . import db
from flask_login import UserMixin


class Image(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(17), nullable=False, unique=True)


class Label(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    label = db.Column(db.Boolean, nullable=True)
    __table_args__ = (db.ForeignKeyConstraint(('patient_id', 'image_id'), ('image.patient_id', 'image.image_id')),)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Edition(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    images_count = db.Column(db.Integer, nullable=False, default=0)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(50), unique=True, nullable=False)
    dname = db.Column(db.String(100), unique=False)
    labels = db.relationship(Label, backref='user', lazy=True)
    edition = db.relationship(Edition, backref='user', lazy=True, uselist=False)
    rank = None
    comp_rank = None
    rank_color = None
    comp_rank_color = None
    delta_radios = 0


class Prediction(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, primary_key=True)
    diagnostic = db.Column(db.Boolean, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint(('patient_id', 'image_id'), ('label.patient_id', 'label.image_id')),)




