"""Check uniform-weight ranking certificates on a fixed small synthetic sample.

Use `run PLAN OUTPUT` once to generate the specified inputs and results.
Use `verify OUTPUT` to check saved inputs and results without generating data.
All mathematical comparisons use integers. NumPy is used for data generation
and the first exhaustive enumeration. The verification pass uses Python loops.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

import numpy as np


def write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expire(signum, frame):
    raise TimeoutError('The fixed time limit was reached.')


def generate(plan, seed):
    rng = np.random.default_rng(seed)
    N, M, r = plan['N'], plan['M'], plan['r']
    truth = rng.integers(0, 2, N)
    difficulty = rng.normal(0.0, 1.5, N)
    skill = 2.0 + rng.normal(0.0, plan['skill_sd'], M)
    probability = 1 / (1 + np.exp(-(skill[:, None] - difficulty[None, :])))
    correct = rng.random((M, N)) < probability
    predictions = np.where(correct, truth, 1 - truth)
    labels = truth.copy()
    flip = rng.random(N) < plan['noise']
    labels[flip] = 1 - labels[flip]
    disagreement = (predictions != labels).sum(axis=0)
    flagged = np.argsort(-disagreement, kind='stable')[:r]
    return {'seed': seed, 'predictions': predictions.tolist(), 'recorded_labels': labels.tolist(),
            'flagged': flagged.tolist(), 'generated_true_labels': truth.tolist()}


def pair_data(data):
    P, rec, flagged = data['predictions'], data['recorded_labels'], data['flagged']
    counts = [sum(p == y for p, y in zip(row, rec)) for row in P]
    order = sorted(range(len(P)), key=lambda m: (-counts[m], m))
    pairs = list(itertools.combinations(order, 2))
    result = []
    for earlier, later in pairs:
        gains = [int(P[earlier][u] == rec[u]) - int(P[later][u] == rec[u]) for u in flagged]
        result.append((counts[later] - counts[earlier], gains))
    return counts, order, pairs, result


def one_event(pair, budget, threshold=1):
    delta, gains = pair
    return delta + 2 * min(budget, gains.count(1)) >= threshold


def two_event(first, second, budget, threshold=1):
    delta, gains = first
    other_delta, other_gains = second
    counts = {(a, b): 0 for a in (-1, 0, 1) for b in (-1, 0, 1)}
    for a, b in zip(gains, other_gains):
        counts[a, b] += 1
    need_a = -((delta - threshold) // 2)
    need_b = -((other_delta - threshold) // 2)
    shared = min(budget, counts[1, 1])
    remaining = budget - shared
    need_a -= shared
    need_b -= shared
    for direction in (1, -1):
        for trade in range(min(remaining, counts[direction, -direction]) + 1):
            a = max(0, need_a - direction * trade)
            b = max(0, need_b + direction * trade)
            if a <= counts[1, 0] and b <= counts[0, 1] and trade + a + b <= remaining:
                return True
    return False


def double_cover_certificate(vertices, edges):
    """Return a matching, cover, and primal/dual numerators with denominator 2."""
    adjacency = {v: [] for v in vertices}
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    right_match = {}

    def augment(left, seen):
        for right in adjacency[left]:
            if right in seen:
                continue
            seen.add(right)
            if right not in right_match or augment(right_match[right], seen):
                right_match[right] = left
                return True
        return False

    for v in vertices:
        augment(v, set())
    left_match = {left: right for right, left in right_match.items()}
    seen_left = set(vertices) - set(left_match)
    seen_right = set()
    queue = sorted(seen_left)
    for left in queue:
        for right in adjacency[left]:
            if left_match.get(left) == right or right in seen_right:
                continue
            seen_right.add(right)
            if right in right_match and right_match[right] not in seen_left:
                seen_left.add(right_match[right])
                queue.append(right_match[right])
    cover_left = set(vertices) - seen_left
    cover_right = seen_right
    matching = sorted((left, right) for right, left in right_match.items())
    alpha = [int(left_match.get(a) == b) + int(left_match.get(b) == a) for a, b in edges]
    incidence = {v: 0 for v in vertices}
    for (a, b), value in zip(edges, alpha):
        incidence[a] += value
        incidence[b] += value
    return {'vertices': vertices, 'edges': edges, 'matching': matching,
            'cover_left': sorted(cover_left), 'cover_right': sorted(cover_right),
            'x2': [2 - int(v in cover_left) - int(v in cover_right) for v in vertices],
            'alpha2': alpha, 'beta2': [2 - incidence[v] for v in vertices]}


def verify_certificate(cert, expected_vertices, expected_edges):
    vertices = cert['vertices']
    edges = [tuple(edge) for edge in cert['edges']]
    require(vertices == expected_vertices and edges == expected_edges, 'Graph differs from event tests.')
    require(len(vertices) == len(set(vertices)), 'Repeated vertex.')
    vertex_set, edge_set = set(vertices), set(edges)
    require(all(a in vertex_set and b in vertex_set and a < b for a, b in edges), 'Invalid edge.')
    require(len(edges) == len(edge_set), 'Repeated edge.')
    matching = [tuple(edge) for edge in cert['matching']]
    require(all(tuple(sorted(edge)) in edge_set for edge in matching), 'Matching uses a missing edge.')
    require(len({a for a, b in matching}) == len(matching), 'Repeated left endpoint.')
    require(len({b for a, b in matching}) == len(matching), 'Repeated right endpoint.')
    left, right = set(cert['cover_left']), set(cert['cover_right'])
    require(left <= vertex_set and right <= vertex_set, 'Cover uses a missing vertex.')
    require(len(left) == len(cert['cover_left']) and len(right) == len(cert['cover_right']), 'Repeated cover vertex.')
    require(all((a in left or b in right) and (b in left or a in right) for a, b in edges), 'Cover misses an orientation.')
    require(len(left) + len(right) == len(matching), 'Matching and cover sizes differ.')
    x, alpha, beta = cert['x2'], cert['alpha2'], cert['beta2']
    require(len(x) == len(beta) == len(vertices) and len(alpha) == len(edges), 'Certificate length differs.')
    require(all(type(z) is int for z in x + alpha + beta), 'Certificate is not integral.')
    require(all(0 <= z <= 2 for z in x), 'Primal coordinate outside bounds.')
    require(all(z >= 0 for z in alpha + beta), 'Negative dual coordinate.')
    xp = dict(zip(vertices, x))
    coverage = dict(zip(vertices, beta))
    for (a, b), value in zip(edges, alpha):
        require(xp[a] + xp[b] <= 2, 'Primal violates an edge.')
        coverage[a] += value
        coverage[b] += value
    require(all(z >= 2 for z in coverage.values()), 'Dual misses a vertex.')
    require(sum(x) == sum(alpha) + sum(beta), 'Primal and dual objectives differ.')
    return sum(x)


def enumerate_numpy(data, pairs):
    rec = np.array(data['recorded_labels'], dtype=np.int16)
    P = np.array(data['predictions'], dtype=np.int16)
    flagged = data['flagged']
    r = len(flagged)
    masks = np.arange(1 << r, dtype=np.int64)
    bits = ((masks[:, None] >> np.arange(r)) & 1).astype(np.int16)
    labels = np.broadcast_to(rec, (1 << r, len(rec))).copy()
    labels[:, flagged] ^= bits
    counts = np.column_stack([(labels == row).sum(axis=1) for row in P])
    events = np.column_stack([counts[:, later] > counts[:, earlier] for earlier, later in pairs])
    sizes = bits.sum(axis=1)
    row_values = events.sum(axis=1)
    one_min = [int(sizes[events[:, e]].min()) if events[:, e].any() else r + 1 for e in range(len(pairs))]
    joint_min = []
    for e, f in itertools.combinations(range(len(pairs)), 2):
        hit = events[:, e] & events[:, f]
        joint_min.append([e, f, int(sizes[hit].min()) if hit.any() else r + 1])
    values, witnesses = [], []
    for budget in range(r + 1):
        eligible = np.flatnonzero(sizes <= budget)
        witness = int(eligible[np.argmax(row_values[eligible])])
        values.append(int(row_values[witness]))
        witnesses.append(witness)
    return one_min, joint_min, values, witnesses


def first_crossing(numerators, denominator, limit):
    a, b = limit
    return next((i for i, n in enumerate(numerators) if n * b > a * denominator), len(numerators))


def worker(plan_path, output, index):
    plan = json.loads(Path(plan_path).read_text())
    output = Path(output)
    signal.signal(signal.SIGALRM, expire)
    start, cpu_start = time.monotonic(), time.process_time()
    data = generate(plan, plan['seeds'][index])
    write_json(output / f'input-{index:02d}.json', data)
    counts, order, pairs, gains = pair_data(data)
    one_min, joint_min, exact, witnesses = enumerate_numpy(data, pairs)
    write_json(output / f'enumeration-{index:02d}.json', {
        'one_event_min_budget': one_min, 'joint_event_min_budget': joint_min,
        'exact_numerators': exact, 'exact_witness_masks': witnesses})
    all_certificates, separate, h2 = [], [], []
    for budget in range(plan['r'] + 1):
        signal.setitimer(signal.ITIMER_REAL, plan['limits_seconds']['certificate'])
        vertices = [e for e, pair in enumerate(gains) if one_event(pair, budget)]
        require(vertices == [e for e, minimum in enumerate(one_min) if minimum <= budget], 'One-event mismatch.')
        edge_set = set()
        for e, f, minimum in joint_min:
            simultaneous = two_event(gains[e], gains[f], budget)
            require(simultaneous == (minimum <= budget), 'Two-event mismatch.')
            if e in vertices and f in vertices and not simultaneous:
                edge_set.add((e, f))
        edges = sorted(edge_set)
        cert = double_cover_certificate(vertices, edges)
        value2 = verify_certificate(cert, vertices, edges)
        require(2 * exact[budget] <= value2 <= 2 * len(vertices), 'Bound ordering fails.')
        all_certificates.append(cert)
        separate.append(len(vertices))
        h2.append(value2)
        write_json(output / f'partial-{index:02d}.json', {
            'completed_budgets': budget + 1, 'certificates': all_certificates,
            'separate_numerators': separate, 'H_numerators_denominator_2Q': h2})
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(all(a <= b for seq in (exact, separate, h2) for a, b in zip(seq, seq[1:])), 'Budget monotonicity fails.')
    Q = len(pairs)
    crossings = []
    for limit in plan['limits']:
        sep = first_crossing(separate, Q, limit)
        lower = first_crossing(h2, 2 * Q, limit)
        truth = first_crossing(exact, Q, limit)
        require(sep <= lower <= truth, 'Breakdown ordering fails.')
        crossings.append({'limit': limit, 'b_sep': sep, 'b_L': lower, 'b_star': truth})
    result = {'status': 'complete', 'seed': data['seed'], 'counts': counts, 'order': order,
              'pairs': pairs, 'one_event_min_budget': one_min, 'joint_event_min_budget': joint_min,
              'exact_numerators': exact, 'exact_witness_masks': witnesses, 'separate_numerators': separate,
              'H_numerators_denominator_2Q': h2, 'Q': Q, 'certificates': all_certificates,
              'crossings': crossings, 'enumerated_corrections': 1 << plan['r'],
              'wall_seconds': time.monotonic() - start, 'cpu_seconds': time.process_time() - cpu_start}
    write_json(output / f'result-{index:02d}.json', result)


def run(plan_path, destination):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    require(plan['margin'] == [0, 1], 'This implementation requires zero margin.')
    require(plan['M'] >= 2 and 0 <= plan['r'] <= plan['N'], 'Invalid input dimensions.')
    output = Path(destination).resolve()
    output.mkdir(exist_ok=False)
    write_json(output / 'plan.json', plan)
    write_json(output / 'environment.json', {'python': sys.version, 'numpy': np.__version__,
              'platform': platform.platform(), 'machine': platform.machine(), 'code_sha256': sha256(Path(__file__)),
              'plan_sha256': sha256(plan_path), 'timing_scope': 'Operational receipts, not performance evidence.'})
    start = time.monotonic()
    statuses = []
    for index, seed in enumerate(plan['seeds']):
        remaining = plan['limits_seconds']['run'] - (time.monotonic() - start)
        if remaining <= 0:
            statuses.append({'index': index, 'seed': seed, 'status': 'unattempted_after_run_cap'})
            continue
        command = [sys.executable, str(Path(__file__).resolve()), '_worker', str(plan_path), str(output), str(index)]
        try:
            process = subprocess.run(command, capture_output=True, timeout=min(remaining, plan['limits_seconds']['instance']))
            (output / f'log-{index:02d}.txt').write_bytes(process.stdout + process.stderr)
            status = 'complete' if process.returncode == 0 else 'failed'
            statuses.append({'index': index, 'seed': seed, 'status': status, 'returncode': process.returncode})
        except subprocess.TimeoutExpired as error:
            (output / f'log-{index:02d}.txt').write_bytes((error.stdout or b'') + (error.stderr or b''))
            statuses.append({'index': index, 'seed': seed, 'status': 'timeout'})
        write_json(output / 'status.json', {'instances': statuses, 'wall_seconds': time.monotonic() - start})
    write_json(output / 'status.json', {'instances': statuses, 'wall_seconds': time.monotonic() - start})
    print(json.dumps({'complete': sum(row['status'] == 'complete' for row in statuses), 'planned': len(statuses)}))


def enumerate_python(data):
    """Independent scalar reference: change labels and recount every prediction."""
    P, original, flagged = data['predictions'], data['recorded_labels'], data['flagged']
    M, r = len(P), len(flagged)
    base = [sum(row[u] == original[u] for u in range(len(original))) for row in P]
    order = sorted(range(M), key=lambda m: (-base[m], m))
    pairs = [(order[a], order[b]) for a in range(M) for b in range(a + 1, M)]
    Q = len(pairs)
    one_min = [r + 1] * Q
    joint = {(a, b): r + 1 for a in range(Q) for b in range(a + 1, Q)}
    exact = [-1] * (r + 1)
    witness = [None] * (r + 1)
    for mask in range(1 << r):
        corrected = original.copy()
        for bit, column in enumerate(flagged):
            if mask & (1 << bit):
                corrected[column] = 1 - corrected[column]
        scores = [sum(row[u] == corrected[u] for u in range(len(corrected))) for row in P]
        events = [e for e, (a, b) in enumerate(pairs) if scores[b] > scores[a]]
        size = mask.bit_count()
        for e in events:
            one_min[e] = min(one_min[e], size)
        for e, f in itertools.combinations(events, 2):
            joint[e, f] = min(joint[e, f], size)
        for budget in range(size, r + 1):
            if len(events) > exact[budget]:
                exact[budget], witness[budget] = len(events), mask
    return base, order, pairs, one_min, [[a, b, value] for (a, b), value in joint.items()], exact, witness


def verify(output):
    output = Path(output)
    plan = json.loads((output / 'plan.json').read_text())
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, plan['limits_seconds']['verification'])
    start = time.monotonic()
    statuses = json.loads((output / 'status.json').read_text())['instances']
    require(len(statuses) == len(plan['seeds']), 'Missing planned status.')
    checked, failures = [], []
    for index, row in enumerate(statuses):
        require(row['index'] == index and row['seed'] == plan['seeds'][index], 'Status order differs from plan.')
        if row['status'] != 'complete':
            failures.append({'index': index, 'reason': row['status']})
            continue
        try:
            data = json.loads((output / f'input-{index:02d}.json').read_text())
            result = json.loads((output / f'result-{index:02d}.json').read_text())
            require(result['status'] == 'complete', 'Result is not complete.')
            require(result['enumerated_corrections'] == 1 << plan['r'], 'Correction count differs.')
            require(data['seed'] == result['seed'] == row['seed'], 'Seed mismatch.')
            require(len(data['predictions']) == plan['M'], 'Model count mismatch.')
            require(len(data['recorded_labels']) == plan['N'], 'Example count mismatch.')
            require(all(len(p) == plan['N'] and set(p) <= {0, 1} for p in data['predictions']), 'Invalid predictions.')
            require(set(data['recorded_labels']) <= {0, 1}, 'Invalid labels.')
            require(len(data['flagged']) == len(set(data['flagged'])) == plan['r'], 'Invalid flagged set size.')
            require(all(0 <= u < plan['N'] for u in data['flagged']), 'Invalid flagged column.')
            disagreement = [sum(row[u] != data['recorded_labels'][u] for row in data['predictions'])
                            for u in range(plan['N'])]
            expected_flags = sorted(range(plan['N']), key=lambda u: (-disagreement[u], u))[:plan['r']]
            require(data['flagged'] == expected_flags, 'Flag selection differs.')
            base, order, pairs, one, joint, exact, witnesses = enumerate_python(data)
            for name, value in [('counts', base), ('order', order), ('pairs', [list(p) for p in pairs]),
                                ('one_event_min_budget', one), ('joint_event_min_budget', joint),
                                ('exact_numerators', exact), ('exact_witness_masks', witnesses)]:
                require(result[name] == value, 'Independent reference differs: ' + name)
            Q, r = len(pairs), plan['r']
            require(result['Q'] == Q and len(result['certificates']) == r + 1, 'Result size mismatch.')
            hs, seps = [], []
            for budget, cert in enumerate(result['certificates']):
                vertices = [e for e, minimum in enumerate(one) if minimum <= budget]
                edges = [(e, f) for e, f, minimum in joint if e in vertices and f in vertices and minimum > budget]
                h2 = verify_certificate(cert, vertices, edges)
                require(2 * exact[budget] <= h2 <= 2 * len(vertices), 'Independent bound ordering fails.')
                hs.append(h2)
                seps.append(len(vertices))
            require(hs == result['H_numerators_denominator_2Q'] and seps == result['separate_numerators'], 'Saved bound differs.')
            require(len(result['crossings']) == len(plan['limits']), 'Missing crossing result.')
            for limit, crossing in zip(plan['limits'], result['crossings']):
                expected = {'limit': limit, 'b_sep': first_crossing(seps, Q, limit),
                            'b_L': first_crossing(hs, 2 * Q, limit), 'b_star': first_crossing(exact, Q, limit)}
                require(crossing == expected, 'Saved crossing differs.')
            checked.append(index)
        except TimeoutError as error:
            failures.append({'index': index, 'reason': 'verification_timeout'})
            failures.extend({'index': later, 'reason': 'unattempted_after_verification_cap'}
                            for later in range(index + 1, len(statuses)))
            break
        except Exception as error:
            failures.append({'index': index, 'reason': repr(error)})
        write_json(output / 'verification-partial.json', {'checked_instances': checked, 'failures': failures})
    signal.setitimer(signal.ITIMER_REAL, 0)
    report = {'checked_instances': checked, 'failures': failures, 'wall_seconds': time.monotonic() - start,
              'method': 'Independent scalar exhaustive label correction and exact integer certificate checks.'}
    write_json(output / 'verification.json', report)
    write_json(output / 'manifest.json', {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != 'manifest.json'})
    print(json.dumps(report))
    return 1 if failures else 0


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == '_worker':
        worker(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif sys.argv[1] == '_verify':
        sys.exit(verify(sys.argv[2]))
    elif sys.argv[1] == 'verify':
        destination = Path(sys.argv[2]).resolve()
        settings = json.loads((destination / 'plan.json').read_text())
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), '_verify', str(destination)],
                                     timeout=settings['limits_seconds']['verification'])
            sys.exit(process.returncode)
        except subprocess.TimeoutExpired:
            write_json(destination / 'verification-timeout.json', {'status': 'timeout', 'verified': False})
            sys.exit(1)
    else:
        raise SystemExit('Use run PLAN OUTPUT or verify OUTPUT.')
