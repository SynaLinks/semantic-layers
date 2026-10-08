# supply-chain

An example semantic layer, runnable without a database: `--load` reads the
CSV files of `data/` into memory.

```shell
uvx semantic-layers run SupplierExposure \
  --load suppliers=data/suppliers.csv --load parts=data/parts.csv \
  --load bill_of_materials=data/bill_of_materials.csv
```
