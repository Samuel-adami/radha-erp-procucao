from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey

Base = declarative_base()


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True)
    agency = Column(String)
    account_number = Column(String)
    initial_balance = Column(Float)
    bank_id = Column(Integer, ForeignKey("banks.id"))


class AccountGroup(Base):
    __tablename__ = "account_groups"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)
    type = Column(String)  # RECEITA or DESPESA
    parent_id = Column(Integer, ForeignKey("account_groups.id"))


class Payable(Base):
    __tablename__ = "payables"

    id = Column(Integer, primary_key=True)
    description = Column(String)
    amount = Column(Float)
    due_date = Column(String)
    payment_date = Column(String)
    status = Column(String)
    supplier_id = Column(Integer)
    account_group_id = Column(Integer, ForeignKey("account_groups.id"))
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"))


class Receivable(Base):
    __tablename__ = "receivables"

    id = Column(Integer, primary_key=True)
    description = Column(String)
    amount = Column(Float)
    due_date = Column(String)
    payment_date = Column(String)
    status = Column(String)
    customer_id = Column(Integer)
    account_group_id = Column(Integer, ForeignKey("account_groups.id"))
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"))


class FiscalConfig(Base):
    __tablename__ = "fiscal_config"

    id = Column(Integer, primary_key=True)
    cfop = Column(String)
    cst = Column(String)
    ncm = Column(String)
    default_tax_rate = Column(Float)
