# Unified Research Version-Space Fixture

Run the exact 5-dimensional analysis:

```bash
python -m tools.research_version_space analyze \
  --model examples/research_version_space/five_dimensions.json \
  --out /tmp/research-version-space.json
```

The fixture enumerates all 32 data/model/search/execution/universe worlds and all
64 evidence-channel subsets.

With no evidence, the controlled metric ranges from 20 to 150. The minimum-cost
architecture meeting the registered maximum width of 40 is:

```text
pitDataReceipt
searchLedger
cost = 4
range = [20, 55]
```

Full point identification is cheaper through the integrated
`unifiedResearchBundle` at cost 8 than through all five narrow receipts at cost
9. Exact Shapley values allocate the 130-point baseline-to-all-alternative
change across the five dimensions while splitting interaction terms fairly.

All values are controlled inputs. They illustrate the calculus and exact solver;
they are not empirical estimates of real revision or selection bias.
