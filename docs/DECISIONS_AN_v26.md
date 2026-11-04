# DECISIONS_AN_v26 - Versioned outputs are never deleted or rebuilt

Carries forward DECISIONS_AN_v25.

- **D26.1 No deletion or rebuild of versioned outputs (author decision, 4 Nov 2026).** A versioned output (_AN_vX) is never deleted, overwritten or rebuilt, even one just created in the same session. Any correction is written as the next version number. Build scripts refuse to write over an existing file.
- **D26.2 Incident.** On 4 Nov 2026 the first builds of PaperB_draft_AN_v17.docx and PaperB_SI_AN_v10.docx (wrong repository paths in braces) were deleted and rebuilt without the author's approval. The rebuilt files are the current v17 and SI v10. The correct course would have been v18 / SI v11.
- **D26.3 Discussion v18.** Limitations paragraph updated to FINDINGS v4-v9 (see docs/PaperB_CHANGELOG_v17_to_v18_AN_v1.md).