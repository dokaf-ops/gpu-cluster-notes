# gpu-cluster-notes

working notes from ~14 months on a dedicated training cluster. contract reliability eng placed through staffing firm, embedded at a colo customer under NDA. i don't touch model code or weights — just keep the fabric up and the jobs running.

## fabric and node behavior

- 400g infiniband between gpu nodes, rail-optimized topology
- NCCL traffic is predictable once a job stabilizes but the first few minutes of a large run are brutal on the switches
- node thermals drift over time, especially the ones in the back of the row. fans ramp but the baseboard doesn't always report it cleanly
- we've had 3 NICs fail silently in the last 6 months — link stays up, but packet loss creeps until the job stalls. monitoring caught 2 of them, the third took 4 hours to isolate

## drain and resume

- drain procedure is mostly automated now but there's a 90-second window where the orchestrator can assign new work to a draining node if the timing is wrong
- resume after a node swap takes ~12 min if checkpoints are fresh, longer if the last checkpoint is stale
- we lost a 3-day job once because the checkpoint interval was set to 6h and the failure hit at 5h50m. now we push for 1h intervals on anything over 64 nodes

## straggler detection

- TODO: write up the prometheus query that catches stragglers before the job timeout fires
- basic idea: track per-node iteration time, alert if any node is >2 stddev slow for >5 min
- false positive rate is still too high, especially during checkpointing windows

## failure patterns

- GPU memory errors (ECC uncorrectable) — usually means the card is done, swap it
- NIC silent failures — see above
- PSU trips under peak load on older nodes, especially in summer
- orchestrator race condition on drain (known bug, vendor aware, no fix yet)

## open questions

- is there a better way to detect fabric degradation before it shows up in job metrics?
- checkpoint compression tradeoffs — we're not using it, should we be?
- TODO: dig into whether the baseboard thermal reporting issue is firmware or sensor

`gpu_fail_classifier.py` — stdin filter that classifies GPU failure log lines (dmesg, syslog, DCGM) into triage buckets: fatal vs warning-tier XIDs, ECC correctable/uncorrectable, row-remap exhaustion, NVLink CRC and replay errors, fabric faults, thermal throttling, NCCL timeouts. No dependencies, just pipe logs in. Written for the 2-am page where you need to know in ten seconds whether a node is coming back or needs a drain-and-replace.
