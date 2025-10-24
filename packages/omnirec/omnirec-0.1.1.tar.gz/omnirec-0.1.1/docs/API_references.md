# API Reference

## Dataset Management

::: omnirec.recsys_data_set.RecSysDataSet
    options:
      show_root_heading: true
      show_root_toc_entry: false
      members_order: source

## Data Loaders

::: omnirec.data_loaders.base.Loader
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.data_loaders.base.DatasetInfo
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.data_loaders.registry.register_dataloader
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.data_loaders.registry.list_datasets
    options:
      show_root_heading: true
      show_root_toc_entry: false

## Preprocessing Pipeline

::: omnirec.preprocess.base.Preprocessor
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.subsample.Subsample
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.core_pruning.CorePruning
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.feedback_conversion.MakeImplicit
    options:
      show_root_heading: true
      show_root_toc_entry: false

### Filtering

::: omnirec.preprocess.filter.TimeFilter
    options:
      show_root_heading: true
      show_root_toc_entry: false
      heading_level: 4

::: omnirec.preprocess.filter.RatingFilter
    options:
      show_root_heading: true
      show_root_toc_entry: false
      heading_level: 4

::: omnirec.preprocess.split.RandomCrossValidation
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.split.RandomHoldout
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.split.UserCrossValidation
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.split.UserHoldout
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.split.TimeBasedHoldout
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.preprocess.pipe.Pipe
    options:
      show_root_heading: true
      show_root_toc_entry: false

## Evaluation Metrics

::: omnirec.runner.evaluation.Evaluator
    options:
      show_root_heading: true
      show_root_toc_entry: false

### Metric Base Classes

::: omnirec.metrics.base.Metric
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.metrics.base.Metric.calculate
    options:
      show_root_heading: true
      show_root_toc_entry: false
      heading_level: 4

::: omnirec.metrics.base.MetricResult
    options:
      show_root_heading: true
      show_root_toc_entry: false

### Ranking Metrics
::: omnirec.metrics.ranking.HR
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.metrics.ranking.NDCG
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.metrics.ranking.Recall
    options:
      show_root_heading: true
      show_root_toc_entry: false

### Prediction Metrics
::: omnirec.metrics.prediction.MAE
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.metrics.prediction.RMSE
    options:
      show_root_heading: true
      show_root_toc_entry: false


## Experiment Planning
::: omnirec.runner.plan.ExperimentPlan
    options:
      show_root_heading: true
      show_root_toc_entry: false

## Runner Function
::: omnirec.util.run.run_omnirec
    options:
      show_root_heading: true
      show_root_toc_entry: false

## Coordinator Class
::: omnirec.runner.coordinator.Coordinator
    options:
      show_root_heading: true
      show_root_toc_entry: false

## Utility Functions

::: omnirec.util.util.set_random_state
    options:
      show_root_heading: true
      show_root_toc_entry: false

::: omnirec.util.util.get_random_state
    options:
      show_root_heading: true
      show_root_toc_entry: false
