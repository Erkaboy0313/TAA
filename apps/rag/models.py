"""No models in the RAG app — chunks live in ``apps.corpus`` (architecture §3).

Keeping this module empty (rather than deleting it) lets Django's app
loader treat ``apps.rag`` as a first-class app and keeps future model
additions co-located with the rest of the pipeline.
"""
