# Prompt 3: code empirical status

Determine whether the article reports original empirical analysis.

Count as Empirical: original quantitative, qualitative, experimental, computational, archival, historical-data, administrative-data, interview, ethnographic, or survey analysis.

Count as Nonempirical: theory, conceptual argument, commentary, agenda-setting essay, narrative review, or systematic review/meta-analysis without original analysis of primary observations.

Return JSON with `empirical_status`, `method`, `data_description`, `evidence`, and `needs_full_text`. Do not infer empirical status merely from the article's subject or publication venue.
