import stat

import dataset
from dataset.database import Database
from dataset.table import Table
import oschmod

from . import DATABASE_FILE

class DB:
    def __init__(self, db_path):
        # Initialize the database
        self.db : Database = dataset.connect(f'sqlite:///{db_path}')

        # This is a hack to make sure the database is created
        table : Table = self.db.create_table('init')
        table.insert(dict(name='init', value='init'))

        # Set the permissions on the database
        oschmod.set_mode(str(db_path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

db = DB(DATABASE_FILE)