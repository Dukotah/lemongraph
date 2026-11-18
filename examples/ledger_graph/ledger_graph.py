#!/usr/bin/env python3
"""Load a hypothesis ledger (LEDGER.json) into LemonGraph and query it.

    python examples/ledger_graph/ledger_graph.py [path/to/LEDGER.json]

The bundled LEDGER.json is the provenance ledger of a long-running Liber Primus
(Cicada 3301) cryptanalysis: one row per hypothesis that was tested, with its
status, the round it ran in, whether its instrument passed a positive control,
what it did and did not cover, and the concrete condition that would reopen it.

Graph model
    node hypothesis:<id>   properties: status, lane, round, round_n, date, pc,
                           positive_control, coverage, not_covered, reopens_if,
                           hypothesis
    node lane:<lane>
    node round:<n>         n = leading integer of the ledger's round field
    edge supersedes        hypothesis -> hypothesis it replaces
                           (from both 'supersedes' and 'superseded_by')
    edge depends_on        hypothesis -> hypothesis named in its reopens_if text
    edge restates          hypothesis -> hypothesis it restates
    edge in_lane           hypothesis -> lane
    edge in_round          hypothesis -> round
    edge active_in         lane -> round   (lane had at least one row in round)
"""

from __future__ import print_function

import collections
import json
import os
import re
import shutil
import sys
import tempfile
import time

import LemonGraph

HERE = os.path.dirname(os.path.abspath(__file__))


def norm_pc(raw):
    """Collapse the free-text positive_control field into passed/failed/none/other."""
    if raw is None:
        return 'none'
    s = str(raw).strip().lower()
    if s in ('passed', 'pass'):
        return 'passed'
    if s in ('failed', 'fail'):
        return 'failed'
    if s in ('none', 'n/a', 'not-persisted') or s.startswith('n/a') or s.startswith('none'):
        return 'none'
    return 'other'


def round_n(raw):
    m = re.match(r'\s*(\d+)', str(raw)) if raw is not None else None
    return int(m.group(1)) if m else None


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def text(x):
    if x is None:
        return None
    return x if isinstance(x, str) else json.dumps(x, sort_keys=True)


def load(txn, rows):
    ids = set(r['id'] for r in rows)
    # longest first so 'B-04' does not shadow 'B-04-X'; word-ish boundaries
    idpat = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(i) for i in sorted(ids, key=len, reverse=True)) + r')(?![\w-])')

    H = {}
    for r in rows:
        n = txn.node(type='hypothesis', value=r['id'])
        rn = round_n(r.get('round'))
        n.update({
            'status': r.get('status'),
            'lane': r.get('lane'),
            'round': text(r.get('round')),
            'round_n': rn,
            'date': r.get('date'),
            'pc': norm_pc(r.get('positive_control')),
            'positive_control': text(r.get('positive_control')),
            'coverage': text(r.get('coverage')),
            'not_covered': text(r.get('not_covered')),
            'reopens_if': r.get('reopens_if'),
            'hypothesis': r.get('hypothesis'),
        })
        H[r['id']] = n

    lanes = {}
    rounds = {}
    for r in rows:
        h = H[r['id']]
        if r['lane'] not in lanes:
            lanes[r['lane']] = txn.node(type='lane', value=r['lane'])
        lane = lanes[r['lane']]
        txn.edge(src=h, tgt=lane, type='in_lane')
        rn = round_n(r.get('round'))
        if rn is not None:
            if rn not in rounds:
                rounds[rn] = txn.node(type='round', value=str(rn))
                rounds[rn]['n'] = rn
            rnode = rounds[rn]
            txn.edge(src=h, tgt=rnode, type='in_round')
            txn.edge(src=lane, tgt=rnode, type='active_in')

        for old in as_list(r.get('supersedes')):
            if old in H:
                txn.edge(src=h, tgt=H[old], type='supersedes')
        for new in as_list(r.get('superseded_by')):
            if new in H:
                txn.edge(src=H[new], tgt=h, type='supersedes')
        for other in as_list(r.get('restates')):
            if other in H:
                txn.edge(src=h, tgt=H[other], type='restates')
        for dep in sorted(set(idpat.findall(r.get('reopens_if') or '')) - set([r['id']])):
            txn.edge(src=h, tgt=H[dep], type='depends_on')


def short(s, n=90):
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 3] + '...'


def header(title, query):
    print()
    print('## ' + title)
    print('query: ' + query)
    print()


def main(path):
    with open(path) as fh:
        ledger = json.load(fh)
    rows = ledger['entries']

    tmpdir = tempfile.mkdtemp()
    t0 = time.time()
    try:
        g = LemonGraph.Graph(os.path.join(tmpdir, 'ledger.db'),
                             serialize_property_value=LemonGraph.Serializer.msgpack())
        with g.transaction(write=True) as txn:
            load(txn, rows)
        with g.transaction(write=False) as txn:
            print('loaded %d ledger rows -> %d nodes, %d edges in %.2fs' % (
                len(rows), txn.nodes_count(), txn.edges_count(), time.time() - t0))
            run_queries(txn)
            run_networkx(txn)
        g.close()
    finally:
        shutil.rmtree(tmpdir)


def run_queries(txn):
    # Q1: everything still on the table, and what it is waiting on
    q = 'n(type="hypothesis", status=["open","never-run"])'
    header('Q1. open / never-run rows and what blocks them', q)
    blockers = collections.defaultdict(list)
    q_dep = 'n(type="hypothesis", status=["open","never-run"])->e(type="depends_on")->n(type="hypothesis")'
    for row, _, dep in txn.query(q_dep):
        blockers[row.value].append('%s [%s]' % (dep.value, dep['status']))
    found = sorted(txn.query(q), key=lambda c: (c[0]['status'], c[0].value))
    for (n,) in found:
        print('%-34s %-10s round=%-4s' % (n.value, n['status'], n['round_n']))
        print('    hypothesis: ' + short(n['hypothesis']))
        if n.value in blockers:
            print('    blocked on: ' + ', '.join(blockers[n.value]))
        print('    reopens if: ' + short(n['reopens_if'] or '(not recorded)'))
    print('-- %d rows; %d depend on another ledger row (query: %s)' % (
        len(found), len(blockers), q_dep))

    # Q2: supersession chains, longest first
    q = 'n(type="hypothesis")-e(type="supersedes")->n(type="hypothesis")'
    header('Q2. supersession chains', q + '   (+ restates)')
    nxt = collections.defaultdict(list)
    has_parent = set()
    for etype in ('supersedes', 'restates'):
        for a, e, b in txn.query('n(type="hypothesis")-e(type="%s")->n(type="hypothesis")' % etype):
            nxt[a.value].append((etype, b.value, b['status']))
            has_parent.add(b.value)
    status = dict((n.value, n['status']) for (n,) in txn.query('n(type="hypothesis")'))

    def walk(v, seen):
        out = []
        for etype, w, _ in sorted(nxt.get(v, ())):
            if w in seen:
                continue
            for tail in walk(w, seen | set([w])) or [[]]:
                out.append([(etype, w)] + tail)
        return out
    for root in sorted(v for v in nxt if v not in has_parent):
        for chain in walk(root, set([root])):
            s = '%s [%s]' % (root, status[root])
            for etype, w in chain:
                s += ' -%s-> %s [%s]' % (etype, w, status[w])
            print(s)

    # Q3: rows whose instrument did not pass a positive control
    q = 'n(type="hypothesis", pc!="passed")'
    header('Q3. rows whose positive control did not pass', q)
    by = collections.Counter((n['status'], n['pc']) for (n,) in txn.query(q))
    print('status         pc      rows')
    for (st, pc), k in sorted(by.items()):
        print('%-14s %-7s %4d' % (st, pc, k))
    q = 'n(type="hypothesis", pc="failed")'
    print('\nquery: ' + q)
    for (n,) in sorted(txn.query(q), key=lambda c: c[0].value):
        print('%-34s %-13s %s' % (n.value, n['status'], short(n['hypothesis'], 60)))
    # a negative without a passing control is an unknown, not a negative
    q = 'n(type="hypothesis", status=["negative","eliminated"], pc!="passed")'
    print('\nquery: ' + q)
    found = sorted(n.value for (n,) in txn.query(q))
    print('-- %d negative/eliminated rows lack a passing positive control%s' % (
        len(found), (': ' + ', '.join(found)) if found else ''))

    # Q4: coverage by round
    q = 'n(type="hypothesis")->e(type="in_round")->n(type="round")'
    header('Q4. coverage by round', q)
    per = collections.defaultdict(collections.Counter)
    for h, _, r in txn.query(q):
        c = per[r['n']]
        c['rows'] += 1
        c[h['status']] += 1
        c['pc_passed'] += h['pc'] == 'passed'
        c['gaps_documented'] += bool(h['not_covered'])
    cols = ('rows', 'negative', 'measured', 'audit', 'open', 'never-run', 'partially-run', 'inconclusive', 'pc_passed', 'gaps_documented')
    print('round ' + ' '.join('%6s' % c[:6] for c in cols))
    for rn in sorted(per):
        print('%5d ' % rn + ' '.join('%6d' % per[rn][c] for c in cols))
    norounds = sum(1 for _ in txn.query('n(type="hypothesis", round_n=null)'))
    print('-- %d rows carry no round (pre-round recon lanes)' % norounds)

    # Q5: lanes that ran across the most rounds
    q = 'n(type="lane")->e(type="active_in")->n(type="round")'
    header('Q5. lanes active in more than one round', q)
    spans = collections.defaultdict(set)
    for lane, _, r in txn.query(q):
        spans[lane.value].add(r['n'])
    for lane, rs in sorted(spans.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(rs) > 1:
            print('%-40s %2d rounds: %s' % (lane, len(rs), ' '.join(str(x) for x in sorted(rs))))


def run_networkx(txn):
    try:
        import networkx as nx
    except ImportError:
        print('\n(networkx not installed - skipping NetworkX export)')
        return
    from LemonGraph.nx import to_networkx

    print()
    print('## NetworkX export (LemonGraph.nx.to_networkx)')
    print()
    G = to_networkx(txn)
    print('full graph: %s with %d nodes, %d edges' % (type(G).__name__, G.number_of_nodes(), G.number_of_edges()))

    # transitive blockers: follow depends_on edges all the way down
    D = nx.DiGraph()
    D.add_edges_from((u, v) for u, v, d in G.edges(data=True) if d['type'] == 'depends_on')
    label = dict((n, d['value']) for n, d in G.nodes(data=True))
    st = dict((n, d.get('status')) for n, d in G.nodes(data=True))
    print('depends_on subgraph: %d nodes, %d edges, acyclic=%s' % (
        D.number_of_nodes(), D.number_of_edges(), nx.is_directed_acyclic_graph(D)))
    ranked = sorted(D.nodes(), key=lambda n: (-len(nx.ancestors(D, n)), label[n]))
    print('rows that the most other rows (transitively) wait on:')
    for n in ranked[:5]:
        print('  %-26s [%s] <- %d rows' % (label[n], st[n], len(nx.ancestors(D, n))))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'LEDGER.json'))
