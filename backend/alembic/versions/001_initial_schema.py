"""Initial schema — TitoliEngine database.

Revision ID: 001
Revises: None
Create Date: 2026-03-27

Tutte le tabelle dal blueprint sezione 2.
Tutti gli importi NUMERIC(20,10) per precisione assoluta.
Include trigger check_journal_balance() per quadratura dare=avere.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── Studios ───────────────────────────────────────────────
    op.create_table(
        "studios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_code", sa.String(16), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.Text),
        sa.Column("subscription_tier", sa.String(50), server_default="standard"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Clients ───────────────────────────────────────────────
    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("studio_id", UUID(as_uuid=True), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_code", sa.String(16), nullable=False),
        sa.Column("legal_form", sa.String(50), nullable=False),
        sa.Column("fiscal_year_start", sa.Date, server_default="2025-01-01"),
        sa.Column("fiscal_year_end", sa.Date, server_default="2025-12-31"),
        sa.Column("balance_type", sa.String(20), nullable=False, server_default="ordinario"),
        sa.Column("valuation_method", sa.String(30), nullable=False, server_default="costo_ammortizzato"),
        sa.Column("cost_method", sa.String(20), nullable=False, server_default="costo_specifico"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("studio_id", "tax_code", name="uq_client_studio_tax_code"),
    )

    # ── Users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("studio_id", UUID(as_uuid=True), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Chart of Accounts ─────────────────────────────────────
    op.create_table(
        "chart_of_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(20), nullable=False),
        sa.Column("parent_code", sa.String(20)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("client_id", "code", name="uq_chart_of_accounts_client_code"),
    )

    # ── Securities ────────────────────────────────────────────
    op.create_table(
        "securities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("isin", sa.String(12), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("security_type", sa.String(50), nullable=False),
        sa.Column("issuer", sa.String(255)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("nominal_value", sa.Numeric(20, 10), nullable=False, server_default="100"),
        sa.Column("coupon_rate", sa.Numeric(10, 6)),
        sa.Column("coupon_frequency", sa.Integer),
        sa.Column("coupon_dates", JSONB),
        sa.Column("coupon_day_count", sa.String(20), server_default="ACT/ACT"),
        sa.Column("maturity_date", sa.Date),
        sa.Column("issue_date", sa.Date),
        sa.Column("issue_price", sa.Numeric(20, 10)),
        sa.Column("tax_regime", sa.String(30), nullable=False, server_default="standard"),
        sa.Column("withholding_rate", sa.Numeric(5, 4), nullable=False, server_default="0.2600"),
        sa.Column("is_listed", sa.Boolean, server_default="true"),
        sa.Column("market", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_securities_isin", "securities", ["isin"])

    # ── Portfolio Positions ───────────────────────────────────
    op.create_table(
        "portfolio_positions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("security_id", UUID(as_uuid=True), sa.ForeignKey("securities.id"), nullable=False),
        sa.Column("classification", sa.String(20), nullable=False, server_default="current"),
        sa.Column("quantity", sa.Numeric(20, 10), nullable=False, server_default="0"),
        sa.Column("book_value", sa.Numeric(20, 10), nullable=False, server_default="0"),
        sa.Column("book_value_per_unit", sa.Numeric(20, 10)),
        sa.Column("amortized_cost", sa.Numeric(20, 10)),
        sa.Column("effective_interest_rate", sa.Numeric(15, 10)),
        sa.Column("acquisition_date", sa.Date),
        sa.Column("acquisition_price", sa.Numeric(20, 10)),
        sa.Column("acquisition_cost_total", sa.Numeric(20, 10)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("client_id", "security_id", "classification", name="uq_position_client_security_class"),
    )

    # ── Portfolio Lots ────────────────────────────────────────
    op.create_table(
        "portfolio_lots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("position_id", UUID(as_uuid=True), sa.ForeignKey("portfolio_positions.id"), nullable=False),
        sa.Column("lot_date", sa.Date, nullable=False),
        sa.Column("lot_quantity", sa.Numeric(20, 10), nullable=False),
        sa.Column("remaining_quantity", sa.Numeric(20, 10), nullable=False),
        sa.Column("unit_cost", sa.Numeric(20, 10), nullable=False),
        sa.Column("total_cost", sa.Numeric(20, 10), nullable=False),
        sa.Column("transaction_costs", sa.Numeric(20, 10), server_default="0"),
        sa.Column("effective_rate", sa.Numeric(15, 10)),
        sa.Column("amortized_cost", sa.Numeric(20, 10)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Documents ─────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("bank_name", sa.String(100)),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("parsing_status", sa.String(20), server_default="pending"),
        sa.Column("parsed_data", JSONB),
        sa.Column("parsing_confidence", sa.Numeric(5, 4)),
        sa.Column("parsing_errors", JSONB),
        sa.Column("document_date", sa.Date),
        sa.Column("bank_reference", sa.String(100)),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )

    # ── Transactions ──────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("security_id", UUID(as_uuid=True), sa.ForeignKey("securities.id"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id")),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("trade_date", sa.Date, nullable=False),
        sa.Column("settlement_date", sa.Date, nullable=False),
        sa.Column("quantity", sa.Numeric(20, 10), nullable=False),
        sa.Column("unit_price", sa.Numeric(20, 10), nullable=False),
        sa.Column("gross_amount", sa.Numeric(20, 10), nullable=False),
        sa.Column("accrued_interest", sa.Numeric(20, 10), server_default="0"),
        sa.Column("tel_quel_amount", sa.Numeric(20, 10), nullable=False),
        sa.Column("bank_commission", sa.Numeric(20, 10), server_default="0"),
        sa.Column("stamp_duty", sa.Numeric(20, 10), server_default="0"),
        sa.Column("tobin_tax", sa.Numeric(20, 10), server_default="0"),
        sa.Column("other_costs", sa.Numeric(20, 10), server_default="0"),
        sa.Column("total_transaction_costs", sa.Numeric(20, 10), server_default="0"),
        sa.Column("net_settlement_amount", sa.Numeric(20, 10), nullable=False),
        sa.Column("coupon_gross", sa.Numeric(20, 10)),
        sa.Column("withholding_tax", sa.Numeric(20, 10)),
        sa.Column("coupon_net", sa.Numeric(20, 10)),
        sa.Column("gain_loss", sa.Numeric(20, 10)),
        sa.Column("gain_loss_type", sa.String(20)),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("exchange_rate", sa.Numeric(15, 8), server_default="1"),
        sa.Column("amount_eur", sa.Numeric(20, 10)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("parsing_confidence", sa.Numeric(5, 4)),
        sa.Column("parsing_warnings", JSONB),
        sa.Column("manually_verified", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_transactions_client", "transactions", ["client_id"])
    op.create_index("idx_transactions_security", "transactions", ["security_id"])
    op.create_index("idx_transactions_date", "transactions", ["trade_date"])
    op.create_index("idx_transactions_status", "transactions", ["status"])

    # ── Journal Entries ───────────────────────────────────────
    op.create_table(
        "journal_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("transaction_id", UUID(as_uuid=True), sa.ForeignKey("transactions.id")),
        sa.Column("entry_date", sa.Date, nullable=False),
        sa.Column("competence_date", sa.Date, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("entry_type", sa.String(50), nullable=False),
        sa.Column("document_ref", sa.String(100)),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("posted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("generation_rule", sa.String(100)),
        sa.Column("generation_params", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Journal Lines ─────────────────────────────────────────
    op.create_table(
        "journal_lines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entry_id", UUID(as_uuid=True), sa.ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("debit", sa.Numeric(20, 10), server_default="0"),
        sa.Column("credit", sa.Numeric(20, 10), server_default="0"),
        sa.Column("description", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "(debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0)",
            name="chk_debit_or_credit",
        ),
    )
    op.create_index("idx_journal_lines_entry", "journal_lines", ["entry_id"])

    # ── Valuations ────────────────────────────────────────────
    op.create_table(
        "valuations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("position_id", UUID(as_uuid=True), sa.ForeignKey("portfolio_positions.id"), nullable=False),
        sa.Column("valuation_date", sa.Date, nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("book_value", sa.Numeric(20, 10), nullable=False),
        sa.Column("market_price", sa.Numeric(20, 10)),
        sa.Column("market_value", sa.Numeric(20, 10)),
        sa.Column("fair_value", sa.Numeric(20, 10)),
        sa.Column("valuation_result", sa.String(30), nullable=False),
        sa.Column("impairment_amount", sa.Numeric(20, 10), server_default="0"),
        sa.Column("reversal_amount", sa.Numeric(20, 10), server_default="0"),
        sa.Column("amortized_cost_value", sa.Numeric(20, 10)),
        sa.Column("amortization_for_period", sa.Numeric(20, 10)),
        sa.Column("is_durable_loss", sa.Boolean, server_default="false"),
        sa.Column("justification", sa.Text),
        sa.Column("journal_entry_id", UUID(as_uuid=True), sa.ForeignKey("journal_entries.id")),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Market Prices ─────────────────────────────────────────
    op.create_table(
        "market_prices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("security_id", UUID(as_uuid=True), sa.ForeignKey("securities.id"), nullable=False),
        sa.Column("price_date", sa.Date, nullable=False),
        sa.Column("close_price", sa.Numeric(20, 10), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("security_id", "price_date", "source", name="uq_market_price_security_date_source"),
    )

    # ── Audit Log ─────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_values", JSONB),
        sa.Column("new_values", JSONB),
        sa.Column("computation_rule", sa.String(200)),
        sa.Column("computation_params", JSONB),
        sa.Column("computation_result", JSONB),
        sa.Column("ip_address", INET),
        sa.Column("user_agent", sa.Text),
    )
    op.create_index("idx_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("idx_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("idx_audit_log_client", "audit_log", ["client_id"])

    # ── Trigger: check_journal_balance() ──────────────────────
    # VINCOLO CRITICO: ogni journal_entry deve quadrare (dare = avere)
    # Tolleranza ZERO — nessun arrotondamento ammesso
    op.execute("""
        CREATE OR REPLACE FUNCTION check_journal_balance()
        RETURNS TRIGGER AS $$
        DECLARE
            total_debit NUMERIC(20,10);
            total_credit NUMERIC(20,10);
        BEGIN
            SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
            INTO total_debit, total_credit
            FROM journal_lines
            WHERE entry_id = NEW.entry_id;

            -- Tolleranza ZERO: dare deve essere ESATTAMENTE uguale ad avere
            IF total_debit != total_credit THEN
                RAISE EXCEPTION 'ERRORE CRITICO: Scrittura % non quadra. Dare=% Avere=%',
                    NEW.entry_id, total_debit, total_credit;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_check_journal_balance
        AFTER INSERT ON journal_lines
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION check_journal_balance();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_check_journal_balance ON journal_lines")
    op.execute("DROP FUNCTION IF EXISTS check_journal_balance()")

    op.drop_table("audit_log")
    op.drop_table("market_prices")
    op.drop_table("valuations")
    op.drop_table("journal_lines")
    op.drop_table("journal_entries")
    op.drop_table("transactions")
    op.drop_table("documents")
    op.drop_table("portfolio_lots")
    op.drop_table("portfolio_positions")
    op.drop_table("securities")
    op.drop_table("chart_of_accounts")
    op.drop_table("users")
    op.drop_table("clients")
    op.drop_table("studios")
