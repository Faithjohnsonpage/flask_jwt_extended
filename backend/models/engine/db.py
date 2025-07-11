#!/usr/bin/env python3
"""DB module
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models.base_model import BaseModel, Base
from os import getenv
from typing import Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session


class DB:
    """Interacts with the MySQL database for Sentinel"""

    def __init__(self) -> None:
        """Instantiate a DB object"""
        USER = getenv('DB_USER')
        PWD = getenv('DB_PWD')
        HOST = getenv('DB_HOST')
        DB = getenv('DB_DB')
        ENV = getenv('DB_ENV')

        self.__engine = create_engine(
            f'mysql+mysqldb://{USER}:{PWD}@{HOST}/{DB}',
            pool_pre_ping=True
        )

        if ENV == "test":
            Base.metadata.drop_all(self.__engine)

    def get_engine(self):
        """Return the SQLAlchemy engine"""
        return self.__engine

    def new(self, obj: Type[BaseModel]) -> None:
        """Add the object to the current database session"""
        self.__session.add(obj)

    def save(self) -> None:
        """Commit all changes of the current database session"""
        self.__session.commit()

    def delete(self, obj: Optional[BaseModel] = None) -> None:
        """Delete from the current database session obj if not None"""
        if obj is not None:
            self.__session.delete(obj)

    def reload(self) -> None:
        """Reloads data from the database"""
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def close(self) -> None:
        """Call remove() method on the private session attribute"""
        if self.__session:
            self.__session.remove()

    def get(self, cls: Type[BaseModel], id: str) -> Optional[BaseModel]:
        """Retrieve an object by its primary key"""
        if id is None:
            return None
        return self.__session.get(cls, id)

    def all(self, cls: Type[BaseModel]) -> List[BaseModel]:
        """Retrieve all objects of a specific class"""
        return self.__session.query(cls).all()

    def filter_by(self,
                  cls: Type[BaseModel],
                  **kwargs: Any
                  ) -> Optional[BaseModel]:
        """Retrieve the first object based on specific criteria"""
        return self.__session.query(cls).filter_by(**kwargs).first()

    def count(self, cls: Type[BaseModel]) -> int:
        """Count the number of objects in a specific class"""
        return self.__session.query(cls).count()

    def exists(self, cls: Type[BaseModel], **kwargs: Any) -> bool:
        """Check if an object with specific criteria exists"""
        return self.__session.query(cls).filter_by(**kwargs).first() is not None
