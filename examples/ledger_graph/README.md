# Ledger graph

Loads a hypothesis ledger into LemonGraph, answers provenance questions with
the LemonGraph query language, and hands the graph to NetworkX through
`LemonGraph.nx.to_networkx`.

`LEDGER.json` is a copy of `liber-primus/LEDGER.json` from
[Dukotah/cicada3301](https://github.com/Dukotah/cicada3301) at commit
`6b945291ed298c14ccf8c73603f695a28f6a7e35`: 350 rows, one per hypothesis tested
during a multi-month Liber Primus (Cicada 3301) cryptanalysis. Each row records
its status, lane, round, whether its instrument passed a positive control, what
it covered and did not cover, what it supersedes, and the condition that would
reopen it.

## Run

    pip install -e . networkx
    python examples/ledger_graph/ledger_graph.py [path/to/LEDGER.json]

The graph is built in a temporary directory and deleted on exit. NetworkX is
optional; without it the last section is skipped.

## Graph model

| element | from ledger field |
| ------- | ----------------- |
| node `hypothesis` (value = row id) | properties: `status`, `lane`, `round`, `round_n`, `date`, `pc`, `positive_control`, `coverage`, `not_covered`, `reopens_if`, `hypothesis` |
| node `lane` | `lane` |
| node `round` (property `n`) | leading integer of `round` (`"10b/B4 + 12/D3"` -> 10) |
| edge `supersedes` | `supersedes`, and `superseded_by` reversed |
| edge `restates` | `restates` |
| edge `depends_on` | other row ids named in the `reopens_if` text |
| edge `in_lane`, `in_round` | hypothesis -> lane / round |
| edge `active_in` | lane -> round |

`pc` collapses the free-text `positive_control` field to `passed`, `failed`,
`none` (missing, `none`, `n/a...`, `not-persisted`) or `other`.

Property values use `Serializer.msgpack()`, so `round_n=null` and list filters
such as `status=["open","never-run"]` work as written.

## Queries

| | question | query |
| - | -------- | ----- |
| Q1 | What is still open or never run, and what is it waiting on? | `n(type="hypothesis", status=["open","never-run"])` and `...->e(type="depends_on")->n(type="hypothesis")` |
| Q2 | Which rows replaced or restated which? | `n(type="hypothesis")-e(type="supersedes")->n(type="hypothesis")` (and `restates`) |
| Q3 | Which rows lack a passing positive control? Does any negative? | `n(type="hypothesis", pc!="passed")`, `n(type="hypothesis", pc="failed")`, `n(type="hypothesis", status=["negative","eliminated"], pc!="passed")` |
| Q4 | Coverage by round | `n(type="hypothesis")->e(type="in_round")->n(type="round")` |
| Q5 | Which lanes ran across several rounds? | `n(type="lane")->e(type="active_in")->n(type="round")` |

## Output

Produced by the command above (Python 3.12, LemonGraph built from this branch):

```
loaded 350 ledger rows -> 545 nodes, 916 edges in 0.11s

## Q1. open / never-run rows and what blocks them
query: n(type="hypothesis", status=["open","never-run"])

B-06                               never-run  round=None
    hypothesis: A signed/archival pointer that a specific text is the key
    reopens if: (not recorded)
B-07                               never-run  round=None
    hypothesis: A correctly-targeted, locally-held archive for the AN END page
    reopens if: (not recorded)
B-14                               never-run  round=None
    hypothesis: AUTO_EVOLUTION epoch-6 SEEK roadmap (S1/S2/S3) never executed
    reopens if: (not recorded)
H-01                               never-run  round=None
    hypothesis: Per-onion HTTP/server-status anomalies: ports 5240/5241/5242/5243, mock uptime "1 days ...
    reopens if: (not recorded)
R12-C2                             never-run  round=12  
    hypothesis: A fresh esoteric/philosophical corpus (29 texts not used in campaign12/13 or armada18/1...
    reopens if: Low prior: Round 7 + D1 established the keytext class is closed by exhaustion, verified...
R20-SMARS-SCAFFOLDED               never-run  round=20  
    hypothesis: The pad is one of the 679 held Marsaglia CDROM physical-randomness units (~21 CPU-h). T...
    reopens if: Run smars_sweep.py against the 679 hash-verified units (~21 CPU-h) through the current ...
R28-L4-UNSWEPT-GENERATORS-QUEUE    never-run  round=28  
    hypothesis: LP2 0-54's pad comes from a 32-bit-seeded generator the census left open: PHP mt_rand (...
    reopens if: Completion event: cells finish -> batch parity (stage_a28.py, void on >1e-6) + oracle a...
R35-S1-S2-WINDOW                   never-run  round=35  
    hypothesis: With the Round 19 panel restored, the fixed grind27 engine passes --self-test and S2 (P...
    reopens if: the original Welsh corpus is found, or the S2 engine is re-gated on a new panel with a ...
R38-S2-PHP-SANDBOX                 never-run  round=38  
    hypothesis: The LP2 key is a PHP 5.x mt_rand stream (canonical or legacy twist, scale29 or mod29) w...
    reopens if: sandbox quota resets (2026-11-01T00:00Z) or a Pro plan; run run_commands.sh.
R39-S1-S2-WINDOWS                  never-run  round=39  
    hypothesis: Round 39 sandbox lanes S1 (S2 window 2 recovery and further Py2.7-MT exact windows) and...
    reopens if: after 2026-11-01 00:00 UTC and before about 2026-11-07: recover window 2 from the snaps...
B-03                               open       round=None
    hypothesis: Generator families Round 8 names as untested: PHP `mt_rand` (distinct tempering), .NET ...
    reopens if: (not recorded)
B-09                               open       round=None
    hypothesis: OSINT residue — T2/T3 blobs, items 6–9
    reopens if: (not recorded)
B-15                               open       round=None
    hypothesis: Round 6 trigram arm disclosed INCONCLUSIVE, restated as flat closure
    reopens if: (not recorded)
B-17                               open       round=None
    hypothesis: Multiple-comparisons tally frozen at 5 across Rounds 8–9
    reopens if: (not recorded)
B-18                               open       round=None
    hypothesis: Round 9 is invisible to all four navigation docs
    reopens if: (not recorded)
B-19                               open       round=None
    hypothesis: Round 9 LENGTH closed on the lower bound, not the point estimate
    reopens if: (not recorded)
B-20                               open       round=None
    hypothesis: Round 9 DIRECTION: 400-rune reads, ≤64 starts → "do not revive"
    reopens if: (not recorded)
B-22                               open       round=None
    hypothesis: Round 7's "orphaned .pyc / not-runnable" premise is now false
    reopens if: (not recorded)
B-24                               open       round=None
    hypothesis: Round 2 specificity anchor (AN END, 85 runes) disclosed underpowered
    reopens if: (not recorded)
C-01                               open       round=None
    hypothesis: SKELETON corpus extension. Round 8's word-length plaintext-identification is negative f...
    reopens if: (not recorded)
D-02                               open       round=None
    hypothesis: Higher-order model test against matched controls. The proposal asked for cross-validate...
    reopens if: (not recorded)
D-03                               open       round=None
    hypothesis: Homophonic-downward (surjective 29→k, k=5..26) annealing/EM search. Closed only by an i...
    reopens if: (not recorded)
D-04                               open       round=None
    hypothesis: Non-additive ciphertext-feedback coefficient sweep ran on 3 of 55 pages (p0/p5/p20) at ...
    reopens if: (not recorded)
G4-ALLRUNES-NC5                    open       round=19  
    hypothesis: round18/L1 NC-5: 'the allrunes Type-1 faces are custom-encoded (not Unicode-mapped), so...
    blocked on: G4-TEX-RNG [open]
    reopens if: L1's matcher is re-run with the allrunes bank included. If a specific allrunes shape va...
G4-TEX-RNG                         open       round=19  
    hypothesis: The LP2 0-54 keystream was generated INSIDE the typesetting document: by a TeX-side PRN...
    reopens if: Phase 2 (S1) runs it. The gate is K2: a planted phase must survive a 1e-3 rigid prefilt...
I1-09                              open       round=19  
    hypothesis: RECOMMENDATION to Phase 2: baseline channel = keyskip1 with adaptive max_skip (free str...
    reopens if: (not recorded)
J-01                               open       round=None
    hypothesis: `DEAD_ENDS.md`'s Campaign XVIII maintenance note ("source deleted; survives only as orp...
    reopens if: (not recorded)
R44-W2B4-TREES-P55-GHOST-ALPHA     open       round=44  
    hypothesis: The p55 grey 'ghost tree' encodes information beyond a flat grey rendering (chroma chan...
    reopens if: the oracle overrules the two-tone characterization, or a non-JPEG source of p55 surface...
VERDICT-OTP-CLASS                  open       round=10  
    hypothesis: LP2 0-54 is OTP-class: a full-length keystream under a soft anti-repeat filter (~83% su...
    blocked on: B-04 [negative]
    reopens if: The derived-key dictionary (B-04) returns a hit, which would make the keystream derived...
-- 29 rows; 2 depend on another ledger row (query: n(type="hypothesis", status=["open","never-run"])->e(type="depends_on")->n(type="hypothesis"))

## Q2. supersession chains
query: n(type="hypothesis")-e(type="supersedes")->n(type="hypothesis")   (+ restates)

L7-C-B17-TALLY [audit] -restates-> B-17 [open]
R24-C1-EXT-NONENGLISH-READJUDICATION [negative] -restates-> L7-A-SCORER-ENGLISH-ONLY [negative]
R24-C1-EXT-NONENGLISH-READJUDICATION [negative] -restates-> R24-C1-MATCHED-RUNIC-READJUDICATION [negative] -restates-> L7-A-ARCHIVE-RESCORE [negative]
R24-C1-EXT-NONENGLISH-READJUDICATION [negative] -restates-> R24-C1-MATCHED-RUNIC-READJUDICATION [negative] -restates-> L7-A-SCORER-ENGLISH-ONLY [negative]
R24-C1-EXT-NONENGLISH-READJUDICATION [negative] -restates-> R24-C1-MATCHED-RUNIC-READJUDICATION [negative] -restates-> RESTATE-B-04 [audit] -restates-> B-04 [negative]
R24-C2-EXT-SKIP-GENERATORS [negative] -restates-> R24-C2-SKIP-BY-TWO-DECODER [negative] -restates-> L7-B-BEAM-ENVELOPE [negative]
R24-C8-DATE-INDEXED-PAD [measured] -restates-> R17-PUBLIC-PAD [negative]
R25-COMPUTE-TAIL-CHUNK1 [partially-run] -restates-> R21-L3-PY27-REDUCERS [measured]
R25-COMPUTE-TAIL-CHUNK1 [partially-run] -restates-> R24-C2-SKIP-BY-TWO-DECODER [negative] -restates-> L7-B-BEAM-ENVELOPE [negative]
R29-L1-ONION-STEGO [negative] -supersedes-> B-10 [superseded]
RESTATE-B-21-ROUND8-BAR [audit] -restates-> B-21 [partially-run]
RESTATE-R16-KDF [audit] -restates-> R16-KDF [negative]
RESTATE-R16-PRNG [audit] -restates-> R16-PRNG [negative] -supersedes-> B-03 [open]
RESTATE-R17-PUBLIC-PAD [audit] -restates-> R17-PUBLIC-PAD [negative]
VERDICT-OTP-CLASS [open] -supersedes-> VERDICT-UNSOLVABLE-BY-DESIGN [superseded]

## Q3. rows whose positive control did not pass
query: n(type="hypothesis", pc!="passed")

status         pc      rows
audit          none      30
audit          other      2
inconclusive   failed     4
inconclusive   none       9
measured       failed     1
measured       none      16
measured       other     13
never-run      none       8
open           none      14
partially-run  failed     1
partially-run  none      10
partially-run  other      2
superseded     none       5

query: n(type="hypothesis", pc="failed")
R37-C2-U7-BOOK-CODE-W              inconclusive  Same as R37-C2-U7-BOOK-CODE with the whole indexed word r...
R37-C2-U8-GEOMETRY                 inconclusive  Numbers are the direction: per-page, interrupter-gated tu...
R38-I1-GLYPH-RECOGNIZER            inconclusive  A stroke-aware rotation-invariant recognizer (strokes/clo...
R39-I1-V2-PAGE-NULL                inconclusive  A page-matched null (shuffle within physical line, or wit...
R41-C1-R44-BOOKCIPHER-BOOKS-FOUND  partially-run R44: LP numbers as pointers into Cicada's known books (bo...
R41-I1-NULL-REFIT-SURVIVOR12       measured      A bar fitted on the population it is applied to (wrong-ke...

query: n(type="hypothesis", status=["negative","eliminated"], pc!="passed")
-- 0 negative/eliminated rows lack a passing positive control

## Q4. coverage by round
query: n(type="hypothesis")->e(type="in_round")->n(type="round")

round   rows negati measur  audit   open never- partia inconc pc_pas gaps_d
    8      1      0      0      0      0      0      1      0      1      1
   10      3      0      2      0      1      0      0      0      1      2
   11      7      0      7      0      0      0      0      0      0      7
   12      6      2      0      0      0      1      0      0      4      4
   13      2      2      0      0      0      0      0      0      2      2
   16      8      8      0      0      0      0      0      0      8      8
   17      2      1      0      0      0      0      0      0      1      2
   18     27      7      5      9      0      0      4      0     17     19
   19     52      6     35      7      3      0      0      0     38     49
   20     12      3      5      3      0      1      0      0     10     12
   21      4      0      2      2      0      0      0      0      4      4
   22      5      4      0      1      0      0      0      0      4      5
   23      1      1      0      0      0      0      0      0      1      1
   24      5      4      1      0      0      0      0      0      5      5
   25      1      0      0      0      0      0      1      0      1      1
   26      4      1      0      1      0      0      2      0      1      4
   27      1      0      0      0      0      0      1      0      1      1
   28      6      3      0      1      0      1      0      1      5      6
   29      1      1      0      0      0      0      0      0      1      1
   30      8      5      2      1      0      0      0      0      8      5
   32      8      3      2      3      0      0      0      0      5      8
   33      7      1      2      3      0      0      1      0      3      7
   34      7      1      4      2      0      0      0      0      1      7
   35      7      2      2      2      0      1      0      0      3      7
   36     11      4      4      2      0      0      1      0      8     11
   37     22     15      3      1      0      0      0      3     17     22
   38     12      6      3      1      0      1      0      1      9     12
   39      6      1      1      2      0      1      0      1      2      6
   40     29     17      1      1      0      0      5      3     22     29
   41      8      2      1      0      0      0      1      4      2      8
   42      5      3      2      0      0      0      0      0      5      5
   43      5      4      1      0      0      0      0      0      4      1
   44     41     25     14      0      1      0      1      0     41     40
-- 26 rows carry no round (pre-round recon lanes)

## Q5. lanes active in more than one round
query: n(type="lane")->e(type="active_in")->n(type="round")

keystream                                 7 rounds: 8 13 16 17 18 19 21
C1                                        6 rounds: 37 38 39 40 41 42
I1                                        5 rounds: 37 38 39 40 41
B1                                        4 rounds: 34 35 36 40
X1                                        4 rounds: 37 38 39 40
I3                                        3 rounds: 19 32 35
T1                                        3 rounds: 19 37 39
instrument                                3 rounds: 16 18 19
recon-a                                   3 rounds: 16 18 19
C2                                        2 rounds: 38 42
C3                                        2 rounds: 37 42
I2                                        2 rounds: 37 38
S1                                        2 rounds: 38 42
mechanism                                 2 rounds: 12 18
verdict                                   2 rounds: 10 12

## NetworkX export (LemonGraph.nx.to_networkx)

full graph: MultiDiGraph with 545 nodes, 916 edges
depends_on subgraph: 37 nodes, 26 edges, acyclic=True
rows that the most other rows (transitively) wait on:
  A-03                       [negative] <- 8 rows
  B-04                       [negative] <- 6 rows
  D-01                       [negative] <- 2 rows
  A-05                       [negative] <- 1 rows
  A-06                       [measured] <- 1 rows
```
