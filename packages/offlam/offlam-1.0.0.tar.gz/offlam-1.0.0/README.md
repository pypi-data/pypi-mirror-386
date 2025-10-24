# Lifted Action Models Learning from Partial Traces
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This repository contains the official code of the Offline Learning of Action Models (OffLAM) algorithm.

### Installation
```
pip install offlam
```

### Example usage
```

from offlam.algorithm import learn
model = learn('path/to/domain.pddl', ['path/to/trace0', 'path/to/trace1'])
print(model)
```

## Custom domain learning
The OffLAM algorithm can be run for learning from traces with partially observable states, partially observable actions, 
and partially observable states and actions.
For running OffLAM on a custom domain, you need to provide an input domain file `'path/to/domain.pddl'` and a 
list of plan trace files `['path/to/trace0', 'path/to/trace1', etc.]`. 
The input planning domain must contain the predicates, object types, and operator signatures, 
an example of (empty) input planning domain is `Analysis/Benchmarks/testworld.pddl`.
Examples of input plan traces with partial states can be found in the directory 
`offlam/Analysis/Input traces/testworld/partial_states`, notice that OffLAM can learn a planning domain from 
plan traces of different environments (e.g. it is possible to learn a planning domain from small environments 
and exploit the learned domain in large environments). 


## Citations
```
@article{lamanna2024lifted,
  title={Lifted Action Models Learning from Partial Traces},
  author={Lamanna, Leonardo and Serafini, Luciano and Saetti, Alessandro and Gerevini, Alfonso and Traverso, Paolo},
  journal={Artificial Intelligence},
  volume={339},
  pages={104256},
  year={2025},
  publisher={Elsevier}
}
```

## License
This project is licensed under the MIT License - see the [LICENSE](/LICENSE) file for details.
