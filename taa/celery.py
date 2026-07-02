"""Celery app placeholder for TAA.

Real wiring (broker URL, autodiscover_tasks, Beat schedule) lands in
E00-S02 (Docker/Redis) and E02-S06 (weekly lex.uz sync). Kept as a
minimal stub so imports don't break future stories.
"""
# Celery deliberately not imported yet — dep lands in E00-S02.
# Placeholder module exists to lock the import path (`taa.celery`).
