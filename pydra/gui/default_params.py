import os

default_params = {
        "directory": os.getcwd(),
        "filename": "",
        "n_trial_digits": 3,
        "n_trials": 1,
        "trial_number": 1,
        "inter_trial_time": 1,
        "inter_trial_unit": "s",
        "recording_triggers": (None, None),

        "inter_trial_ms": 0,  # for completeness, parameter updated automatically
        "trial_index": 0,  # for completeness, parameter updated automatically
        "event_names": [],  # for completeness, parameter updated automatically
        "targets": [],  # for completeness, parameter updated automatically
        "triggers": {},  # for completeness, parameter updated automatically
        "protocol": [],  # for completeness, parameter updated automatically
}
