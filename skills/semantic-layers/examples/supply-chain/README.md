# supply-chain

An example semantic layer, runnable without a database: synalog loads the CSV
files of `data/` into DuckDB.

```shell
uvx synalog rules/SupplierExposure.l run SupplierExposure \
  --load suppliers=data/suppliers.csv --load parts=data/parts.csv \
  --load bill_of_materials=data/bill_of_materials.csv
```
