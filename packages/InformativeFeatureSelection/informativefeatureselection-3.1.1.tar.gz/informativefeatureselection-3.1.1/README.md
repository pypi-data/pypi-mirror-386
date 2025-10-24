# Install

`pip install InformativeFeatureSelection`

## Features

* Several implementations of feature selection algorithms based on discriminant analysis
* Binary implementation of Informative Normalized Difference Index (INDI)
* Multiclass implementation of INDI 

INDI may be extremely usefully in hyperspectral imaging analysis.

Implemented algorithms were proposed in the following papers:
1. [Paringer RA, Mukhin AV, Kupriyanov AV. Formation of an informative index for recognizing specified 
objects in hyperspectral data. Computer Optics 2021; 45(6): 873-878. DOI: 10.18287/2412-6179-CO-930.](http://www.computeroptics.ru/KO/PDF/KO45-6/450611.pdf)

2. [Mukhin, A., Paringer, R. and Ilyasova, N., 2021, September. Feature selection algorithm with feature space
separability estimation using discriminant analysis. In 2021 International Conference on Information Technology
and Nanotechnology (ITNT) (pp. 1-4). IEEE.](https://ieeexplore.ieee.org/document/9649144)

## Requirements

To simplify usage, two Docker images were created:

1. `banayaki/feature-selection:base`
This image serves as a base image for InformativeFeatureSelection.
It includes the necessary `python` and its packages.

2. `banayaki/feature-selection:notebook`
This image serves as an extension of the base image for InformativeFeatureSelection.
It includes an additional tool: Jupyter Notebook.
The Jupyter server starts automatically when the container begins.

### How to use them?

Just run the following command:

```bash
docker container run --rm -p 8888:8888 -v ./project:/home/workdir banayaki/feature-selection:notebook
```

Then just copy jupyter's token from container's log.


## Usage example

See jupyter notebook file in `examples` folder. 

## License

[MIT License](LICENSE)
