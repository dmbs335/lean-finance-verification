# Preregistered Epistemic-Crowding Event Study

This controlled benchmark translates the epistemic-liquidation mechanism into a falsifiable empirical protocol.

For each strategy exposed to a failed evidence domain, the plan preregisters one unexposed control matched on four conventional dimensions:

- return behavior;
- factor exposure;
- holdings overlap;
- liquidity characteristics.

The plan also fixes the event time, matching tolerance, pre-trend tolerance, and minimum event-window difference-in-differences before analysis.

For each pair:

```text
pretrend DID = (treated pre - treated baseline)
             - (control pre - control baseline)

event DID    = (treated post - treated pre)
             - (control post - control pre)
```

A bounded certificate is emitted only when registration precedes the event, every treated strategy uses the failed domain, every control does not, all conventional distances remain within tolerance, all pretrend DIDs are within tolerance, and the aggregate event DID exceeds the registered threshold.

## Controlled result

Three matched pairs pass a 500 bps conventional-distance threshold and a 50 bps absolute pretrend-DID threshold. Their event DIDs sum to 2,550 bps, an integer average of 850 bps, exceeding the preregistered 700 bps threshold.

The fixture is synthetic. It demonstrates a fail-closed analysis contract, not evidence that a real vendor shock caused real fund outflows. A real study additionally requires dated methodology incidents, trustworthy strategy dependencies, flows or position changes, and defensible matching/parallel-trend assumptions.
