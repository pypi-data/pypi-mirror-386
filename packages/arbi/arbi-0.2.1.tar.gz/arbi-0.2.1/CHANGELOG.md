# Changelog

## 0.2.1 (2025-10-18)

Full Changelog: [v0.2.0...v0.2.1](https://github.com/arbitrationcity/arbi-python/compare/v0.2.0...v0.2.1)

### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([a499053](https://github.com/arbitrationcity/arbi-python/commit/a4990530e19afda079fec1702da7b10e5ee8a145))

## 0.2.0 (2025-10-13)

Full Changelog: [v0.1.1...v0.2.0](https://github.com/arbitrationcity/arbi-python/compare/v0.1.1...v0.2.0)

### Features

* DRAFT add email verification requirement for local user registration ([ba914da](https://github.com/arbitrationcity/arbi-python/commit/ba914dae291c8b58df7bfd3be5d01e27cdf456b7))
* implement public workspaces with deployment key encryption ([9b25ecd](https://github.com/arbitrationcity/arbi-python/commit/9b25ecdced445221b56e1bd45caa44af7039d76d))
* improve future compat with pydantic v3 ([be64906](https://github.com/arbitrationcity/arbi-python/commit/be64906d140b119239ab09b23564ada62ed4e7f4))
* Llamaindex agent featureflag ([0464f7a](https://github.com/arbitrationcity/arbi-python/commit/0464f7af287125546d87896d6316d3b34aa1c9a1))
* **types:** replace List[str] with SequenceNotStr in params ([bcc155b](https://github.com/arbitrationcity/arbi-python/commit/bcc155b44acb974cc0d72cf8ce20918f59f5c5e5))


### Bug Fixes

* avoid newer type syntax ([2008b65](https://github.com/arbitrationcity/arbi-python/commit/2008b653d1baba6824f79da6183fdbdf2543f605))
* **compat:** compat with `pydantic&lt;2.8.0` when using additional fields ([0bc83c2](https://github.com/arbitrationcity/arbi-python/commit/0bc83c26322edf26307d9d1bfd4f26d0e4d131b3))


### Chores

* do not install brew dependencies in ./scripts/bootstrap by default ([6dfd710](https://github.com/arbitrationcity/arbi-python/commit/6dfd710821d6a0f81b42c65c40fdc91631769681))
* **internal:** add Sequence related utils ([07de38e](https://github.com/arbitrationcity/arbi-python/commit/07de38eb8a532b5e82dfbbcf840afbdd55c38ac6))
* **internal:** detect missing future annotations with ruff ([9740de5](https://github.com/arbitrationcity/arbi-python/commit/9740de55f5783fc2a8e9d0823ed09ec677b9a2c0))
* **internal:** move mypy configurations to `pyproject.toml` file ([3907f70](https://github.com/arbitrationcity/arbi-python/commit/3907f7002aef0fa434c3cf024a36d1ec58b3d79d))
* **internal:** update pydantic dependency ([89b016f](https://github.com/arbitrationcity/arbi-python/commit/89b016f708b3dd946973de2d9047688faf199f9d))
* **internal:** update pyright exclude list ([7c356cf](https://github.com/arbitrationcity/arbi-python/commit/7c356cf1faea5ec7c787b961a07a4630f60b2805))
* **tests:** simplify `get_platform` test ([b011a08](https://github.com/arbitrationcity/arbi-python/commit/b011a08fb145b126dbadb6847a1f43d8a8ee062b))
* **types:** change optional parameter type from NotGiven to Omit ([4d1fbc7](https://github.com/arbitrationcity/arbi-python/commit/4d1fbc7bfeb2ef9a88f3458ae9ec7f5a0f932a8f))

## 0.1.1 (2025-08-26)

Full Changelog: [v0.1.0...v0.1.1](https://github.com/arbitrationcity/arbi-python/compare/v0.1.0...v0.1.1)

### Chores

* **internal:** change ci workflow machines ([54e1ad5](https://github.com/arbitrationcity/arbi-python/commit/54e1ad548a490aced615402fef6069f8fb062346))

## 0.1.0 (2025-08-24)

Full Changelog: [v0.1.0-alpha.1...v0.1.0](https://github.com/arbitrationcity/arbi-python/compare/v0.1.0-alpha.1...v0.1.0)

### Features

* **api:** manual updates ([0eef976](https://github.com/arbitrationcity/arbi-python/commit/0eef9761f948767035a957db7a480a5f1c9fa67b))
* **api:** manual updates ([cf4ce4f](https://github.com/arbitrationcity/arbi-python/commit/cf4ce4fc8a9ac37366d87a3fc216d98491a97a80))
* **api:** manual updates ([88379e2](https://github.com/arbitrationcity/arbi-python/commit/88379e2df1d787be045b522dd71c8fc72062c5bf))
* **api:** manual updates ([9fdc003](https://github.com/arbitrationcity/arbi-python/commit/9fdc003db20c59b3d42b3518beb6abb87efba4e3))
* **api:** manual updates ([45cdc9a](https://github.com/arbitrationcity/arbi-python/commit/45cdc9a0d716af2bbbcffd742044fb7871191131))
* **api:** manual updates ([fdcd3b8](https://github.com/arbitrationcity/arbi-python/commit/fdcd3b8a24e3e853e5c1992b7ea9882d53be29c3))
* **api:** manual updates - test ([ceb0a29](https://github.com/arbitrationcity/arbi-python/commit/ceb0a29da5fbffc47c3adfafd52d2fb718661e05))
* **api:** manual updates -test 2 ([718dc68](https://github.com/arbitrationcity/arbi-python/commit/718dc68b20b2cd964117b5de9676747628444181))
* clean up environment call outs ([88cdd65](https://github.com/arbitrationcity/arbi-python/commit/88cdd6551e968fc66a5f0702799973cc2e133058))
* **client:** support file upload requests ([0e302b2](https://github.com/arbitrationcity/arbi-python/commit/0e302b2c990d2a5a29e9cad98f75017e190a244b))
* enabled stainless CI ([71702c2](https://github.com/arbitrationcity/arbi-python/commit/71702c25ecead109974da51e104b355805c9e827))


### Bug Fixes

* **parsing:** ignore empty metadata ([5c8f7a1](https://github.com/arbitrationcity/arbi-python/commit/5c8f7a1448a88497243dde391e745124d9708dac))
* **parsing:** parse extra field types ([13d7e6b](https://github.com/arbitrationcity/arbi-python/commit/13d7e6b0ccd9ab20db2f505dfb3a3a3d5a2bd950))


### Chores

* **internal:** codegen related update ([32175d3](https://github.com/arbitrationcity/arbi-python/commit/32175d3433c0f30de68c728793888ce2ea50c805))
* **internal:** fix ruff target version ([b14949a](https://github.com/arbitrationcity/arbi-python/commit/b14949ac8dc813d4256a7768a0e0f7b2c6edad5f))
* **internal:** update comment in script ([c5ad447](https://github.com/arbitrationcity/arbi-python/commit/c5ad447a54950674fb5bfdea7dc7a23960086311))
* **project:** add settings file for vscode ([dc9cfc0](https://github.com/arbitrationcity/arbi-python/commit/dc9cfc0a3a1d9af1050569d86b7cedf5466492bc))
* update @stainless-api/prism-cli to v5.15.0 ([481255c](https://github.com/arbitrationcity/arbi-python/commit/481255c1dd4bd151ddbab289e079e82f7468ab30))
* update github action ([3b13bfd](https://github.com/arbitrationcity/arbi-python/commit/3b13bfd3d337f25cc1014dbd6774cc9005ab3848))
* update SDK settings ([3844736](https://github.com/arbitrationcity/arbi-python/commit/38447362988da6e7b9277b804962c3e47c33a63f))
* update SDK settings ([a010c89](https://github.com/arbitrationcity/arbi-python/commit/a010c891b2a453331c120851e77ae06f7f0b97c1))
* update SDK settings ([c1365e9](https://github.com/arbitrationcity/arbi-python/commit/c1365e9d75cb0454096dedd3d954e04715e579ac))
* update SDK settings ([b7631d1](https://github.com/arbitrationcity/arbi-python/commit/b7631d192230f69c6925ab4a1f658da3054da887))

## 0.1.0-alpha.1 (2025-07-14)

Full Changelog: [v0.0.1-alpha.0...v0.1.0-alpha.1](https://github.com/arbitrationcity/arbi-python/compare/v0.0.1-alpha.0...v0.1.0-alpha.1)

### Features

* **api:** manual updates ([0b7203d](https://github.com/arbitrationcity/arbi-python/commit/0b7203d7a467ada2c2ab1f25413aadc9ca665749))
* **api:** manual updates ([1a0beea](https://github.com/arbitrationcity/arbi-python/commit/1a0beea23f8cabfd4f6713ce50c830bb98d17386))
* **api:** manual updates ([7a29f9e](https://github.com/arbitrationcity/arbi-python/commit/7a29f9ecbd53e92da5e72eb80c80c92b1a72847d))
* **api:** manual updates ([6e9af4d](https://github.com/arbitrationcity/arbi-python/commit/6e9af4db5e0fb939e28f8244800a96adaac02812))
* **api:** manual updates ([71a7f84](https://github.com/arbitrationcity/arbi-python/commit/71a7f8429aad6432e71a78be76851a419ed0f10d))
* **api:** manual updates ([f4a3df0](https://github.com/arbitrationcity/arbi-python/commit/f4a3df03b5cd986f6a21774fe382dfdc23b4b799))
* **api:** update via SDK Studio ([a37fa7c](https://github.com/arbitrationcity/arbi-python/commit/a37fa7c0fc6dbee8de49fa8919eb97bfabc55cc9))
* **api:** update via SDK Studio ([4bbebd5](https://github.com/arbitrationcity/arbi-python/commit/4bbebd57ab8ffc88cfe9fd71c47f2d2f4b912e8d))
* **api:** update via SDK Studio ([88f4dbb](https://github.com/arbitrationcity/arbi-python/commit/88f4dbbc1b0e1c5cc08bc90f34fa9758b3983186))
* **api:** update via SDK Studio ([4a8b50c](https://github.com/arbitrationcity/arbi-python/commit/4a8b50c9cde9cdb33d0f9388da669be2cf4fcd9c))
* **api:** update via SDK Studio ([389c3f2](https://github.com/arbitrationcity/arbi-python/commit/389c3f2ad334b951bfb884ded6beb28b90006ed2))
* **api:** update via SDK Studio ([407112f](https://github.com/arbitrationcity/arbi-python/commit/407112f491febbbfc5489e4d12a4633dd8626aed))
* **client:** add support for aiohttp ([3f66d0a](https://github.com/arbitrationcity/arbi-python/commit/3f66d0a4a51d66147b1f4a86ad0398980b35468e))
* Tas 130/feature/create initial integration tests ([496851f](https://github.com/arbitrationcity/arbi-python/commit/496851f6780ab8fe1be4f8d73697fe005c2eabac))


### Bug Fixes

* **ci:** correct conditional ([47fe3d0](https://github.com/arbitrationcity/arbi-python/commit/47fe3d0213f76e09727dd4a7b0b6638e17722671))
* **ci:** release-doctor — report correct token name ([2c759bc](https://github.com/arbitrationcity/arbi-python/commit/2c759bc1f4d8ffe6b23dbdd2b8edb98f038182ea))
* **client:** don't send Content-Type header on GET requests ([e397cca](https://github.com/arbitrationcity/arbi-python/commit/e397cca3ff3d5e9463eecb598b538eff3bed6635))
* **multipart:** avoid appending [] to names ([b06cef9](https://github.com/arbitrationcity/arbi-python/commit/b06cef972cb20f898c5c7ca7c7ae32928ea1d862))
* **parsing:** correctly handle nested discriminated unions ([abf152f](https://github.com/arbitrationcity/arbi-python/commit/abf152f8b234a2533102b170c107e8877a9c23a4))
* **tests:** fix: tests which call HTTP endpoints directly with the example parameters ([a56bac3](https://github.com/arbitrationcity/arbi-python/commit/a56bac3b5ba6fc92ef93c702c8a7716e97d93562))


### Chores

* change publish docs url ([6ce0e40](https://github.com/arbitrationcity/arbi-python/commit/6ce0e40b3dda97479a88f8294aed0f3de7501b2f))
* **ci:** change upload type ([8af91c9](https://github.com/arbitrationcity/arbi-python/commit/8af91c9a97e92dfa389b926e01b76458a3b6b400))
* **ci:** only run for pushes and fork pull requests ([9cb4440](https://github.com/arbitrationcity/arbi-python/commit/9cb44404fc948c72cbc3ab0c2cf80bbbcf27de89))
* **internal:** bump pinned h11 dep ([bad7ed0](https://github.com/arbitrationcity/arbi-python/commit/bad7ed07d8ab4168f6355ff38f4eaf9abc42596d))
* **internal:** codegen related update ([dc45558](https://github.com/arbitrationcity/arbi-python/commit/dc45558c0f0ada5918245209bbfcadc9a5f9675e))
* **internal:** codegen related update ([830b7f4](https://github.com/arbitrationcity/arbi-python/commit/830b7f4452f471d97e7eadcb3e6acd93995f8c17))
* **internal:** codegen related update ([262c91c](https://github.com/arbitrationcity/arbi-python/commit/262c91cec722940e8afc101acd94183784c67af5))
* **package:** mark python 3.13 as supported ([73e7e87](https://github.com/arbitrationcity/arbi-python/commit/73e7e877d86db4044a01ef4f73466bb1ca47b50a))
* **readme:** fix version rendering on pypi ([8e119de](https://github.com/arbitrationcity/arbi-python/commit/8e119ded795b17bbe639212577f08f59938d3201))
* **tests:** skip some failing tests on the latest python versions ([dc6e2d4](https://github.com/arbitrationcity/arbi-python/commit/dc6e2d44cbf2cd466671bc049f5170285c3ddde1))
* update SDK settings ([7fda948](https://github.com/arbitrationcity/arbi-python/commit/7fda9487374b30035398d22926ea43ca28d73fd6))
* update SDK settings ([dbabaf0](https://github.com/arbitrationcity/arbi-python/commit/dbabaf033d8cf222befa9c3593a1036759fce6ca))


### Documentation

* **client:** fix httpx.Timeout documentation reference ([722c201](https://github.com/arbitrationcity/arbi-python/commit/722c201e208a947433f1cd024392c269e2bc8f08))
