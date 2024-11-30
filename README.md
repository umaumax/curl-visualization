# curl-visualization

## how to collect data
sequential
``` bash
# only for mac
alias date=gdate

for i in $(seq 1 100); do
  time_offset=$(date +%s.%3N)
  {
    curl -o /dev/null -w '%{json}' https://www.google.com
    echo '{"time_offset":'$time_offset'}'
  } | jq -s add > curl.$i.json
done
cat curl.*.json | jq 'with_entries(select(.key|test("^time.*")))' | jq -s . > curl.time-results.json
```

parallel
``` bash
# only for mac
alias date=gdate

for i in $(seq 1 100); do
  sleep 0.001
  time_offset=$(date +%s.%3N)
  {
    curl -o /dev/null -w '%{json}' https://wallpapers.com/images/high/sunset-forest-4k-pc-art-3bov3n49o9j58x2s.webp
    echo '{"time_offset":'$time_offset'}'
  } | jq -s add > curl.$i.json &
done
wait
cat curl.*.json | jq 'with_entries(select(.key|test("^time.*")))' | jq -s . > curl.time-results.json
```

### NOTE
You can get a `time_redirect` field by a below command.
``` bash
curl -L -s -o /dev/null -w '%{json}' https://google.com | jq 'with_entries(select(.key|test("^time.*")))'
```

## how to run
launch streamlit server by default json data
``` bash
streamlit run ./dashboard.py -- --default-json ./samples/sequential/curl.time-results.json
streamlit run ./dashboard.py -- --default-json ./samples/parallel/curl.time-results.json
```

``` marmaid
gantt
    title cURL time_ prefix fields Timeline
    dateFormat  X
    axisFormat  
    section Metrics
    time_namelookup       :active, a1, 0, 1
    time_connect          :active, a2, 0, 2
    time_redirect         :active, a3, 0, 3
    time_appconnect       :active, a4, 0, 4
    time_pretransfer      :active, a5, 0, 5
    time_starttransfer    :active, a6, 0, 6
    time_posttransfer     :active, a7, 0, 7
    time_total            :active, a8, 0, 8
```
