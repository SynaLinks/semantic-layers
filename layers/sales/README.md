# sales

An example semantic layer about orders and customers: what a customer is,
which orders count as sales, revenue, and the customers who bought.

Install it, then connect it to a database with `orders` and `customers`
tables:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
uvx semantic-layers connect sales psql host=... database=... user=... password=...
```
