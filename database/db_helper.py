from sqlalchemy import desc

from database.models import Session, init_db
from .models import FuturesProductBean, FuturesPositionBean,AccountBean


class DBHelper:
    def __init__(self):
        init_db()
        self.session = Session()

    def update_account_bean(self, account_bean):
        try:
            existing_account = self.session.query(AccountBean).filter_by(id=account_bean.id).first()
            if existing_account:
                # 更新现有记录
                existing_account.dynamic_equity = account_bean.dynamic_equity
                # 更新其他需要更新的字段
                self.session.commit()
                print("Account bean updated successfully.")
            else:
                print("Account bean not found.")
        except Exception as e:
            self.session.rollback()
            print(f"Error occurred: {e}")

    def get_account_bean(self):
        return self.session.query(AccountBean).first()

    def is_account_table_empty(self):
        return self.session.query(AccountBean).count() == 0

    def insert_default_account(self):
        account_bean = AccountBean()
        account_bean.dynamic_equity = 0
        self.session.add(account_bean)
        self.session.commit()

    def add_futures_position(self, position_bean):
        self.session.add(position_bean)
        self.session.commit()

    def delete_futures_position(self, position):
        try:
            self.session.delete(position)
            self.session.commit()
        except Exception as e:
            self.session.rollback()

    def load_all_futures_position(self):
        return self.session.query(FuturesPositionBean).order_by(desc(FuturesPositionBean.profit_loss_amount)).all()

    def delete_all_futures_position(self):
        self.session.query(FuturesPositionBean).delete()
        self.session.commit()

    def add_futures_product(self, pin_yin, trading_product, trading_code, trading_units, minimum_price_change, margin_ratio):
        new_product = FuturesProductBean(
            pin_yin=pin_yin,
            trading_product=trading_product,
            trading_code=trading_code,
            trading_units=trading_units,
            minimum_price_change=minimum_price_change,
            margin_ratio=margin_ratio
        )
        self.session.add(new_product)
        self.session.commit()

    def get_futures_product(self, product_id):
        return self.session.query(FuturesProductBean).filter_by(id=product_id).first()

    def update_futures_product(self, product_id, **kwargs):
        product = self.session.query(FuturesProductBean).filter_by(id=product_id).first()
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            self.session.commit()

    def delete_futures_product(self, product_id):
        product = self.session.query(FuturesProductBean).filter_by(id=product_id).first()
        if product:
            self.session.delete(product)
            self.session.commit()

    def dict_to_futures_product_bean(self, data):
        return FuturesProductBean(
            pin_yin=data['pinYin'],
            trading_product=data['tradingProduct'],
            trading_code=data['tradingCode'],
            trading_units=float(data['tradingUnits']),
            minimum_price_change=float(data['minimumPriceChange']),
            margin_ratio=float(data['marginRatio'])
        )

    def insert_future_list(self, future_list):
        for data in future_list:
            futures_product = self.dict_to_futures_product_bean(data)
            self.session.add(futures_product)
        self.session.commit()

    def is_futures_products_table_empty(self):
        return self.session.query(FuturesProductBean).count() == 0

    def get_all_futures_products(self):
        return self.session.query(FuturesProductBean).all()
