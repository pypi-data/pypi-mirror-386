<img src="https://github.com/akensert/molcraft/blob/main/docs/_static/molcraft-logo.png" alt="molcraft-logo", width="90%">

**Deep Learning on Molecules**: A Minimalistic GNN package for Molecular ML.

> [!NOTE]  
> In progress.

## Installation

For CPU users:

```bash
pip install --pre molcraft
```

For GPU users:
```bash
pip install --pre molcraft[gpu]
```

## Examples 

```python
from molcraft import features
from molcraft import descriptors
from molcraft import featurizers 
from molcraft import layers
from molcraft import models 
import keras

featurizer = featurizers.MolGraphFeaturizer(
    atom_features=[
        features.AtomType(),
        features.NumHydrogens(),
        features.Degree(),
    ],
    bond_features=[
        features.BondType(),
        features.IsRotatable(),
    ],
    super_node=True,
    self_loops=True,
    include_hydrogens=False,
)

graph = featurizer([('N[C@@H](C)C(=O)O', 2.5), ('N[C@@H](CS)C(=O)O', 1.5)])
print(graph)

model = models.GraphModel.from_layers(
    [
        layers.Input(graph.spec),
        layers.NodeEmbedding(dim=128),
        layers.EdgeEmbedding(dim=128),
        layers.GraphConv(units=128),
        layers.GraphConv(units=128),
        layers.GraphConv(units=128),
        layers.GraphConv(units=128),
        layers.Readout(),
        keras.layers.Dense(units=1024, activation='elu'),
        keras.layers.Dense(units=1024, activation='elu'),
        keras.layers.Dense(1)
    ]
)

pred = model(graph)
print(pred)

# featurizers.save_featurizer(featurizer, '/tmp/featurizer.json')
# models.save_model(model, '/tmp/model.keras')

# loaded_featurizer = featurizers.load_featurizer('/tmp/featurizer.json')
# loaded_model = models.load_model('/tmp/model.keras')
```

