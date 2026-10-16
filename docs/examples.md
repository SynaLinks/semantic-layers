# Examples

This repository's `layers/` folder holds two example layers, installable from
it:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --list
```

## sales

Orders and customers: what a customer is, which orders count as sales,
revenue, and the customers who bought.

=== "concepts/customer.l"

    ```synalog
    --8<-- "layers/sales/concepts/customer.l"
    ```

=== "concepts/delivered_order.l"

    ```synalog
    --8<-- "layers/sales/concepts/delivered_order.l"
    ```

=== "rules/active_customer.l"

    ```synalog
    --8<-- "layers/sales/rules/active_customer.l"
    ```

=== "rules/revenue.l"

    ```synalog
    --8<-- "layers/sales/rules/revenue.l"
    ```

=== "rules/revenue_by_country.l"

    ```synalog
    --8<-- "layers/sales/rules/revenue_by_country.l"
    ```

=== "tables/orders.l"

    ```synalog
    --8<-- "layers/sales/tables/orders.l"
    ```

## support

Support tickets: the open ones, and each agent's workload — a rule built on
another rule.

=== "rules/open_tickets.l"

    ```synalog
    --8<-- "layers/support/rules/open_tickets.l"
    ```

=== "rules/workload.l"

    ```synalog
    --8<-- "layers/support/rules/workload.l"
    ```

=== "tables/tickets.l"

    ```synalog
    --8<-- "layers/support/tables/tickets.l"
    ```
