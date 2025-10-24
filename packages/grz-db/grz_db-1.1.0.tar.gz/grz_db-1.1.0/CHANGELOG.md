# Changelog

## [1.1.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v1.0.1...grz-db-v1.1.0) (2025-10-23)


### Features

* **grzctl,grz-cli:** support meanReadLength ([#437](https://github.com/BfArM-MVH/grz-tools/issues/437)) ([b86b843](https://github.com/BfArM-MVH/grz-tools/commit/b86b84313758d6fa16b1ee74af4834ba3e2ec914))


### Bug Fixes

* **grz-db:** bump grz-pydantic-models version ([b86b843](https://github.com/BfArM-MVH/grz-tools/commit/b86b84313758d6fa16b1ee74af4834ba3e2ec914))

## [1.0.1](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v1.0.0...grz-db-v1.0.1) (2025-10-13)


### Bug Fixes

* **grz-db,grzctl:** properly repopulate donors ([#413](https://github.com/BfArM-MVH/grz-tools/issues/413)) ([cb7b1bd](https://github.com/BfArM-MVH/grz-tools/commit/cb7b1bdebcfaec2e5581eb8a2e93ab57397b242e))

## [1.0.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.6.0...grz-db-v1.0.0) (2025-10-07)


### Features

* **grz-db:** bump required dependencies ([#401](https://github.com/BfArM-MVH/grz-tools/issues/401)) ([f62a6e1](https://github.com/BfArM-MVH/grz-tools/commit/f62a6e1982f7cd43210d9abf1856f7a46607092c))
* **grz-pydantic-models:** allow MV consent revocation on non-initial ([1179499](https://github.com/BfArM-MVH/grz-tools/commit/117949907151b612251ce5680d709d335f0e9427))
* **grzctl:** add quarterly report export ([#376](https://github.com/BfArM-MVH/grz-tools/issues/376)) ([1179499](https://github.com/BfArM-MVH/grz-tools/commit/117949907151b612251ce5680d709d335f0e9427))

## [0.6.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.5.0...grz-db-v0.6.0) (2025-08-27)


### Features

* **grz-db,grzctl:** sort submission db list by latest state with fallbacks ([#370](https://github.com/BfArM-MVH/grz-tools/issues/370)) ([fdc521b](https://github.com/BfArM-MVH/grz-tools/commit/fdc521bcc28af3c036aea7fa89837fa078eec25f))

## [0.5.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.4.0...grz-db-v0.5.0) (2025-08-19)


### Features

* **grz-db:** add limit parameter to database list_submissions ([e2eebda](https://github.com/BfArM-MVH/grz-tools/commit/e2eebdaaaa524cfeacb97f9717ba85bd74b2c8a6))
* **grzctl:** add configurable display limit for db list command ([#344](https://github.com/BfArM-MVH/grz-tools/issues/344)) ([e2eebda](https://github.com/BfArM-MVH/grz-tools/commit/e2eebdaaaa524cfeacb97f9717ba85bd74b2c8a6))
* **grzctl:** confirm before updating submission from error state ([#357](https://github.com/BfArM-MVH/grz-tools/issues/357)) ([25e6cb6](https://github.com/BfArM-MVH/grz-tools/commit/25e6cb62130cf926a9c77d5232bc39d3ecb91c66))


### Bug Fixes

* **grz-db:** allow empty author private key passphrases ([25e6cb6](https://github.com/BfArM-MVH/grz-tools/commit/25e6cb62130cf926a9c77d5232bc39d3ecb91c66))

## [0.4.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.3.0...grz-db-v0.4.0) (2025-08-05)


### Features

* **grzctl:** add reporting for processed submissions ([#320](https://github.com/BfArM-MVH/grz-tools/issues/320)) ([d44aead](https://github.com/BfArM-MVH/grz-tools/commit/d44aeade809e39693360b577e5482873ae975709))


### Bug Fixes

* **grz-db:** add StringConstraints to SubmissionBase.id ([#323](https://github.com/BfArM-MVH/grz-tools/issues/323)) ([0ac80fb](https://github.com/BfArM-MVH/grz-tools/commit/0ac80fbb4e68957bb9b59a395c90bc2bdf67e02d))

## [0.3.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.2.1...grz-db-v0.3.0) (2025-07-31)


### Features

* **grzctl,grz-db,grz-common,grz-pydantic-models:** add columns, migration, and populate ([#306](https://github.com/BfArM-MVH/grz-tools/issues/306)) ([c158fa0](https://github.com/BfArM-MVH/grz-tools/commit/c158fa0cfe47ddacd66947dd57b814f43cfaefdc))

## [0.2.1](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.2.0...grz-db-v0.2.1) (2025-07-02)


### Bug Fixes

* **grz-db,grzctl:** address previously unchecked mypy type checks ([#247](https://github.com/BfArM-MVH/grz-tools/issues/247)) ([e51a65b](https://github.com/BfArM-MVH/grz-tools/commit/e51a65b090c891f44c6c4cc7199138d4cb15c07a))

## [0.2.0](https://github.com/BfArM-MVH/grz-tools/compare/grz-db-v0.1.0...grz-db-v0.2.0) (2025-06-30)


### Features

* **grzctl,grz-db:** Add support for change requests ([#151](https://github.com/BfArM-MVH/grz-tools/issues/151)) ([2f28d69](https://github.com/BfArM-MVH/grz-tools/commit/2f28d691b72da2d904391680ff72b1f9a3a22254))


### Bug Fixes

* **grz-db:** don't print the duplicate tanG ([#229](https://github.com/BfArM-MVH/grz-tools/issues/229)) ([718a2be](https://github.com/BfArM-MVH/grz-tools/commit/718a2be52d959be44449f6b46143be62728c2631))
* **grz-db:** Ensure author's key is ed25519 ([#204](https://github.com/BfArM-MVH/grz-tools/issues/204)) ([0f7eba2](https://github.com/BfArM-MVH/grz-tools/commit/0f7eba2652c67f3c4ddb507f7d4e197dc0c086ec))
* **grzctl,grz-db:** Add `db submission modify` to allow setting tanG/pseudonym ([#198](https://github.com/BfArM-MVH/grz-tools/issues/198)) ([b6275c3](https://github.com/BfArM-MVH/grz-tools/commit/b6275c38b134e6d334dc158c9c98631e62750b68))
* **grzctl:** improve error message on incorrect passphrase for private key ([#206](https://github.com/BfArM-MVH/grz-tools/issues/206)) ([8b73036](https://github.com/BfArM-MVH/grz-tools/commit/8b7303643b96b87bf9b095e135633fc3db3a7c7e))

## 0.1.0 (2025-06-11)


### Features

* migrate to monorepo configuration ([36c7360](https://github.com/BfArM-MVH/grz-tools/commit/36c736044ce09473cc664b4471117465c5cab9a3))
