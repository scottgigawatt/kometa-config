# Set up Plex test libraries 🎟️

Create tiny, private movie and TV libraries once, then reuse them for [preview runs](testing.md). Plex may run natively on Synology while Kometa runs in Docker on your workstation.

## Prepare media on Synology

The example layout uses a `plex` share at `/volume1/plex`. Keep test media in a separate `test` folder, never inside a production movie or TV directory.

1. In File Station, create `test` inside the `plex` share.
2. In an SSH session on the NAS, clone the [Plex test libraries](https://github.com/chazlarson/plex-test-libraries):

   ```sh
   cd /volume1/plex/test
   git clone https://github.com/chazlarson/plex-test-libraries.git
   ```

3. Confirm the `PlexMediaServer` system internal user has inherited read access to the test folder, subfolders, and files.

If Git is unavailable on the NAS, mount the share at `/Volumes/plex` on your Mac and clone there instead. Use only one of the two clone routes:

```sh
mkdir -p /Volumes/plex/test
cd /Volumes/plex/test
git clone https://github.com/chazlarson/plex-test-libraries.git
```

The upstream repository contains tiny media fixtures. For additional coverage, use small synthetic clips with Plex-compatible movie or episode names inside the test directories only.

## Add the libraries in Plex

In Plex Web, open **Settings → Manage → Libraries → Add Library**.

| Type | Exact library name | NAS folder |
| --- | --- | --- |
| Movies | `test_movie_lib` | `/volume1/plex/test/plex-test-libraries/test_movie_lib` |
| TV Shows | `test_tv_lib` | `/volume1/plex/test/plex-test-libraries/test_tv_lib` |

Use the Plex Movie and Plex Series agents. Keep the libraries private and unpinned, then wait for scanning and matching to finish.

> [!CAUTION]
> Point each library at its specific fixture directory—not the whole share or the parent `test` folder. Never substitute production library names in the test configuration.

Only Plex needs filesystem access to these media files. The workstation's Kometa container communicates with Plex through its API; the media share needs to be mounted on the workstation only when adding or inspecting fixture files.

## Configure private access

Return to the Kometa configuration checkout on your workstation. Create the environment once without replacing existing values:

```sh
mkdir -p .secrets
cp -n example.test.env .secrets/test.env
```

Edit `.secrets/test.env` with your Plex server URL, a Plex token authorized for the fixture libraries, and a TMDb API key. Overlay previews also need an MDBList API key. Use a server address reachable from Docker; `localhost` inside the container does not mean the NAS. Include a port only when your endpoint requires one.

Every environment value is private, including the server URL. Do not paste it into source, issues, screenshots, or PRs. Test isolation comes from the guarded configuration; a Plex token may still have wider permissions, so protect it accordingly.

## Verify setup

From the workstation checkout, with Docker running and `.venv` active:

```sh
make check
make test-library
```

Follow the [testing guide](testing.md#review-the-result) to inspect the smoke collections and artwork. Keep `.kometa-test/` caches and poster backups for later runs.
