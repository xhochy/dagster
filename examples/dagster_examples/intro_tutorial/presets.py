import csv
import sqlite3
from copy import deepcopy

import sqlalchemy
import sqlalchemy.ext.declarative

from dagster import (
    Field,
    ModeDefinition,
    PresetDefinition,
    String,
    execute_pipeline_with_preset,
    pipeline,
    resource,
    solid,
)
from dagster.utils import script_relative_path


class LocalSQLiteWarehouse(object):
    def __init__(self, conn_str):
        self._conn_str = conn_str

    def update_normalized_cereals(self, records):
        conn = sqlite3.connect('example.db')
        curs = conn.cursor()
        try:
            curs.execute('DROP TABLE IF EXISTS normalized_cereals')
            curs.execute(
                '''CREATE TABLE IF NOT EXISTS normalized_cereals
                (name text, mfr text, type text, calories real,
                 protein real, fat real, sodium real, fiber real,
                 carbo real, sugars real, potass real, vitamins real,
                 shelf real, weight real, cups real, rating real)'''
            )
            curs.executemany(
                '''INSERT INTO normalized_cereals VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                [tuple(record.values()) for record in records],
            )
        finally:
            curs.close()


@resource(config={'conn_str': Field(String)})
def local_sqlite_warehouse_resource(context):
    return LocalSQLiteWarehouse(context.resource_config['conn_str'])


Base = sqlalchemy.ext.declarative.declarative_base()


class NormalizedCereal(Base):
    __tablename__ = 'normalized_cereals'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    mfr = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.String)
    calories = sqlalchemy.Column(sqlalchemy.Float)
    protein = sqlalchemy.Column(sqlalchemy.Float)
    fat = sqlalchemy.Column(sqlalchemy.Float)
    sodium = sqlalchemy.Column(sqlalchemy.Float)
    fiber = sqlalchemy.Column(sqlalchemy.Float)
    carbo = sqlalchemy.Column(sqlalchemy.Float)
    sugars = sqlalchemy.Column(sqlalchemy.Float)
    potass = sqlalchemy.Column(sqlalchemy.Float)
    vitamins = sqlalchemy.Column(sqlalchemy.Float)
    shelf = sqlalchemy.Column(sqlalchemy.Float)
    weight = sqlalchemy.Column(sqlalchemy.Float)
    cups = sqlalchemy.Column(sqlalchemy.Float)
    rating = sqlalchemy.Column(sqlalchemy.Float)


class SqlAlchemyPostgresWarehouse(object):
    def __init__(self, conn_str):
        self._conn_str = conn_str
        self._engine = sqlalchemy.create_engine(self._conn_str)

    def update_normalized_cereals(self, records):
        Base.metadata.bind = self._engine
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)
        NormalizedCereal.__table__.insert().execute(records)


@resource(config={'conn_str': Field(String)})
def sqlachemy_postgres_warehouse_resource(context):
    return SqlAlchemyPostgresWarehouse(context.resource_config['conn_str'])


@solid
def read_csv(context, csv_path):
    with open(csv_path, 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return lines


@solid
def normalize_calories(context, cereals):
    columns_to_normalize = [
        'calories',
        'protein',
        'fat',
        'sodium',
        'fiber',
        'carbo',
        'sugars',
        'potass',
        'vitamins',
        'weight',
    ]
    quantities = [cereal['cups'] for cereal in cereals]
    reweights = [1.0 / float(quantity) for quantity in quantities]

    normalized_cereals = deepcopy(cereals)
    for idx in range(len(normalized_cereals)):
        cereal = normalized_cereals[idx]
        for column in columns_to_normalize:
            cereal[column] = float(cereal[column]) * reweights[idx]

    context.resources.warehouse.update_normalized_cereals(normalized_cereals)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='unittest',
            resource_defs={'warehouse': local_sqlite_warehouse_resource},
        ),
        ModeDefinition(
            name='dev',
            resource_defs={
                'warehouse': sqlachemy_postgres_warehouse_resource
            },
        ),
    ],
    preset_defs=[
        PresetDefinition(
            'unittest',
            environment_dict={
                'solids': {
                    'read_csv': {
                        'inputs': {'csv_path': {'value': 'cereal.csv'}}
                    }
                },
                'resources': {
                    'warehouse': {'config': {'conn_str': ':memory:'}}
                },
            },
            mode='unittest',
        ),
        PresetDefinition.from_files(
            'dev',
            environment_files=[
                script_relative_path('presets_dev_warehouse.yaml'),
                script_relative_path('presets_csv.yaml'),
            ],
            mode='dev',
        ),
    ],
)
def presets_pipeline():
    normalize_calories(read_csv())


if __name__ == '__main__':
    result = execute_pipeline_with_preset(presets_pipeline, 'unittest')
    assert result.success
