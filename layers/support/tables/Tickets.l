---
name: Tickets
description: One row per support ticket, with its status and the agent on it.
keywords: [ticket, case, request, issue]
---
@OrderBy(Tickets, "ticket_id");
Tickets(ticket_id:, status:, agent_id:, opened_at:) :-
  tickets(ticket_id:, status:, agent_id:, opened_at:);
