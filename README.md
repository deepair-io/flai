![](./docs/assets/images/cover.png)

# FLAI: Reinforcement Learning Virtual Platform for Travel


![python](https://img.shields.io/badge/python-3.8-blue.svg)
[![version](https://img.shields.io/badge/version-0.1.2-green.svg)](http://pypi.deepair.io)

## Introduction
Welcome to **Flai**, pronounced as 'Fly!' :smiley:


Flai is toolkit for developing and comparing reinforcement learning algorithms built by [deepair](https://www.deepair.io). It is inspired by OpenAI Gym and has been modified for deepair's needs. Flai comes with pre packaged games that are designed and maintained by deepair. Get in touch with us, if you want to write your games. Currently this package is designed for deepair's internal use. Our long term goal is to open source this package, along with its games to AI research community.

## Installation
To install the entire library, use `pip install deepair-flai`.

This does not include dependencies for all families of environments (there's a massive number, and some can be problematic to install on certain systems). You can install these dependencies for one family like `pip install flai[seatsmart]` or use `pip install flai[ubundle]` to install all dependencies.

We support Python 3.8 and above on Linux and macOS. We will accept PRs related to Windows, but do not officially support it.

## Getting started
TODO

## Documentation

### Local Server
Launching documentation server locally requires `npm`. It is built on `docsify` and recommended to install globally using the following command:

```
npm i docsify-cli -g
```

Now to run the server, you can run the following command:

```
docsify init ./docs
```
