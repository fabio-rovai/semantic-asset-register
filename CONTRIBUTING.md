# Contributing

## If you publish an asset that this register assesses

You have a standing right of reply, and using it is the fastest way to change a
result.

Open an issue with the `publisher-response` label. Three kinds of response are
all welcome, and all are treated the same way:

1. **The finding is wrong.** Show the retrieval we got wrong, or the check we
   implemented wrong. If you are right, the check is fixed and the register is
   re-run. Findings are never quietly edited; corrections are recorded in
   `docs/CORRECTIONS.md` with the date and what changed.
2. **The finding is right and you have fixed it.** Say so and the register will
   pick the fix up on the next run. Snapshots are hashed, so an improvement is
   visible as a changed hash and a changed outcome.
3. **The check does not apply to you.** This is the response we most want. If a
   check is being applied to an asset whose kind or purpose makes it
   meaningless, that is a defect in the catalogue, not in your asset, and the
   fix is a narrower `sar:appliesToKind` or an outright removal.

We do not require you to agree with a conventional finding. Conventional checks
record a departure from community practice, not a breach of any rule you are
bound by.

## If you want to add a check

Every check in the catalogue must carry five things, and a pull request without
them will be asked for them:

- `sar:derivesFrom` pointing at a real, linkable authority
- `sar:citation` naming the specific clause, section or rule inside that authority
- `sar:normativity`, either `sar:Normative` or `sar:Conventional`
- `sar:severity`
- `sar:appliesToKind` listing every asset kind the check is meaningful for

A check is normative only if failing it violates a published specification. If
the only support for a check is that most practitioners do it this way, it is
conventional. Reclassifying convention as standard is the failure mode this
register exists to avoid, and pull requests that do it will be rejected on that
ground alone.

Checks must be implementable without a licensed dependency, and must degrade to
`cantTell` rather than to `failed` when they cannot be evaluated.

## If you want to add an asset

Add it to `data/seed_assets.json` and run `pipeline/probe.py`. An asset that
cannot be retrieved as RDF is still worth recording: put it in
`sought_but_not_rdf` with what you actually observed and the date. A register
that only lists what worked is not a register of the estate.

## Running the pipeline

```bash
pip install -r requirements.txt
./pipeline/setup.sh          # fetches ROBOT, checks for java
python3 pipeline/probe.py    # retrieval, writes results/probe_results.json
python3 pipeline/assess.py   # checks, writes results/findings.ttl and .csv
```

The probe stage hits live government infrastructure. It sleeps between requests
and identifies itself in the User-Agent. Please keep both of those properties.
