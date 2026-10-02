# Examples

This repository's `layers/` folder holds two example layers, installable from
it:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --list
```

## sales

Orders and customers: what a customer is, which orders count as sales,
revenue, and the customers who bought.

=== "concepts/Customer.l"

    ```prolog
    --8<-- "layers/sales/concepts/Customer.l"
    ```

=== "concepts/DeliveredOrder.l"

    ```prolog
    --8<-- "layers/sales/concepts/DeliveredOrder.l"
    ```

=== "rules/ActiveCustomer.l"

    ```prolog
    --8<-- "layers/sales/rules/ActiveCustomer.l"
    ```

=== "rules/Revenue.l"

    ```prolog
    --8<-- "layers/sales/rules/Revenue.l"
    ```

=== "rules/RevenueByCountry.l"

    ```prolog
    --8<-- "layers/sales/rules/RevenueByCountry.l"
    ```

=== "tables/Orders.l"

    ```prolog
    --8<-- "layers/sales/tables/Orders.l"
    ```

## support

Support tickets: the open ones, and each agent's workload — a rule built on
another rule.

=== "rules/OpenTickets.l"

    ```prolog
    --8<-- "layers/support/rules/OpenTickets.l"
    ```

=== "rules/Workload.l"

    ```prolog
    --8<-- "layers/support/rules/Workload.l"
    ```

=== "tables/Tickets.l"

    ```prolog
    --8<-- "layers/support/tables/Tickets.l"
    ```
