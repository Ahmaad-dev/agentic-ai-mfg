"""UI: eigener Session-Titel + weiches Ausblenden statt Löschen

Zwei Spalten auf `sessions`:

* ``title`` — bisher wurde der Titel IMMER aus der ersten Nutzernachricht abgeleitet.
  Umbenennen war damit unmöglich. Die Spalte ist nullbar; solange sie leer ist, gilt
  weiterhin der abgeleitete Titel. Damit ändert sich für alle bestehenden Sessions nichts.

* ``hidden_at`` — der Grund für die ganze Migration. Ein echtes DELETE auf `sessions`
  würde per ``cascade="all, delete-orphan"`` auch `messages` UND `agent_runs` mitnehmen.
  `agent_runs` ist die Quelle für Tokens, Kosten und Validierungszahlen im Management
  Dashboard: eine gelöschte Unterhaltung würde also rückwirkend die Kennzahlen des
  Projekts verändern, ohne dass es jemand merkt. Deshalb wird nur ausgeblendet. Das macht
  „Rückgängig" nebenbei ehrlich — es wird nichts wiederhergestellt, sondern nur wieder
  eingeblendet.

Revision ID: 9b1e40c7d2a3
Revises: 57dbefe2d996
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9b1e40c7d2a3"
down_revision: Union[str, Sequence[str], None] = "57dbefe2d996"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("sessions", sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "hidden_at")
    op.drop_column("sessions", "title")
