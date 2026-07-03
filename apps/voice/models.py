"""No persistent models for the voice app.

Audio bytes are in-memory only (project-context R9) and voice
preferences live on `apps.accounts.EntrepreneurProfile` (E04-S07),
so this app owns no tables of its own.
"""
