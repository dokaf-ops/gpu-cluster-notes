# failure log

| date | node | symptom | root cause | time to resolve | notes |
|------|------|---------|------------|-----------------|-------|
| 2024-11-03 | gpu-node-47 | job stall, no errors in stdout | NIC silent failure, packet loss on ib0 | 4h | missed by monitoring, manual triage |
| 2024-10-19 | gpu-node-12 | ECC uncorrectable count spiking | bad VRAM | 2h (swap) | card was 11 months old |
| 2024-09-28 | gpu-node-31 | node dropped from job | PSU trip under peak load | 45min | summer temps, older chassis |