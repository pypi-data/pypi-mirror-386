# CHANGELOG

<!-- version list -->

## v1.6.2 (2025-10-22)

### Bug Fixes

- Add workers-runtime-sdk as a dependency, update type test
  ([#41](https://github.com/cloudflare/workers-py/pull/41),
  [`f381505`](https://github.com/cloudflare/workers-py/commit/f381505e4c9b40ddb602928d964aa3fe38936e5c))


## v1.6.1 (2025-10-15)

### Bug Fixes

- Be more lenient with wrangler version parsing
  ([#45](https://github.com/cloudflare/workers-py/pull/45),
  [`8315a03`](https://github.com/cloudflare/workers-py/commit/8315a03de83bff3836c84be28726bea7f6124dd8))


## v1.6.0 (2025-10-15)

### Features

- Pywrangler init proxies to C3 directly with Python preselected
  ([`8ec7724`](https://github.com/cloudflare/workers-py/commit/8ec7724c4768314cf5a6a4434cb0c33b95d3611f))


## v1.5.1 (2025-10-13)

### Bug Fixes

- Fix default value for --outdir in help message
  ([#39](https://github.com/cloudflare/workers-py/pull/39),
  [`7aded7a`](https://github.com/cloudflare/workers-py/commit/7aded7a43580fc50b6408baee0184fa814481c9b))


## v1.5.0 (2025-10-10)

### Features

- Implement pywrangler types to generate Python type stubs
  ([#38](https://github.com/cloudflare/workers-py/pull/38),
  [`39b67bd`](https://github.com/cloudflare/workers-py/commit/39b67bd24ed3916de12aa9025703ed18fe4a73cd))


## v1.4.0 (2025-10-10)

### Features

- Adds wrangler version check
  ([`ed41bcc`](https://github.com/cloudflare/workers-py/commit/ed41bccf24d5130b2c628edc7c3ece48edf14253))


## v1.3.0 (2025-10-08)

### Features

- Implements python version detection based on wrangler config
  ([`dec6e10`](https://github.com/cloudflare/workers-py/commit/dec6e10a8ff685feffbbd329d26a52212d83e0e3))


## v1.2.1 (2025-10-07)

### Bug Fixes

- Add version check for uv ([#36](https://github.com/cloudflare/workers-py/pull/36),
  [`f9b16ab`](https://github.com/cloudflare/workers-py/commit/f9b16ab2cd08b0c5afe7e10b053f982d3d536633))

### Documentation

- Update README.md to use `uv tool`
  ([`14770ae`](https://github.com/cloudflare/workers-py/commit/14770aea1c2bc2dd052c7f162f8fc4192815c550))


## v1.2.0 (2025-09-26)

### Features

- Use uv instead of pyodide-build to manage pyodide install and venv
  ([#30](https://github.com/cloudflare/workers-py/pull/30),
  [`1629919`](https://github.com/cloudflare/workers-py/commit/16299198db73f1e3efb99eb6ef928fc46978acd9))


## v1.1.8 (2025-09-25)

### Bug Fixes

- Sync: Use a token that we write only after sync succeeds
  ([#29](https://github.com/cloudflare/workers-py/pull/29),
  [`64bc90a`](https://github.com/cloudflare/workers-py/commit/64bc90ac3832e094e096130f87992d0899e6b8fc))


## v1.1.7 (2025-08-28)

### Bug Fixes

- Check for venv python version mismatch
  ([`c7871f0`](https://github.com/cloudflare/workers-py/commit/c7871f07dcc2ad54f0cd9e0243ff5107cf43d9c9))


## v1.1.6 (2025-08-27)

### Bug Fixes

- Sync: if nothing to do, only warn if user requested directly
  ([#26](https://github.com/cloudflare/workers-py/pull/26),
  [`e142800`](https://github.com/cloudflare/workers-py/commit/e142800306cf4a021c10c629814265ed63d9cd90))


## v1.1.5 (2025-08-26)

### Bug Fixes

- Lock pyodide-build to fix running on Py 3.12
  ([`2f301f4`](https://github.com/cloudflare/workers-py/commit/2f301f483be59ead2a799a0e8cba6291e428080b))


## v1.1.4 (2025-08-06)

### Bug Fixes

- Allow overriding the python version ([#22](https://github.com/cloudflare/workers-py/pull/22),
  [`e58114f`](https://github.com/cloudflare/workers-py/commit/e58114fd20f44b0358747a2b40652566ccc8486d))

- Pass --yes to npx so it won't time out after 10 seconds if wrangler not installed
  ([#20](https://github.com/cloudflare/workers-py/pull/20),
  [`c80d5e5`](https://github.com/cloudflare/workers-py/commit/c80d5e58ec896fb3c494b7726d2f199defd7734b))


## v1.1.3 (2025-07-31)

### Bug Fixes

- Fixes --version returning unknown version
  ([`fa71797`](https://github.com/cloudflare/workers-py/commit/fa71797e23bb2b8263bfc8fc34c2a21c0677c8c3))


## v1.1.2 (2025-07-28)

### Bug Fixes

- Mark python_modules as a virtual env dir
  ([`e889742`](https://github.com/cloudflare/workers-py/commit/e88974297ace9511e0ca1abc6bf617ecb52cfb05))


## v1.1.1 (2025-07-23)

### Bug Fixes

- Output relative path in package installation message
  ([`4eecf36`](https://github.com/cloudflare/workers-py/commit/4eecf3604fe5edb16b3f0cd775cc8773cb1b608e))


## v1.1.0 (2025-07-23)

### Features

- Renames vendor dir to `python_modules`
  ([`01e5ab9`](https://github.com/cloudflare/workers-py/commit/01e5ab9f0280bf267c803d1e451a473fc5171864))


## v1.0.4 (2025-06-20)

### Bug Fixes

- Use jsonc-parser for jsonc parsing to support multi-line comments
  ([`229062d`](https://github.com/cloudflare/workers-py/commit/229062d717091b46010791f71df82e43a6323a5b))


## v1.0.3 (2025-06-20)

### Bug Fixes

- Only look for pyproject.toml on `sync` command
  ([`fd2eb1d`](https://github.com/cloudflare/workers-py/commit/fd2eb1db64c81f04334fc09634326e4287972b6a))


## v1.0.2 (2025-06-18)

### Bug Fixes

- Expose release job outputs to deploy job
  ([`116b8be`](https://github.com/cloudflare/workers-py/commit/116b8be6531dc91f2a2e869af9e1c667cc17862a))


## v1.0.1 (2025-06-17)

### Bug Fixes

- Skip Upload Distribution Artifacts step on tagged commit
  ([`06fafb0`](https://github.com/cloudflare/workers-py/commit/06fafb0e331dfa5744529889290d0afda01c3716))


## v1.0.0 (2025-06-17)

- Initial Release

## v1.0.0 (2025-06-16)

- Initial Release
