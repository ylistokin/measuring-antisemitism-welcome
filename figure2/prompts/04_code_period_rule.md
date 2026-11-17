# Prompt 4: apply the modern-period rule

Determine whether the study contains at least one empirical observation after 1960.

Rules:

1. Include the paper when any analyzed observation is dated 1961 or later.
2. A study may begin before 1960. Do not exclude a mixed historical-modern panel solely because its first observation predates 1961.
3. Historical explanatory variables paired with post-1960 outcomes qualify because the study analyzes post-1960 observations.
4. Exclude a study when all analyzed observations end in 1960 or earlier.
5. Publication year is not the observation year.
6. Background history, citations, or dates mentioned only for context do not define the observation window.
7. If the title and abstract do not establish the window, request full-text review.

Return JSON with `earliest_observation_year`, `latest_observation_year`, `includes_post_1960_observation`, `evidence`, `confidence`, and `needs_full_text`. Use null for unknown years. Never invent a year.
