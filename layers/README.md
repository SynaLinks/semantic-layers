# Example layers

Two semantic layers to try the format with — each folder is one layer,
installable on its own:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --list
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
```

Each has a `synalog.toml` naming and describing it, without a `[connection]`:
they are written for anyone's data, so whoever installs them connects them to
their own database.
