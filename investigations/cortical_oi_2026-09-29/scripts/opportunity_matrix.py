#!/usr/bin/env python3
"""
Generate opportunity matrix from archaeology data.
Loads the JSON files produced by the subagents and creates a CSV of experimental opportunities.
"""

import json
import os
from pathlib import Path

def load_json(filename):
    """Load JSON file, return empty list if not found or error."""
    path = Path(filename)
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def main():
    # Load all archaeology data
    prior_art = load_json('prior_art.json')
    cortical_assets = load_json('cortical_assets.json')
    adaptive_exp = load_json('adaptive_exp.json')
    neural_prediction = load_json('neural_prediction.json')
    plasticity_protocols = load_json('plasticity_protocols.json')
    software_inventory = load_json('software_inventory.json')
    
    print(f"Loaded: {len(prior_art)} prior art, {len(cortical_assets)} cortical assets, {len(adaptive_exp)} adaptive frameworks, {len(neural_prediction)} neural prediction methods, {len(plasticity_protocols)} plasticity protocols, {len(software_inventory)} software tools.")
    
    opportunities = []
    
    # Opportunity 1: Use adaptive experimentation to optimize stimulation parameters for burst suppression
    opp = {
        "Pergunta": "Can Bayesian optimization find stimulation parameters that reliably reduce burst rate in cortical networks?",
        "Prior Art": "Bayesian optimization used in experimental design (see adaptive_exp.json); closed-loop stimulation studied in prior art (e.g., adaptive enhancement of learning protocol 2013, model-free ACLS 2021).",
        "Ferramentas existentes": "Software: Gaussian process libraries (scikit-learn, GPyTorch); our infrastructure already does closed-loop stimulation and burst detection.",
        "Dados necessários": "Burst rate as a function of stimulation parameters (amplitude, pulse count, pulse width, interval). Need to collect data from multiple stimulation conditions.",
        "Experimento possível": "Run a closed-loop experiment where the stimulation parameters are selected by a Bayesian optimizer aiming to minimize burst rate over successive trials.",
        "Hipótese": "Bayesian optimization will find stimulation parameters that reduce burst rate below baseline within N trials.",
        "Métrica": "Burst rate (bursts per second) and number of trials to reach significant reduction.",
        "Falsificação": "If burst rate does not decrease significantly after a reasonable number of trials (e.g., 20) compared to baseline, the hypothesis is falsified.",
        "Potencial científico": "Alto - demonstrates autonomous parameter search in neural closed-loop systems.",
        "Potencial tecnológico": "Médio - could lead to adaptive stimulation protocols for therapeutic devices."
    }
    opportunities.append(opp)
    
    # Opportunity 2: Test if STDP-like protocols can be induced in cortical networks using our closed-loop burst-triggered stimulation
    opp = {
        "Pergunta": "Does burst-triggered stimulation with precise spike-timing induce spike-timing-dependent plasticity-like changes in burst probability?",
        "Prior Art": "STDP is well-established (see plasticity_protocols.json); closed-loop stimulation shown to modulate networks (prior art).",
        "Ferramentas existentes": "Our infrastructure can detect bursts and deliver stimulation with controlled timing (we have StimDesign and precise timing via the loop).",
        "Dados necessários": "Pre- and post-stimulation burst statistics, requiring baseline recording, stimulation recording, and post-stimulation recording.",
        "Experimento possível": "Record baseline burst rate, then run a closed-loop experiment where stimulation is delivered with a fixed delay relative to detected bursts (e.g., +10ms for LTP-like, -10ms for LTD-like), then measure post-stimulation burst rate changes.",
        "Hipótese": "Post-burst stimulation (+10ms) will increase burst rate (LTP-like), while pre-burst stimulation (-10ms) will decrease burst rate (LTD-like).",
        "Métrica": "Change in burst rate (post - pre) for each stimulation timing condition.",
        "Falsificação": "If the burst rate changes do not follow the expected timing-dependent pattern (i.e., no significant difference between +10ms and -10ms conditions), the hypothesis is falsified.",
        "Potencial científico": "Alto - would demonstrate plasticity-like changes in cortical networks under closed-loop stimulation.",
        "Potencial tecnológico": "Alto - could inform therapeutic stimulation protocols for neural reorganization."
    }
    opportunities.append(opp)
    
    # Opportunity 3: Use latent factor analysis (LFADS) to predict burst likelihood from population dynamics and improve prediction accuracy
    opp = {
        "Pergunta": "Can LFADS-predicted neural states improve burst prediction accuracy over simple interval-based models?",
        "Prior Art": "LFADS is a state-of-the-art method for predicting neural dynamics (see neural_prediction.json); burst prediction is a key goal in neuroscience (see prior art on burst-based encoding).",
        "Ferramentas existentes": "We can record population spike data (we already do); we would need to implement or use an LFADS library (software inventory shows we could reuse or build).",
        "Dados necessários": "High-resolution spike trains from multiple electrodes to train LFADS model, then test prediction of upcoming bursts.",
        "Experimento possível": "Train an LFADS model on recorded spike data (excluding bursts to avoid circularity), then use the latent state to predict burst probability in held-out data, compare to baseline interval-based predictor.",
        "Hipótese": "LFADS-predicted neural state will yield higher burst prediction accuracy (lower contradiction rate) than a simple ISI-based predictor.",
        "Métrica": "Contradiction rate (failed predictions) using LFADS vs. baseline predictor.",
        "Falsificação": "If the contradiction rate using LFADS is not significantly lower than the baseline predictor, the hypothesis is falsified.",
        "Potencial científico": "Alto - improves understanding of neural precursors to bursts.",
        "Potencial tecnológico": "Médio - could lead to better closed-loop neuroprosthetics."
    }
    opportunities.append(opp)
    
    # Opportunity 4: Test network-level plasticity via burst-modulation closed-loop stimulation (adaptive stimulation based on burst features)
    opp = {
        "Pergunta": "Does adaptive stimulation based on burst features (e.g., spike count, synchrony) lead to lasting changes in network burst dynamics?",
        "Prior Art": "Adaptive stimulation studied (see prior art); plasticity protocols include burst modulation concepts (see plasticity_protocols.json).",
        "Ferramentas existentes": "We can extract burst features (spike count, synchrony) from our detected bursts and adjust stimulation parameters accordingly.",
        "Dados necessários": "Burst features and stimulation parameters over time, plus post-stimulation baseline to assess lasting changes.",
        "Experimento possível": "Run a closed-loop experiment where stimulation amplitude or pulse count is scaled by a feature of the detected burst (e.g., higher spike count -> stronger stimulation), then measure burst rate during and after the experiment to see if changes persist.",
        "Hipótese": "Adaptive stimulation based on burst features will produce lasting changes in burst rate after stimulation ends, indicating network plasticity.",
        "Métrica": "Burst rate during stimulation and in a post-stimulation baseline period, compared to pre-stimulation baseline.",
        "Falsificação": "If burst rate returns to pre-stimulation levels immediately after stimulation ends, the hypothesis is falsified (no lasting change).",
        "Potencial científico": "Alto - demonstrates closed-loop induction of network plasticity.",
        "Potencial tecnológico": "Alto - could lead to adaptive therapeutic devices that promote long-term neural reorganization."
    }
    opportunities.append(opp)
    
    # Opportunity 5: Use software tools to replay real Cortical Cloud data and test if our closed-loop infrastructure works with biological data
    opp = {
        "Pergunta": "Does our closed-loop OI infrastructure work with real cortical organoid data from Cortical Cloud?",
        "Prior Art": "We have demonstrated integration with the simulator (see our prior experiments); Cortical Cloud provides real data (see cortical_assets.json).",
        "Ferramentas existentes": "Our infrastructure (CorticalOIController, etc.) is designed to work with the CL API; we can use h5py to read data and simulate the API.",
        "Dados necessários": "A real Cortical Cloud recording (HDF5 format) to replay via CL_SDK_REPLAY_PATH.",
        "Experimento possível": "Set CL_SDK_REPLAY_PATH to a real recording and run our standard closed-loop integration experiment, measuring burst rate, contradiction rate, etc.",
        "Hipótese": "Our infrastructure will function correctly with real data, producing meaningful burst detection, contradiction logging, and closed-loop stimulation.",
        "Métrica": "Successful execution of the experiment (no crashes), production of expected outputs (HDF5 with data streams, logs).",
        "Falsificação": "If the experiment fails to run or produces corrupt data, the hypothesis is falsified (our infrastructure is not compatible with real data without modification).",
        "Potencial científico": "Alto - validates infrastructure for real biological data.",
        "Potencial tecnológico": "Alto - enables real scientific discovery with Cortical Cloud."
    }
    opportunities.append(opp)
    
    # Write opportunities to CSV
    import csv
    output_file = 'opportunity_matrix.csv'
    if opportunities:
        keys = opportunities[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(opportunities)
        print(f"Opportunity matrix written to {output_file} with {len(opportunities)} opportunities.")
    else:
        print("No opportunities generated.")
    
    # Also write a JSON version for easier processing
    json_file = 'opportunity_matrix.json'
    with open(json_file, 'w') as f:
        json.dump(opportunities, f, indent=2)
    print(f"Opportunity matrix also written to {json_file}.")

if __name__ == '__main__':
    main()