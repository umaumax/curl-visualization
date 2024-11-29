# curl-visualization

## how to collect data
``` bash
for i in $(seq 1 100); do
  curl -o /dev/null -w '%{json}' https://www.google.com > curl.$i.json
done
cat curl.*.json | jq 'with_entries(select(.key|test("^time.*")))' | jq -s . > curl.time-results.json
```

## how to run
launch streamlit server by default json data
``` bash
streamlit run ./dashboard.py -- --default-json ./samples/curl.time-results.json
```
