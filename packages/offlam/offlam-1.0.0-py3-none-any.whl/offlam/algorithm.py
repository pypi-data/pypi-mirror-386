import shutil
import sys
from shutil import copyfile
from timeit import default_timer
from typing import List

from offlam import Configuration
from offlam.src.Action import Action
from offlam.src.ActionModel import ActionModel
from offlam.src.Learner import *
from offlam.Util.generate_dataframe import save_dataframe
from offlam.Util.plot_results import plot_overall_prec_recall


def learn_from_traces(l, traces, trace_names, greedy=False):
    learning_in_progress = True

    prev_cert_size = 0
    prev_uncert_size = np.inf

    l.traces = traces

    while learning_in_progress:
        learning_in_progress = False

        for input_trace, trace_name in zip(traces, trace_names):

            # Learn action model from problem instance
            l.learn_offline(input_trace, greedy=greedy)

            cert_size = sum([len(op.eff_pos_cert) + len(op.eff_neg_cert) + len(op.precs_cert)
                             for op in l.action_model.operators])
            uncert_size = sum([len(op.eff_pos_uncert) + len(op.eff_neg_uncert) + len(op.precs_uncert)
                               for op in l.action_model.operators])

            if cert_size > prev_cert_size or uncert_size < prev_uncert_size:
                prev_cert_size = cert_size
                prev_uncert_size = uncert_size
                learning_in_progress = True

    return traces


def check_inconsistency(l, traces):
    inconsistent_preds = set()
    for trace in traces:
        for k, obs in enumerate(trace.observations):
            obs_positive_literals = set.union(*obs.positive_literals.values())
            obs_negative_literals = set.union(*obs.negative_literals.values())

            assert obs_positive_literals is not None
            inconsistent_preds |= {p.split('(')[0] for p in obs_positive_literals if f'not_{p}' in obs_negative_literals}

    # Remove predicate from action models
    for p in inconsistent_preds:
        print(f'[Debug] Removing predicate {p}')
        l.action_model.remove_predicate(p)

    # Remove predicate from trace observations
    [trace.remove_predicates(inconsistent_preds) for trace in traces]

    return traces


# TODO: move this in action model class
def replace_predicate(l, old_preds):

    # Replace predicate in predicate list
    predicates_old = [p for p in l.action_model.predicates if p.split('(')[0] in old_preds]
    l.action_model.predicates = [p for p in l.action_model.predicates if p not in predicates_old]
    l.action_model.predicates += [f"a_{p}" for p in predicates_old]
    l.action_model.predicates += [f"b_{p}" for p in predicates_old]

    precs_uncert_new = defaultdict(set)
    precs_cert_new = defaultdict(set)
    effs_pos_uncert_new = defaultdict(set)
    effs_pos_cert_new = defaultdict(set)
    effs_neg_uncert_new = defaultdict(set)
    effs_neg_cert_new = defaultdict(set)

    # Replace predicate in operator action model
    for op in l.action_model.operators:

        # Replace predicate in operator uncertain preconditions
        matched_precs = {p for p in op.precs_uncert if p.split('(')[0] in old_preds}
        precs_uncert_new_pos = {f'a_{p}' for p in matched_precs}
        precs_uncert_new_neg = {f'b_{p}' for p in matched_precs}
        precs_uncert_new[op.operator_name] = precs_uncert_new_pos | precs_uncert_new_neg
        op.precs_uncert = op.precs_uncert - matched_precs | precs_uncert_new[op.operator_name]

        # Replace predicate in operator certain preconditions
        matched_precs = {p for p in op.precs_cert if p.split('(')[0] in old_preds}
        precs_cert_new_pos = {f'a_{p}' for p in matched_precs}
        precs_cert_new_neg = {f'b_{p}' for p in matched_precs}
        precs_cert_new[op.operator_name] = precs_cert_new_pos | precs_cert_new_neg
        op.precs_cert = op.precs_cert - matched_precs | precs_cert_new[op.operator_name]

        # Replace predicate in operator uncertain positive effects
        matched_effs = {p for p in op.eff_pos_uncert if p.split('(')[0] in old_preds}
        effs_pos_uncert_new_pos = {f'a_{p}' for p in matched_effs}
        effs_pos_uncert_new_neg = {f'b_{p}' for p in matched_effs}
        effs_pos_uncert_new[op.operator_name] = effs_pos_uncert_new_pos | effs_pos_uncert_new_neg
        op.eff_pos_uncert = op.eff_pos_uncert - matched_effs | effs_pos_uncert_new[op.operator_name]

        # Replace predicate in operator certain positive effects
        matched_effs = {p for p in op.eff_pos_cert if p.split('(')[0] in old_preds}
        effs_pos_cert_new_pos = {f'a_{p}' for p in matched_effs}
        effs_pos_cert_new_neg = {f'b_{p}' for p in matched_effs}
        effs_pos_cert_new[op.operator_name] = effs_pos_cert_new_pos | effs_pos_cert_new_neg
        op.eff_pos_cert = op.eff_pos_cert - matched_effs | effs_pos_cert_new[op.operator_name]

        # Replace predicate in operator uncertain negative effects
        matched_effs = {p for p in op.eff_neg_uncert if p.split('(')[0] in old_preds}
        effs_neg_uncert_new_pos = {f'a_{p}' for p in matched_effs}
        effs_neg_uncert_new_neg = {f'b_{p}' for p in matched_effs}
        effs_neg_uncert_new[op.operator_name] = effs_neg_uncert_new_pos | effs_neg_uncert_new_neg
        op.eff_neg_uncert = op.eff_neg_uncert - matched_effs | effs_neg_uncert_new[op.operator_name]

        # Replace predicate in operator certain negative effects
        matched_effs = {p for p in op.eff_neg_cert if p.split('(')[0] in old_preds}
        effs_neg_cert_new_pos = {f'a_{p}' for p in matched_effs}
        effs_neg_cert_new_neg = {f'b_{p}' for p in matched_effs}
        effs_neg_cert_new[op.operator_name] = effs_neg_cert_new_pos | effs_neg_cert_new_neg
        op.eff_neg_cert = op.eff_neg_cert - matched_effs | effs_neg_cert_new[op.operator_name]

    for op_name, ground_actions in l.action_model.ground_actions.items():

        if sum([len(precs_uncert_new[op_name]), len(precs_cert_new[op_name]), len(effs_pos_uncert_new[op_name]),
                len(effs_pos_cert_new[op_name]), len(effs_neg_cert_new[op_name]), len(effs_neg_uncert_new[op_name])]) > 0:

            # Replace predicate in uncertain preconditions of all ground actions
            for a in ground_actions:

                if len(precs_uncert_new[op_name]) > 0:
                    a_matched_precs = {p for p in a.precs_uncert if p.split('(')[0] in old_preds}
                    precs_uncert_new_pos = {f'a_{p}' for p in a_matched_precs}
                    precs_uncert_new_neg = {f'b_{p}' for p in a_matched_precs}
                    a_precs_uncert_new = precs_uncert_new_pos | precs_uncert_new_neg
                    a.precs_uncert = a.precs_uncert - a_matched_precs | a_precs_uncert_new

                # Replace predicate in certain preconditions of all ground actions
                if len(precs_cert_new[op_name]) > 0:
                    a_matched_precs = {p for p in a.precs_cert if p.split('(')[0] in old_preds}
                    precs_cert_new_pos = {f'a_{p}' for p in a_matched_precs}
                    precs_cert_new_neg = {f'b_{p}' for p in a_matched_precs}
                    a_precs_cert_new = precs_cert_new_pos | precs_cert_new_neg
                    a.precs_cert = a.precs_cert - a_matched_precs | a_precs_cert_new

                # Replace predicate in uncertain positive effects of all ground actions
                if len(effs_pos_uncert_new[op_name]) > 0:
                    a_matched_effs = {p for p in a.eff_pos_uncert if p.split('(')[0] in old_preds}
                    effs_pos_uncert_new_pos = {f'a_{p}' for p in a_matched_effs}
                    effs_pos_uncert_new_neg = {f'b_{p}' for p in a_matched_effs}
                    a_effs_pos_uncert_new = effs_pos_uncert_new_pos | effs_pos_uncert_new_neg
                    a.eff_pos_uncert = a.eff_pos_uncert - a_matched_effs | a_effs_pos_uncert_new

                # Replace predicate in certain positive effects of all ground actions
                if len(effs_pos_cert_new[op_name]) > 0:
                    a_matched_effs = {p for p in a.eff_pos_cert if p.split('(')[0] in old_preds}
                    effs_pos_cert_new_pos = {f'a_{p}' for p in a_matched_effs}
                    effs_pos_cert_new_neg = {f'b_{p}' for p in a_matched_effs}
                    a_effs_pos_cert_new = effs_pos_cert_new_pos | effs_pos_cert_new_neg
                    a.eff_pos_cert = a.eff_pos_cert - a_matched_effs | a_effs_pos_cert_new

                # Replace predicate in uncertain negative effects of all ground actions
                if len(effs_neg_uncert_new[op_name]) > 0:
                    a_matched_effs = {p for p in a.eff_neg_uncert if p.split('(')[0] in old_preds}
                    effs_neg_uncert_new_pos = {f'a_{p}' for p in a_matched_effs}
                    effs_neg_uncert_new_neg = {f'b_{p}' for p in a_matched_effs}
                    a_effs_neg_uncert_new = effs_neg_uncert_new_pos | effs_neg_uncert_new_neg
                    a.eff_neg_uncert = a.eff_neg_uncert - a_matched_effs | a_effs_neg_uncert_new

                # Replace predicate in certain negative effects of all ground actions
                if len(effs_neg_cert_new[op_name]) > 0:
                    a_matched_effs = {p for p in a.eff_neg_cert if p.split('(')[0] in old_preds}
                    effs_neg_cert_new_pos = {f'a_{p}' for p in a_matched_effs}
                    effs_neg_cert_new_neg = {f'b_{p}' for p in a_matched_effs}
                    a_effs_neg_cert_new = effs_neg_cert_new_pos | effs_neg_cert_new_neg
                    a.eff_neg_cert = a.eff_neg_cert - a_matched_effs | a_effs_neg_cert_new


# Split only negative atoms
def fill_fictitious(l, filled_traces):
    trace_modified = False
    for k, trace in enumerate(filled_traces):

        if trace_modified:
            break

        print(f'[Info] Adding forward fictitious predicates to trace: {trace.name}')

        # Fill traces with fictitious predicates in forward states
        for i in range(len(trace.observations) - 1):

            if type(trace.actions[i]) == Action:

                # pos_i = set.union(*trace.observations[i].positive_literals.values())
                neg_i = set.union(*trace.observations[i].negative_literals.values())

                pos_j = set.union(*trace.observations[i + 1].positive_literals.values())
                neg_j = set.union(*trace.observations[i + 1].negative_literals.values())

                adding_fict_preds = True

                while adding_fict_preds:

                    neg_unknown = [p[4:] for p in neg_i if p[4:] not in pos_j and p not in neg_j]

                    neg_objs = list({p.split('(')[1] for p in neg_unknown})
                    neg_unknown = [p for p in neg_unknown if p.split('(')[1] == neg_objs[0]]
                    assert len({p.split('(')[1] for p in neg_unknown}) <= 1

                    if len(neg_unknown) > 0:

                        neg_pred_names = set([p.split('(')[0] for p in neg_unknown])
                        neg_pred_names = sorted(list(neg_pred_names))
                        neg_split_names = [[f"{chr(97 + k)}_{p}" for k in range(2)] for p in neg_pred_names]
                        for v in range(len(filled_traces)):
                            filled_traces[v].rename_pred(neg_pred_names, neg_split_names)

                        # Replace predicate in the planning domain with fictitious predicates
                        replace_predicate(l, neg_pred_names)

                        for neg_pred_name in neg_pred_names:

                            for p in [p for p in neg_unknown if p.startswith(neg_pred_name)]:

                                neg_split = [f"{chr(97 + i)}_{p}" for i in range(2)]  # split "p" into "p1" and "p2"

                                # Add "p1" and "not_p2" to the next observation
                                trace.observations[i + 1].positive_literals[neg_split[0].split('(')[0]].add(neg_split[0])
                                trace.observations[i + 1].negative_literals[neg_split[1].split('(')[0]].add(f"not_{neg_split[1]}")
                                trace_modified = True

                        if trace_modified:
                            print(f'[Info] Adding {len(neg_pred_names) * 2} forward fictitious predicates (neg unknown) {neg_pred_names}')
                            return trace_modified, k
                    else:
                        adding_fict_preds = False

    return trace_modified, k


def learn(domain_path: str,
          trace_paths: List[str],
          online_eval: bool = False):

    now = default_timer()

    l = Learner(input_domain_path=domain_path)

    traces = [l.parse_trace(t) for t in trace_paths]
    [t.set_objects(l.action_model) for t in traces]

    filled_traces = learn_from_traces(l, traces, trace_paths, greedy=True)

    trace_modified = True
    while trace_modified:
        start = default_timer()
        trace_modified, trace_idx = fill_fictitious(l, filled_traces)
        print(f'Time for filling (forward): {default_timer() - start}')

        start = default_timer()
        filled_traces = learn_from_traces(l, filled_traces, trace_paths, greedy=True)
        print(f'Time for learning: {default_timer() - start}')

        start = default_timer()
        filled_traces = check_inconsistency(l, filled_traces)
        print(f'Time for checking consistency: {default_timer() - start}')

    # Post process action model in order to remove fictitious predicates
    post_processed_action_model = l.post_process_action_model(l.action_model)

    post_processed_action_model.write('PDDL/domain_learned.pddl', eff_pos_uncertain=False, eff_neg_uncertain=False)

    print('\n\n')
    print(f'Number of processed traces: {len(traces)}')
    print(f'Total CPU time: {default_timer() - now}')

    if online_eval:
        l.eval_log('PDDL/domain_learned.pddl')

    with open('PDDL/domain_learned.pddl', 'r') as f:
        model = f.read()

    # Clean PDDL files
    shutil.rmtree("PDDL")

    return model