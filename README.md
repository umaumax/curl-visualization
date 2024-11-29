# curl-visualization

## how to collect data
``` bash
# only for mac
alias date=gdate

for i in $(seq 1 100); do
  # for mac
  time_offset=$(date +%s.%3N)
  {
    curl -o /dev/null -w '%{json}' https://www.google.com
    echo '{"time_offset":'$time_offset'}'
  } | jq -s add > curl.$i.json
done
cat curl.*.json | jq 'with_entries(select(.key|test("^time.*")))' | jq -s . > curl.time-results.json
```

## how to run
launch streamlit server by default json data
``` bash
streamlit run ./dashboard.py -- --default-json ./samples/curl.time-results.json
```
