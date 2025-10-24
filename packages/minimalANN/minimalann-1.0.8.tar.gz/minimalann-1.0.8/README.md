# minimalANN

## How to use?

Example :-
Suppose this is the network architecture-

![Network architecture](minimalANN/assets/architecture.png)

To implement the above architecture, we can use the following code -

```python
import numpy as np
import minimalANN.network as network
import minimalANN.layer as layer

nn = network.NeuralNetwork()

nn.layers.append(layer.Layer(1, 2, "sigmoid"))
nn.layers[0].weights = np.array([[-0.27], [-0.41]])
nn.layers[0].bias = np.array([[-0.48], [-0.13]])

nn.layers.append(layer.Layer(2, 1, "linear"))
nn.layers[1].weights = np.array([[0.09, -0.17]])
nn.layers[1].bias = np.array([[0.48]])

X = np.array([[1]])
y = np.array([1.707])

nn = nn.train(X, y, 1)
print(nn.weights)
```
