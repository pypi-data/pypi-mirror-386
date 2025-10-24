if __name__ == "__main__":
    import sys
    import os
    import numpy as np
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    __package__ = "minimalANN"
    from minimalANN import network, layer

    nn = network.NeuralNetwork()

    nn.layers.append(layer.Layer(1, 2, "sigmoid"))
    nn.layers[0].weights = np.array([[-0.27], [-0.41]])
    nn.layers[0].bias = np.array([[-0.48], [-0.13]])

    nn.layers.append(layer.Layer(2, 1, "linear"))
    nn.layers[1].weights = np.array([[0.09, -0.17]])
    nn.layers[1].bias = np.array([[0.48]])

    X = np.array([[1]])
    y = np.array([1.707])

    nn = nn.train(X, y, 1, verbose=False)
    print(nn.weights)
