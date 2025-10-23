# Self-Hosted Virtual Stack

**SVS is an open-source python library for managing self-hosted services on a linux server.**

## Goals

The goal of this project is to provide a simple and easy-to-use library for managing self-hosted services on a linux server. It is designed to be used by developers who want to automate the management of their self-hosted services, such as web servers, databases, and other applications.

It should be both begginer-friendly and yet allow advanced users to customize the behavior of the library to suit their needs.

Under the hood, all services will be managed using Docker containers, which allows for easy deployment and management of services. Given the complexity of Docker, the library will provide templates for common services and hide as much of the complexity as possible while still allowing advanced users to access the underlying Docker functionality if they wish to do so.

## Technology overview

Every service will run a Docker container and all of users' services will be on the same Docker network, allowing them to communicate with each other easily without

1. exposing them to other users on the same server
1. having to use compose stacks and custom networks to allow cross-service communication.

Direct SSH access to the containers will be provided but handled by additional authentication as to avoid having to create system accounts for each user.

## Features

Currently, the library is in early development and has the following features:

- [x] User management
- [x] Docker network management
- [ ] Service management
- [x] Service templates
- [ ] CI/CD integration
- [ ] DB/System sync issues + recovery
- [ ] Remote SSH access

## Running locally

Given this repository accesses system files, creates docker containers and manages services and is designed strictly for linux servers, it is recommended to run in a virtual environment.

The easiest way to achieve a reproducible environment is to use the included devcontainer configuration. Devcontainers allow you to run a containerized development environment with all dependencies installed. [See the devcontainer documentation](https://code.visualstudio.com/docs/devcontainers/containers).

The local devcontainer config creates the following compose stack:

1. A `debian` container for the development environment.
1. A `postgres` database container for storing service data.
1. A `caddy` container to act as a HTTP proxy

This guide assumes you have chosen to use the devcontainer setup.

### Starting the devcontainer

To start the devcontainer, open the repository in Visual Studio Code and select "Reopen in Container" from the command palette. This will build the container and start it.

After attaching to the devcontainer, the dependencies will be automatically installed. After that's done, you can launch a new terminal which will have the virtual environment activated automatically.

### Linting + Formatting

The devcontainer includes pre-configured linting and formatting tools for Visual Studio Code and all files should be formatted on save. If you use a different editor, you can run the pre-commit hooks manually by running `pre-commit run --all-files` in the terminal to apply the formatting and linting rules.

### Running the tests

To run the tests, you can use the `pytest` command in the terminal. This will run all tests in the `tests` directory. You can also run individual test files or functions by specifying their paths.

Tests are split into unit and integration tests. They can be run separately by using the `-m` flag with pytest:

```bash
pytest -m unit
pytest -m integration
```

### Running the docs

Python docstrings are use throughout the codebase to generate documentation. To generate the documentation, you can use the `mkdocs` command in the terminal. This will build the documentation and serve it locally.
To run the documentation server, you can use the following command:

```bash
mkdocs serve
```
