# blog

Static source files for the legacy Hexo blog.

## Credentials and Qiniu uploads

Do not store credentials anywhere in this repository, including ignored files,
examples, posts, generated assets, or Git history. The previously committed Qiniu
keys must be revoked or rotated in Qiniu before uploading again. Removing them
from the current configuration does not remove them from old commits or copies.

The checked-in `_config.yml` has empty credentials and `qiniu.sync: false`.
Normal rendering keeps the existing Qiniu image URLs but does not upload assets.
This deliberately corrects the old misspelling `sunc`, which did not disable sync.

If this legacy blog still needs uploads, use the plugin's native `secret_file`
support and keep both the private configuration and credentials **outside all
repositories**. Never reuse the exposed keys.

1. Create a private directory such as `$HOME/.config/legacy-blog` with mode `700`.
2. Copy the current `_config.yml` into that directory as `config.yml` with mode
   `600`. In that external copy, set `qiniu.sync: true` and add
   `qiniu.secret_file` with the absolute path to `qiniu.json` in the same private
   directory. Leave the inline `access_key` and `secret_key` fields empty.
3. Put the replacement credentials in the external `qiniu.json`, with the JSON
   properties `access_key` and `secret_key`, and set its mode to `600`. Retrieve
   values using a trusted secret manager, not from Git history, shell history,
   a committed `.env`, or this README.
4. From the repository root, explicitly upload using the external configuration:

   ```sh
   ./node_modules/.bin/hexo --config "$HOME/.config/legacy-blog/config.yml" qiniu sync
   ```

The plugin reads the JSON file before initializing the Qiniu client. Plain
`${VARIABLE}` strings in this old Hexo YAML configuration are not environment
variable interpolation. Do not use `--debug`, `hexo config`, or print the loaded
configuration while credentials are present: the old plugin can log its config.
Keep the external copy in sync with non-secret settings when `_config.yml` changes.

## Checks before a commit

Run the focused, redacted check:

```sh
python3 tools/check-secrets.py
```

It checks tracked and non-ignored files for populated sensitive assignments,
private-key blocks, and common credential token formats. It prints only file
names, line numbers, and rule names, never matched values. This is a heuristic,
not proof that a repository or its history contains no secrets. Review diffs and
use a maintained secret scanner such as Gitleaks for broader audits.

For a Git pre-commit integration, invoke `python3 tools/check-secrets.py --staged`
from your existing hook; this checks the index, rather than uncommitted working
files. Do not overwrite an existing hook.
