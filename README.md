Beanstalk re-launched on august 6th 

Beanstalk's first post-replant season was 6075

## Subgraph Notes

- Add bean volume by order fill / listing fill (similar to pod volume). bean order vol + bean listing vol = bean vol. 
- If you run the following graphql query, you get 3 results. I think we should merge these into a single value. The same issue 
  may also exist for the hourly snapshots for season 6074. 
```
query MyQuery {
  podMarketplaceDailySnapshots(
    first: 10, where: {season: 6074}
  ) {
    totalBeanVolume
    totalPodVolume
    totalPodsFilled
    totalPodsListed
    timestamp
  }
}
```
