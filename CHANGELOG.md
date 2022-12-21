# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2022-10-25

### Fixed

- Fix to beanstalk credit profile graph. Replaced area component `pods_issued` (included 
  harvested and unharvestable pods) with `pods_unharvestable`. This ensures that harvestable pods are not counted 
  as part of the total debt, making multiple pieces of this chart more accurate. 

## [1.0.0] - 2022-10-21

### Added
- First version of analytics website 