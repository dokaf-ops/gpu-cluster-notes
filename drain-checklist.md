# drain checklist

1. check orchestrator queue — make sure no new jobs are pending for the target node
2. initiate drain via cli, confirm status flips to 'draining'
3. wait for active job to hit next checkpoint
4. verify node is fully idle (gpu-smi, check for orphan processes)
5. pull node from monitoring rotation
6. if hardware swap: power down, swap, POST, burn-in for 30 min
7. re-add to pool, verify first job assignment completes clean

note: step 2-3 has the race condition window. watch it.