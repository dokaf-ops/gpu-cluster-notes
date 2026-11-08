# nccl timeout pattern on mixed-revision nodes

started seeing this maybe 6 weeks ago, happens 1-2x per week on the training cluster. not every time, which makes it annoying.

## symptoms in order

1. job runs fine for 4-8 hours, no errors, throughput looks normal
2. one node starts logging `NCCL WARN Timeout waiting for message` — always rank 0 on the affected node, not the whole job
3. within ~90 seconds every other rank on that same switch leaf hits the same timeout
4. job hangs, doesn't crash. scheduler doesn't kill it because the heartbeat is still alive from the other nodes
5. have to manually drain the node and restart the job

## what i checked first

- cables: swapped the 400g optics on the suspect node, no change
- firmware: node was on an older NIC firmware rev (thought this was it). upgraded, same thing happened 3 days later
- thermals: GPU temps fine, switch ASIC temp fine, ambient was 71F which is normal for that row
- link flaps: checked the switch counters, zero link flaps before or during the event. no CRC errors either

## dead ends

- thought it was the NCCL version mismatch because the suspect node got reimaged a week before and pulled a newer NCCL from the container. matched versions across all nodes, still happened
- tried pinning NCCL_SOCKET_IFNAME thinking it was picking up the wrong interface. no difference
- opened a ticket with the switch vendor, they said counters look clean on their side

## what i think is happening

the nodes that fail are all from a specific hardware revision — different baseboard, slightly different PCIe topology. the NCCL allreduce is tree-based and i think the timing on the PCIe transfers is just different enough on those boards that under sustained load one rank falls behind and the timeout fires. but i can't prove it because i don't have access to the NCCL debug logs at that level (need a rebuild with NCCL_DEBUG=INFO and the customer hasn't approved the downtime).

## TODO

- ask if we can schedule a 2-hour maintenance window to run with NCCL_DEBUG=INFO and reproduce
- check if the other site has the same board revision mix or if they're all uniform
- still don't understand why the scheduler heartbeat stays alive when the ranks are hung — is the heartbeat on a different thread? need to look at the orchestrator code