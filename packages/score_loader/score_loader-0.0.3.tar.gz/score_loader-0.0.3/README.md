# Score.dev Python loader

Python implementation of the [score.dev](https://docs.score.dev/docs/) specification, allowing to load workload definition and applying a first pass of evaluation for `${metadata...}` placeholders.

`${resources...}` placeholders must be evaluated after provisioning of the resources, cannot be done while loading the workload definition.


## Usage

`pip install score-loader`

or

`uv add score-loader`

then in your code:

```
from score_loader.loader import load_score_file

workload = load_score_file("score.yml")
```

## Unit tests

`uv run pytest`


