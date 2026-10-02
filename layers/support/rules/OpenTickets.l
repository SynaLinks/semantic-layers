---
name: OpenTickets
description: Tickets still waiting for an answer.
keywords: [open, pending, backlog, unresolved]
---
import tables.Tickets.Tickets;

@OrderBy(OpenTickets, "ticket_id");
OpenTickets(ticket_id:, agent_id:) distinct :- Tickets(ticket_id:, agent_id:, status: "open");
