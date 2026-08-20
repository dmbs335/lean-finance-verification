# Causal Strategy Interaction Kernel

This module formalizes the minimum proof surface for a causal strategy
interaction graph.

## Direction convention

`kernel.effect target source context` is the local causal response of the
**target** strategy's selected fitness metric to an increase in the
**source** treatment.

The context records:

- horizon;
- market regime;
- fitness metric;
- treatment type (`capitalStock`, `orderFlow`, or `adoption`);
- shock provenance.

Consequently, a single context-free scalar is not assumed to exist. The theorem
`no_context_free_effect_of_context_dependence` makes this explicit.

## Verified results

The current Lean layer proves:

1. competition and mutualism are symmetric classifications;
2. predation is asymmetric under strict signs;
3. mutualism and competition cannot hold simultaneously in one context;
4. a genome-fixed scale intervention preserves the strategy genome and
   sequential scale changes compose additively;
5. a nonzero null direction of the linear first-stage observation map is a
   constructive certificate that an affected kernel coordinate is not point
   identified;
6. a relevant scalar IV moment equation identifies at most one edge effect;
7. a zero first stage with a zero reduced form fits every scalar effect;
8. a proof-carrying edge certificate binds the estimated IV effect to a
   directed kernel coordinate and exposes interval ordering, relevance, moment
   fit, and explicit evidence for exogeneity, exclusion, no anticipation,
   genome stability, exposure validity, and market clearing;
9. a strictly positive lower bound implies a positive kernel effect and a
   certified opportunity-creation edge, while a strictly negative upper bound
   implies a negative kernel effect.

## Trust boundary

Lean verifies implications from encoded assumptions. It does not prove that an
empirical instrument is truly exogenous, that exclusion holds in the real
market, or that a holdings-based exposure map observes all derivatives and
synthetic positions. Those claims must enter as explicit evidence in the edge
certificate and remain auditable outside the kernel.

The rank result is deliberately constructive. Rather than asserting a numerical
matrix rank computed by an unverified external routine, it accepts a null-space
witness and proves that the witness creates observational equivalence while
changing the claimed interaction coordinate.
