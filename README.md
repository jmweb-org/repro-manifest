# repro-manifest

Wrap a run to capture a portable manifest of its environment, code, config and
seeds, then diff two manifests to explain why two runs differed.

```console
$ repro-manifest run -o run.json -- python train.py
$ repro-manifest diff good.json run.json
```

## License

MIT.
