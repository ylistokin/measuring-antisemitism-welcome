# Prompt 2: code subject focus symmetrically

You are coding one research article for a comparative census. Apply the same target-plus-discriminatory-process standard to anti-Black racism and antisemitism.

Definitions:

- Anti-Black racism includes prejudice, stereotyping, unequal treatment, racial hierarchy, segregation, anti-Black violence, or discriminatory institutions directed at Black people. Studying Black people or a Black-white outcome gap is not sufficient by itself.
- Antisemitism includes prejudice, stereotyping, unequal treatment, exclusion, persecution, violence, or discriminatory institutions directed at Jews as Jews. Jewish identity, Israel, Holocaust memory, or Jewish outcomes are not sufficient by themselves.

Assign exactly one class:

- A: the target group and discriminatory process define the research question or central analysis.
- B: the subject receives substantial analysis inside a broader inquiry but is not the primary focus.
- C: incidental, identity-only, comparison-only, insufficiently supported by metadata, or non-substantive.

Return JSON with `subject`, `class`, `evidence`, `ambiguity`, and `needs_full_text`. Quote no more than a short phrase from the source. If evidence is insufficient, choose C and set `needs_full_text` to true rather than guessing.
