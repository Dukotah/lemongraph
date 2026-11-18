# LANE-REPORT - lemongraph (lane 5)

Branches on `origin` (github.com/Dukotah/lemongraph):

- `fix/modern-packaging` - one commit on top of `upstream/lg-lite`, upstream PR candidate
- `lane/ledger-graph` - fork-only, branched off `fix/modern-packaging`

## 1. Upstream contribution rules

- There is no CONTRIBUTING.md, CODE_OF_CONDUCT or CI on either `master` or `lg-lite`.
- Active development is on **`lg-lite`**, not `master`. `master` was last touched 2022-09-07; the
  maintainer (`NSA-LGDev2`) said in #25 that "`lg-lite` will get pushed to master at some point", merged
  #35 into `lg-lite` on 2026-04-30, and 7 of the 8 queued PRs (#37-#43) target `lg-lite`. So the PR targets
  `lg-lite`.
- Observed convention: small single-purpose PRs, tests go into the single `test.py` (unittest),
  `requirements.txt` is the single source of dependencies (`setup.py` reads it), version lives in
  `LemonGraph/version.py`, changes are noted in `CHANGELOG.md` by the maintainer at release time.

## 2. What changed and why

### Recon correction

The lane brief was written against `master`, where `lg_cffi_setup.py` imports `distutils` and `setup.py`
pins `cffi<1.12`, `msgpack<0.6` etc. On `lg-lite` the maintainer has already removed `lg_cffi_setup.py`,
dropped zlib (crc32 is compiled in), handled the `pkg_resources` deprecation, and moved deps fetching
into `deps/*.ext` + `make deps`. `lg-lite` builds and passes `test.py` on 3.12 as-is. What is still broken
on `lg-lite` is **Python 3.13+**: `requirements.txt` caps `cffi<1.17`, and cffi 1.16 does not compile on 3.13.
`master` is broken on both 3.12 and 3.13 (cffi<1.12), but nobody is merging to `master`, so fixing it there
would be wasted effort.

### `fix/modern-packaging` (1 commit, 4 files, +36/-12)

- `requirements.txt`: keep every lower bound, raise upper bounds to the next major
  (`cffi<3`, `lazy<2`, `msgpack<2`, `python-dateutil<3`). No code change, no behaviour change; `test.py`
  is green with the newest releases (cffi 2.1.1, msgpack 1.2.4, dateutil 2.9.0.post0).
- `pyproject.toml`: `[build-system]` only - `setuptools` + `cffi` as PEP 517/518 build requirements, so
  isolated builds no longer depend on the deprecated `setup_requires` path. `setup.py` is untouched: it is
  load-bearing (cffi_modules, `make deps` wrapper around build_ext/install/sdist).
- `.github/workflows/ci.yml`: ubuntu-24.04, Python 3.9-3.13, `pip install -e .` then `python test.py`.
- `README.md`: the "Python setup" subsection's CentOS 6/7 and Ubuntu 15.04-20.04 bullets replaced with an
  Ubuntu 22.04/24.04 apt line, a note that `make deps` needs network, and `pip install .` /
  `pip install -e .` + `python test.py`. Rest of README untouched.

Not changed, deliberately: `collections.Hashable` in `serializer.py` (that is #41), `server/__init__.py`
(#37/#38), `test.py` (every queued PR touches it), and the `make deps` network fetch of LMDB + d3/
svg-crowbar/json-view (curl from d3js.org, nytimes.github.io and plain-http pgrabovets.github.io). The build
is therefore **not offline-safe**: with no network `deps/js.ext` fails under `set -e`. Pre-populating
`deps/lmdb` and `deps/js/` is the only workaround today; vendoring or making the JS optional would be a
separate upstream discussion (the `http://` json-view URL is also worth raising).

### `lane/ledger-graph` (fork-only)

- `LemonGraph/nx.py`: generic `to_networkx(txn, graph_class=None, node_type=None, edge_type=None,
  beforeID=None)`. Nodes keyed by LemonGraph ID with `type`, `value` and properties; edges keyed by edge ID
  in a MultiDiGraph; graph properties in `G.graph`; supports historical views via `beforeID`. NetworkX is
  imported lazily, not added as a dependency. This answers upstream issue #1 and can be offered upstream on
  its own (one file + the `TestNetworkX` test case).
- `test.py`: `TestNetworkX` (skips if networkx is absent).
- `examples/ledger_graph/`: `ledger_graph.py` (loader + 5 queries + NetworkX analysis), a copy of
  `LEDGER.json` from Dukotah/cicada3301 @ `6b94529`, and a README with the real output pasted.
  350 rows -> 545 nodes / 916 edges in under a second.

## 3. Evidence

Breakage proof (`uv venv -p X && uv pip install -e .`, clean clones):

```
master  py3.12  c/call_python.c:20:30: error: invalid use of incomplete typedef 'PyInterpreterState'   (cffi<1.12)   install exit=1
master  py3.13  same error                                                                                            install exit=1
lg-lite py3.12  cffi==1.16.0 msgpack==1.0.8 python-dateutil==2.8.2 ... Ran 32 tests in 2.423s OK
lg-lite py3.13  src/c/_cffi_backend.c:6121:9: error: implicit declaration of function '_PyErr_WriteUnraisableMsg'   install exit=1
```

After the fix (`fix/modern-packaging`, same procedure):

```
py3.9   cffi==2.0.0 msgpack==1.1.2 python-dateutil==2.9.0.post0   install exit=0  Ran 32 tests in 4.238s  OK
py3.12  cffi==2.1.1 msgpack==1.2.4 python-dateutil==2.9.0.post0   install exit=0  Ran 32 tests in 2.072s  OK
py3.13  cffi==2.1.1 msgpack==1.2.4 python-dateutil==2.9.0.post0   install exit=0  Ran 32 tests in 2.398s  OK
py3.14  cffi==2.1.1 (uv-managed CPython 3.14.10)                   install exit=0  Ran 32 tests in 4.047s  OK
```

GitHub Actions on the fork, run 44203400117 (https://github.com/Dukotah/lemongraph/actions/runs/44203400117):

```
completed success  1m8s
test (3.9) success / test (3.10) success / test (3.11) success / test (3.12) success / test (3.13) success
```

Not verified: the README's exact apt line in clean `ubuntu:22.04`/`ubuntu:24.04` containers - the docker run
was killed by host memory pressure and docker runs were then disallowed. CI covers ubuntu-24.04 with
setup-python + `libffi-dev`; the 22.04 apt recipe (`python3-dev python3-venv`) is untested.

Branch B:

```
$ uv pip install -e . networkx      # py3.12: cffi 2.1.1, msgpack 1.2.4, networkx 3.7
$ python test.py                    -> Ran 33 tests in 3.233s  OK   (32 upstream + TestNetworkX)
$ python test.py TestNetworkX -v    -> Ran 1 test in 0.204s  OK
$ /usr/bin/time python examples/ledger_graph/ledger_graph.py
  wall 0.91s maxrss 43332KB, 212 lines of output (pasted in examples/ledger_graph/README.md)
loaded 350 ledger rows -> 545 nodes, 916 edges in 0.11s
```

Findings the queries surfaced in the ledger: 29 rows are open/never-run, only 2 of them are linked to
another row (G4-ALLRUNES-NC5 waits on G4-TEX-RNG; VERDICT-OTP-CLASS waits on B-04); 19 of the 29 have no
`reopens_if` recorded; all 137 negative/eliminated rows have a passing positive control; 6 rows have a
failed control; A-03 is the row the most others transitively depend on (8).

## 4. Competing work check

- Upstream PRs, all states, listed with `gh pr list --state all`: nothing touches packaging, pins, CI or
  README install text. Closest is **#28 "Add tox configuration"** (2019, open, targets `master`, rewrites
  most `.py` files) - stale and conflicting with `lg-lite`; this PR is the narrower modern equivalent.
- Overlap with the 8 queued PRs (`gh pr view N --json files`):

| PR | base | files | overlap with fix/modern-packaging |
| -- | ---- | ----- | --------------------------------- |
| #36 | master | MatchLGQL.py, httpd.py, test.py | none |
| #37 | lg-lite | kv.py, server/__init__.py, sset.py, lib/lemongraph.c, test.py | none |
| #38 | lg-lite | server/__init__.py, test.py | none |
| #39 | lg-lite | dirlist.py, test.py | none |
| #40 | lg-lite | snapshot.py, test.py | none |
| #41 | lg-lite | serializer.py, test.py | none |
| #42 | lg-lite | __init__.py, test.py | none |
| #43 | lg-lite | httpd.py, test.py | none |

  This PR touches only `requirements.txt`, `pyproject.toml` (new), `.github/workflows/ci.yml` (new),
  `README.md`. Branch B touches `test.py` but is fork-only.
- Issues: #1 (networkx) is answered by branch B's adapter. No issue about install/3.13/CI exists. #44
  ("Pending private security advisories") is unrelated.

## 5. Draft upstream text

### PR (base: `lg-lite`, head: `Dukotah:fix/modern-packaging`)

Title: `Build on Python 3.13: relax dependency pins, add pyproject.toml and CI`

Body:

```
On lg-lite, `pip install .` fails on Python 3.13:

    src/c/_cffi_backend.c:6121:9: error: implicit declaration of function '_PyErr_WriteUnraisableMsg'

requirements.txt caps cffi below 1.17, and cffi 1.16 does not compile against 3.13. The msgpack (<1.1)
and python-dateutil (<2.9) caps also hold back the releases that ship 3.13 wheels.

Changes:
- requirements.txt: lower bounds unchanged, upper bounds raised to the next major version
  (cffi<3, lazy<2, msgpack<2, python-dateutil<3). No code changes.
- pyproject.toml: declares setuptools + cffi as build requirements (PEP 517/518). setup.py is
  unchanged and still drives the cffi build and `make deps`.
- .github/workflows/ci.yml: runs test.py on Python 3.9-3.13 for pushes and pull requests.
- README: replaces the CentOS 6/7 and Ubuntu 15.04-20.04 setup notes with Ubuntu 22.04/24.04.

Tested: test.py passes (32 tests) on 3.9, 3.12, 3.13 and 3.14 locally, and on 3.9-3.13 in GitHub
Actions: https://github.com/Dukotah/lemongraph/actions/runs/44203400117

The CI workflow would also give you a pass/fail signal on the PRs currently waiting on lg-lite
(#37-#43), each of which adds a test to test.py. It touches none of the files those PRs change.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Optional follow-up issue (networkx, reply on #1 rather than a new issue)

```
We have a small NetworkX export for LemonGraph: LemonGraph/nx.py, to_networkx(txn, ...) returns a
MultiDiGraph keyed by LemonGraph node/edge IDs, with type/value/properties as attributes and support for
historical views via beforeID. networkx is imported lazily, not added as a dependency. Branch with a test:
https://github.com/Dukotah/lemongraph/tree/lane/ledger-graph - happy to open a PR against lg-lite if
that is useful.
```

## 6. Land probability: Med

The maintainer does merge outside PRs into `lg-lite` (fast, for #35), and this one is small, touches no
queued file and arrives with green CI, but eight PRs have sat unreviewed for 1-4 months, so attention is
the bottleneck.

Owner next steps: (1) review the single commit on `fix/modern-packaging`; (2) open the PR against
**`lg-lite`** (not `master`) with the body above; (3) optionally reply on #1 with the networkx text;
(4) if you want the 22.04 apt line proven, run it once in `docker run ubuntu:22.04` before opening.
