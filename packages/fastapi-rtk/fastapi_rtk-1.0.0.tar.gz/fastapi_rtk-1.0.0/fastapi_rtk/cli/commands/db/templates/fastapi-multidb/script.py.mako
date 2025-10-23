<%!
import re

%>"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import fastapi_rtk.types
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade(engine_name: str) -> None:
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name: str) -> None:
    globals()["downgrade_%s" % engine_name]()

<%
    from fastapi_rtk import Setting
    from fastapi_rtk.const import DEFAULT_METADATA_KEY
    bind_names = []

    MAIN_DATABASE = Setting.SQLALCHEMY_DATABASE_URI
    BINDS = Setting.SQLALCHEMY_BINDS
    BINDS = list(BINDS.keys())

    db_names = [DEFAULT_METADATA_KEY] + BINDS
%>

## generate an "upgrade_<xyz>() / downgrade_<xyz>()" function
## for each database name in the ini file.

% for db_name in db_names:

def upgrade_${db_name}() -> None:
    ${context.get("%s_upgrades" % db_name, "pass")}


def downgrade_${db_name}() -> None:
    ${context.get("%s_downgrades" % db_name, "pass")}

% endfor
