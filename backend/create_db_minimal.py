import os
from flask import Flask
from extensions import db
from config import Config
import models

app = Flask(__name__)
# Force instance-relative path to be absolute for the primary DB
db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    print(f"Tables created successfully in {db_path}")
