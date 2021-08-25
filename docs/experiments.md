# Flai
**[Home]** | **[Experiments]** |  **[Tutorial]** |

## Experiments

### Best Practices

For runnning experiments in reproducible and organizable fassion, the following resources are recommended but not required.

#### Resources

1. **Sacred** : [Sacred](https://github.com/IDSIA/sacred) is a tool to help you configure, organize, log and reproduce experiments. It is designed to do all the tedious overhead work that you need to do around your actual experiment in order to:

    - keep track of all the parameters of your experiment
    - easily run your experiment for different settings
    - save configurations for individual runs in a database
    - reproduce your results

    > **Note** : Watch this video [[here](https://www.youtube.com/watch?v=qqg7RO0o1OE)] to prepare yourself about sacred. Sacred also have online documentation [[here](https://sacred.readthedocs.io/en/stable/)] for additional references. I would recomment please go over the video in your spare time and try using it for a small experiment.

    **Why sacred?** because it provides ConfigScopes, Config Injection, Command-line interface, Observers, Automatic seeding and Dashboard out of the box. 

    **Installation** : Sacred is a stand alone python package and can be installed via `pip` command. It is not shipped with FLAI. 

2. **Mongo DB** : We will be using Mongo DB [[here](https://www.mongodb.com/)] for observing experiment runs via "sacred". 

3. **Bitbucket** : To version control the progress, we will be using "Git". For this specific use case, we will use bitbucket. 

4. **Omniboard** : We will be using Omniboard UI [here] as a dashboard to visualize runs recorded in MongoDB via sacred. 

#### Design and Workflow

To Do

#### Security and Authentications

> **NOTE** : This section will be removed when we move authentication protocol centeralized or when we relax user access restrictions in this repository.

For now, we will be using following username and passwords.

- **Mongo DB**:
  - DATABASE : `sacred`
  - USERNAME : `naman`
  - PASSWORD : `naman_deepair`
  - URI : `mongodb+srv://<username>:<password>@deepaircluster-j3jek.mongodb.net/<dbname>?retryWrites=true&w=majority`

- **Omniboard**:
  - URL : `http://ec2-3-14-133-122.us-east-2.compute.amazonaws.com:9000`
  - USERNAME : `deepair`
  - PASSWORD : `Riapeed@2020`

[Home]: ./index.md
[Experiments]: ./experiments.md
[Tutorial]: ./tutorial.md