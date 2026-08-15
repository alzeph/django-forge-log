from django.dispatch import Signal

# Envoyé après qu'une entrée ActionLog a été remise au writer configuré
# (avant écriture effective si le backend est asynchrone/différé).
# Fournit `entry` (forge_log.schemas.ActionLogEntry) en kwarg.
action_logged = Signal()
