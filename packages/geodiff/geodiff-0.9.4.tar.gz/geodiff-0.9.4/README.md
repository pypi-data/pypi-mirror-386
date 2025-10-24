Differentiable geometry representations for shape parameterization and optimization.


## Project Plan
### Stage 1: Initial Setup
- [x] Add Github Actions workflow for Github Pages.
- [x] Create first cut User Docs using Jupyter Books and MyST markdown.
    - [x] What is this package for?
    - [x] Add .gitignore for MyST markdown.
- [x] Launch Github Discussions for the project.
    - [x] Create introductory dicussion post.
- [x] Add MIT License.
- [x] Update pyproject.toml.
    - [x] Maintainers, license, license-file, keywords, classifiers, project urls.
- [x] Add Github Actions workflow for Github Release and PyPI publishing.
- [x] Add CHANGELOG.md to maintain release details.
- [x] Create first tag and push it to initiate first release and publish.

### Stage 2: Implement Geometry Representations
- [x] Install necessary dependencies
    - [x] numpy, matplotlib and pytorch.
- [x] Implement loss functions.
    - [x] Start with Chamfer loss.
- [x] Hicks-Henne bump functions.
    - [x] Implement the Hicks-Henne class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] CST parameterization.
    - [x] Implement the CST class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] NICE normalizing flow parameterization.
    - [x] Implement the NICE class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] RealNVP normalizing flow parameterization.
    - [x] Implement the RealNVP class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] NIGnet parameterization.
    - [x] Implement the NIGnet class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] NeuralODE parameterization.
    - [x] Implement the NeuralODE class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] Make Pre-Aux net modular by defining it separately from the invertible networks.
    - [x] Make Pre-Aux net modular for NICE.
    - [x] Change test script for NICE.
    - [x] Make Pre-Aux net modular for all representations.
    - [x] Change test scripts for all representations.
    - [x] Update documentation for all representations.
        - [x] Fix random seed for replicating results.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.


### Stage 3: Implement Latent Vectors for Geometry Representation
- [x] Add latent code functionality to Pre-Aux nets.
- [x] Add latent code functionality to NICE.
- [x] Add test script for training with latent code using autodecoder framework.
    - [x] Use NICE for the test script.
    - [x] Fit two latent codes to fit two differently rotated squares.
- [x] Add latent code functionality to all representations.
- [x] Merge with main branch.
- [x] Create a tag and push it to create a release.


### Stage 4: Improve Sampling of Points on the Closed Transform
- [x] Sample points in T [0, 1]^d using Farthest Point Sampling for Blue-noise properties.
    - [x] Write function to compute FPS.
    - [x] Create test script to visualize the point samples with specified number of points.
- [x] Transform T to points on closed manifold to preserve uniform point sampling.
    - [x] Use the arc cosine formulation for transforming t, s to phi, theta in 3D.
    - [x] Update test script to visualize point samples on closed manifold as well.
- [x] Merge with main branch.
- [x] Create a tag and push it to create a release.