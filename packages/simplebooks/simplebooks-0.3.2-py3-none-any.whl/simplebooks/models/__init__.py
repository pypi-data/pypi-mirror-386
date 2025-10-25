from .Account import Account
from .AccountCategory import AccountCategory
from .AccountType import AccountType
from .ArchivedEntry import ArchivedEntry
from .ArchivedTransaction import ArchivedTransaction
from .Currency import Currency
from .Customer import Customer
from .Entry import Entry
from .EntryType import EntryType
from .Identity import Identity
from .Ledger import Ledger
from .LedgerType import LedgerType
from .Statement import Statement
from .Transaction import Transaction
from .Vendor import Vendor
from sqloquent import contains, within, has_many, belongs_to
from typing import Callable
import sqloquent.tools


Identity.ledgers = has_many(Identity, Ledger, 'identity_id')
Ledger.owner = belongs_to(Ledger, Identity, 'identity_id')

Ledger.currency = belongs_to(Ledger, Currency, 'currency_id')
Currency.ledgers = has_many(Currency, Ledger, 'currency_id')

Ledger.accounts = has_many(Ledger, Account, 'ledger_id')
Account.ledger = belongs_to(Account, Ledger, 'ledger_id')

Account.children = has_many(Account, Account, 'parent_id')
Account.parent = belongs_to(Account, Account, 'parent_id')

Account.category = belongs_to(Account, AccountCategory, 'category_id')
AccountCategory.accounts = has_many(AccountCategory, Account, 'category_id')

Account.entries = has_many(Account, Entry, 'account_id')
Entry.account = belongs_to(Entry, Account, 'account_id')

Entry.transactions = within(Entry, Transaction, 'entry_ids')
Transaction.entries = contains(Transaction, Entry, 'entry_ids')

Transaction.ledgers = contains(Transaction, Ledger, 'ledger_ids')
Ledger.transactions = within(Ledger, Transaction, 'ledger_ids')

Statement.ledger = belongs_to(Statement, Ledger, 'ledger_id')
Ledger.statements = has_many(Ledger, Statement, 'ledger_id')

Statement.transactions = contains(Statement, Transaction, 'tx_ids')
Transaction.statements = within(Transaction, Statement, 'tx_ids')

Statement.archived_transactions = contains(Statement, ArchivedTransaction, 'tx_ids')
ArchivedTransaction.statements = within(ArchivedTransaction, Statement, 'tx_ids')

ArchivedEntry.transactions = within(ArchivedEntry, ArchivedTransaction, 'entry_ids')
ArchivedTransaction.entries = contains(ArchivedTransaction, ArchivedEntry, 'entry_ids')

ArchivedEntry.account = belongs_to(ArchivedEntry, Account, 'account_id')
Account.archived_entries = has_many(Account, ArchivedEntry, 'account_id')

ArchivedTransaction.ledgers = contains(ArchivedTransaction, Ledger, 'ledger_ids')
Ledger.archived_transactions = within(Ledger, ArchivedTransaction, 'ledger_ids')


def set_connection_info(db_file_path: str):
    """Set the connection info for all models to use the specified
        sqlite3 database file path.
    """
    Account.connection_info = db_file_path
    AccountCategory.connection_info = db_file_path
    ArchivedEntry.connection_info = db_file_path
    ArchivedTransaction.connection_info = db_file_path
    Currency.connection_info = db_file_path
    Customer.connection_info = db_file_path
    Entry.connection_info = db_file_path
    Identity.connection_info = db_file_path
    Ledger.connection_info = db_file_path
    Statement.connection_info = db_file_path
    Transaction.connection_info = db_file_path
    Vendor.connection_info = db_file_path

def get_migrations() -> dict[str, str]:
    """Returns a dict mapping model names to migration file content strs."""
    models = [
        Account,
        AccountCategory,
        ArchivedEntry,
        ArchivedTransaction,
        Currency,
        Customer,
        Entry,
        Identity,
        Ledger,
        Statement,
        Transaction,
        Vendor,
    ]
    migrations = {}
    for model in models:
        migrations[model.__name__] = sqloquent.tools.make_migration_from_model(model)
    return migrations

def publish_migrations(
        migration_folder_path: str,
        migration_callback: Callable[[str, str], str] = None
    ):
    """Writes migration files for the models. If a migration callback is
        provided, it will be used to modify the migration file contents.
        The migration callback will be called with the model name and
        the migration file contents, and whatever it returns will be
        used as the migration file contents.
    """
    sqloquent.tools.publish_migrations(migration_folder_path)
    migrations = get_migrations()
    for name, m in migrations.items():
        m2 = migration_callback(name, m) if migration_callback else m
        m = m2 if type(m2) is str and len(m2) > 0 else m
        with open(f'{migration_folder_path}/create_{name}.py', 'w') as f:
            f.write(m)

def automigrate(migration_folder_path: str, db_file_path: str):
    """Executes the sqloquent automigrate tool."""
    sqloquent.tools.automigrate(migration_folder_path, db_file_path)

