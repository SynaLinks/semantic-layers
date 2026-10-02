---
name: Workload
description: Open tickets per support agent, busiest first.
keywords: [workload, load, backlog, agent]
---
import rules.OpenTickets.OpenTickets;

@OrderBy(Workload, "open_tickets", "DESC");
Workload(agent_id:, open_tickets? += 1) distinct :- OpenTickets(agent_id:);
