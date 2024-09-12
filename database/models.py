from sqlalchemy import Column, String, Integer, Float, create_engine, BigInteger, Boolean, DateTime, ForeignKey, INTEGER, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class AccountBean(Base):
    __tablename__ = 'account'

    id = Column(INTEGER, Sequence('article_aid_seq', start=1, increment=1), primary_key=True)
    dynamic_equity = Column(Float)
    reminder_ahead_of_time = Column(Integer)

class FuturesProductBean(Base):
    __tablename__ = 'futures_products'

    id = Column(INTEGER, Sequence('article_aid_seq', start=1, increment=1), primary_key=True)
    pin_yin = Column(String)
    trading_product = Column(String)
    trading_code = Column(String)
    trading_units = Column(Float)
    minimum_price_change = Column(Float)
    margin_ratio = Column(Float)

class FuturesPositionBean(Base):
    __tablename__ = 'futures_position'

    id = Column(INTEGER, Sequence('article_aid_seq', start=1, increment=1), primary_key=True)
    product_name = Column(String)
    profit_loss_amount = Column(Float)
    stop_loss_price = Column(Float)
    cost_price = Column(Float)
    position_quantity = Column(Integer)
    initial_stop_loss = Column(Float)
    product_value = Column(Float)
    operation_direction = Column(Integer)

class ReminderBean(Base):
    __tablename__ = 'reminder_time'
    id = Column(INTEGER, Sequence('article_aid_seq', start=1, increment=1), primary_key=True)
    reminder_time = Column(String)
    is_checked = Column(Boolean)

class SettingtBean(Base):
    __tablename__ = 'setting'

    id = Column(INTEGER, Sequence('article_aid_seq', start=1, increment=1), primary_key=True)
    reminder_ahead_of_time = Column(Integer)


# 数据库连接
engine = create_engine('sqlite:///energyx.db')
Session = sessionmaker(bind=engine)


def init_db():
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Tables created.")
