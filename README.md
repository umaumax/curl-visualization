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

## screenshots
### sequential
![1-1-sequential-summary](https://github.com/user-attachments/assets/95366624-39ef-4d37-8feb-dbd2fdd4076d)
![1-2-sequential-requests](https://github.com/user-attachments/assets/37191152-e95d-47b7-847c-358ad9ace1d3)
![1-3-sequential-timeline](https://github.com/user-attachments/assets/d086bc33-bb53-4747-b11b-f18df6778b28)

### parallel
![2-1-parallel-summary](https://github.com/user-attachments/assets/b18f8790-6849-4590-a79e-562525edb24a)
![2-2-parallel-requests](https://github.com/user-attachments/assets/24a8e0c5-d342-4102-9d87-09e1ff9d5df5)
![2-3-parallel-timeline](https://github.com/user-attachments/assets/507efe1c-cfb1-4457-bd2d-8314dd00a1a6)
